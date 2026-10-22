"""Read-only AWS checks for the visual prototype. This program cannot launch resources."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import subprocess


READ_OPERATIONS = {
    ("sts", "get-caller-identity"),
    ("ec2", "describe-instance-types"),
    ("ec2", "describe-instance-type-offerings"),
    ("ec2", "describe-instances"),
    ("service-quotas", "get-service-quota"),
    ("pricing", "get-products"),
}
CANDIDATES = ("g4dn.2xlarge", "g5.2xlarge", "g6.2xlarge")
GPU_QUOTA = "L-DB2E81BA"


class CheckFailed(Exception):
    pass


class AWS:
    def __init__(self, executable: str, profile: str, region: str):
        self.executable, self.profile, self.region = executable, profile, region

    def call(self, service: str, operation: str, *args: str) -> dict:
        if (service, operation) not in READ_OPERATIONS:
            raise CheckFailed(f"Operation is not in the read-only allowlist: {service} {operation}")
        api_region = "us-east-1" if service == "pricing" else self.region
        command = [self.executable, service, operation, *args, "--profile", self.profile,
                   "--region", api_region, "--output", "json", "--no-cli-pager",
                   "--cli-connect-timeout", "10", "--cli-read-timeout", "20"]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60,
                                    env={**os.environ, "AWS_MAX_ATTEMPTS": "1"})
        except (OSError, subprocess.TimeoutExpired) as error:
            raise CheckFailed(f"{service} {operation}: {type(error).__name__}") from error
        if result.returncode:
            # No --debug, credential exports or arbitrary command execution.
            raise CheckFailed(f"{service} {operation}: {result.stderr.strip()[:500]}")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise CheckFailed(f"{service} {operation}: response was not JSON") from error


def positive(value: object, label: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise CheckFailed(f"{label} is not a valid number") from error
    if not number.is_finite() or number <= 0:
        raise CheckFailed(f"{label} must be finite and positive")
    return number


def price_rate(response: dict, unit: str) -> Decimal:
    """Require one unambiguous positive public USD rate; missing prices never mean free."""
    rates = set()
    for raw in response.get("PriceList", []):
        product = json.loads(raw) if isinstance(raw, str) else raw
        for term in product.get("terms", {}).get("OnDemand", {}).values():
            for dimension in term.get("priceDimensions", {}).values():
                if dimension.get("unit") == unit and dimension.get("beginRange") == "0":
                    rates.add(positive(dimension.get("pricePerUnit", {}).get("USD"), "USD rate"))
    if len(rates) != 1:
        raise CheckFailed(f"Expected one {unit} USD price, found {len(rates)} distinct rates")
    return rates.pop()


def price(aws: AWS, service_code: str, unit: str, **filters: str) -> Decimal:
    values = [{"Type": "TERM_MATCH", "Field": name, "Value": value}
              for name, value in filters.items()]
    return price_rate(aws.call("pricing", "get-products", "--service-code", service_code,
                               "--filters", json.dumps(values)), unit)


def cost_estimate(compute: Decimal, storage: Decimal, ipv4: Decimal, *, hours: Decimal,
                  disk_gib: Decimal, retention_hours: Decimal, reserve: Decimal) -> dict:
    # Storage continues to cost money while an instance is stopped. Use 28 days/month
    # as a conservative planning divisor, not as a claim about AWS billing proration.
    values = [compute, storage, ipv4, hours, disk_gib, retention_hours, reserve]
    for value in values:
        positive(value, "Cost input")
    if retention_hours < hours:
        raise CheckFailed("Disk retention must cover the entire runtime")
    parts = {"compute": compute * hours, "gp3_storage": storage * disk_gib * retention_hours / 672,
             "public_ipv4": ipv4 * hours, "tax_transfer_contingency": reserve}
    return {**{key: str(value.quantize(Decimal("0.01"), rounding="ROUND_UP"))
               for key, value in parts.items()},
            "total": str(sum(parts.values()).quantize(Decimal("0.01"), rounding="ROUND_UP"))}


def inspect(aws: AWS, expected_account: str, hours: Decimal, disk_gib: Decimal,
            retention_hours: Decimal, reserve: Decimal, cloud_budget: Decimal) -> dict:
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "region": aws.region,
              "status": "blocked", "resources_created": False, "blockers": [], "candidates": [],
              "assumptions": {"gpu_hours": str(hours), "disk_gib": str(disk_gib),
                              "disk_retention_hours": str(retention_hours),
                              "cloud_allowance_usd": str(cloud_budget)},
              "limitations": ["Offering availability does not establish immediate GPU capacity.",
                              "This is a planning estimate, not a hard billing cap or a launch command.",
                              "Unreal download, asset rights and motion compatibility need separate checks.",
                              "No paid marketplace AMI, extra IOPS, snapshots or continuous streaming included."]}
    try:
        identity = aws.call("sts", "get-caller-identity")
        if identity.get("Account") != expected_account:
            raise CheckFailed("Authenticated AWS account does not match --expected-account")
        report["account"] = identity["Account"]
    except CheckFailed as error:
        report["blockers"].append(str(error))
        return report

    def check(label, function):
        try:
            return function()
        except (CheckFailed, KeyError, ValueError, TypeError) as error:
            report["blockers"].append(f"{label}: {error}")
            return None

    quota = check("GPU quota", lambda: aws.call("service-quotas", "get-service-quota",
                  "--service-code", "ec2", "--quota-code", GPU_QUOTA)["Quota"]["Value"])
    specs = check("GPU specifications", lambda: aws.call("ec2", "describe-instance-types",
                  "--instance-types", *CANDIDATES)["InstanceTypes"])
    offerings = check("Regional offerings", lambda: aws.call("ec2", "describe-instance-type-offerings",
                      "--location-type", "region", "--filters",
                      "Name=instance-type,Values=" + ",".join(CANDIDATES))["InstanceTypeOfferings"])
    instances = check("Current GPU usage", lambda: aws.call("ec2", "describe-instances", "--filters",
                      "Name=instance-state-name,Values=pending,running,stopping",
                      "Name=instance-type,Values=g*,vt*")["Reservations"])
    used = None
    if instances is not None:
        types = [instance["InstanceType"] for reservation in instances
                 for instance in reservation["Instances"]]
        if not types:
            used = 0
        else:
            used_specs = check("Existing GPU vCPUs", lambda: aws.call("ec2", "describe-instance-types",
                               "--instance-types", *sorted(set(types)))["InstanceTypes"])
            if used_specs is not None:
                counts = {item["InstanceType"]: item["VCpuInfo"]["DefaultVCpus"] for item in used_specs}
                used = sum(counts[item] for item in types)
    report["gpu_vcpu_quota"] = quota
    report["used_gpu_vcpus"] = used
    storage = check("gp3 price", lambda: price(aws, "AmazonEC2", "GB-Mo", regionCode=aws.region,
                    productFamily="Storage", volumeApiName="gp3"))
    usage_prefix = {"us-east-1": "USE1", "us-east-2": "USE2"}[aws.region]
    ipv4 = check("IPv4 price", lambda: price(aws, "AmazonVPC", "Hrs", regionCode=aws.region,
                 usagetype=usage_prefix + "-PublicIPv4:InUseAddress"))
    report["shared_rates_usd"] = {"gp3_per_gib_month": str(storage) if storage is not None else None,
                                  "public_ipv4_per_hour": str(ipv4) if ipv4 is not None else None}
    offered = {item["InstanceType"] for item in offerings or []}
    specs_by_type = {spec["InstanceType"]: spec for spec in specs or []}
    for kind in CANDIDATES:
        spec = specs_by_type.get(kind)
        compute = check(kind + " Linux price", lambda kind=kind: price(
            aws, "AmazonEC2", "Hrs", regionCode=aws.region, instanceType=kind,
            operatingSystem="Linux", tenancy="Shared", preInstalledSw="NA",
            capacitystatus="Used", operation="RunInstances"))
        candidate = {"type": kind, "vcpus": spec["VCpuInfo"]["DefaultVCpus"] if spec else None,
                     "memory_gib": spec["MemoryInfo"]["SizeInMiB"] / 1024 if spec else None,
                     "gpus": spec.get("GpuInfo", {}).get("Gpus", []) if spec else None,
                     "offered_in_region": kind in offered if offerings is not None else None,
                     "quota_sufficient": quota - used >= spec["VCpuInfo"]["DefaultVCpus"]
                     if quota is not None and used is not None and spec is not None else None,
                     "linux_hourly_usd": str(compute) if compute is not None else None}
        if all(value is not None for value in [compute, storage, ipv4]):
            estimate = cost_estimate(compute, storage, ipv4, hours=hours, disk_gib=disk_gib,
                                     retention_hours=retention_hours, reserve=reserve)
            candidate["estimate_usd"] = estimate
            candidate["within_cloud_allowance"] = Decimal(estimate["total"]) <= cloud_budget
        candidate["cloud_checks_passed"] = all([
            candidate["offered_in_region"] is True, candidate["quota_sufficient"] is True,
            candidate.get("within_cloud_allowance") is True, (candidate["memory_gib"] or 0) >= 32,
        ])
        report["candidates"].append(candidate)
    if any(item["cloud_checks_passed"] for item in report["candidates"]):
        report["status"] = "cloud_candidate_found"
    else:
        report["blockers"].append("No candidate passed pricing, region, memory and quota checks.")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aws", default="aws", help="AWS CLI v2 executable or configured wrapper")
    parser.add_argument("--profile", default="cricket-visual")
    parser.add_argument("--region", choices=["us-east-1", "us-east-2"], default="us-east-2")
    parser.add_argument("--expected-account", required=True)
    parser.add_argument("--gpu-hours", default="8")
    parser.add_argument("--disk-gib", default="200")
    parser.add_argument("--retention-hours", default="168")
    parser.add_argument("--contingency-usd", default="10")
    parser.add_argument("--cloud-budget-usd", default="80")
    parser.add_argument("--output", type=Path, default=Path("build/cloud/aws-visual-preflight.json"))
    args = parser.parse_args()
    try:
        values = [positive(getattr(args, key), key) for key in
                  ["gpu_hours", "disk_gib", "retention_hours", "contingency_usd", "cloud_budget_usd"]]
        if values[2] < values[0]:
            raise CheckFailed("Disk retention must cover the entire runtime")
        if values[4] > 80:
            raise CheckFailed("The prototype's current cloud allowance is US$80")
        if len(args.expected_account) != 12 or not args.expected_account.isascii() or not args.expected_account.isdigit():
            raise CheckFailed("Expected account must be a 12-digit AWS account ID")
    except CheckFailed as error:
        parser.error(str(error))
    report = inspect(AWS(args.aws, args.profile, args.region), args.expected_account, *values)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "cloud_candidate_found" else 2


if __name__ == "__main__":
    raise SystemExit(main())
