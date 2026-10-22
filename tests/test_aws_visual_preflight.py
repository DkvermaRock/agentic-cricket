import json
from decimal import Decimal
from unittest.mock import patch
from types import SimpleNamespace

import pytest

from deploy.aws_visual_preflight import AWS, CANDIDATES, CheckFailed, cost_estimate, inspect, positive, price_rate


def price_response(rate="1.25", unit="Hrs", currency="USD"):
    return {"PriceList": [json.dumps({"terms": {"OnDemand": {"offer": {"priceDimensions": {
        "rate": {"unit": unit, "beginRange": "0", "pricePerUnit": {currency: rate}}
    }}}}})]}


def test_write_operations_cannot_reach_aws():
    with patch("subprocess.run") as run:
        with pytest.raises(CheckFailed, match="read-only"):
            AWS("aws", "test", "us-east-1").call("ec2", "run-instances", "--image-id", "ami-example")
        run.assert_not_called()


def test_ohio_prices_use_supported_pricing_endpoint():
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0, stdout="{}")) as run:
        AWS("aws", "test", "us-east-2").call("pricing", "get-products")
        command = run.call_args.args[0]
        assert command[command.index("--region") + 1] == "us-east-1"


@pytest.mark.parametrize("value", ["0", "-1", "NaN", "Infinity", "garbage", True])
def test_invalid_cost_inputs_fail_closed(value):
    with pytest.raises(CheckFailed):
        positive(value, "cost")


@pytest.mark.parametrize("response", [
    {}, price_response("0"), price_response("1.25", currency="EUR"),
    {"PriceList": price_response("1.25")["PriceList"] + price_response("2.00")["PriceList"]},
])
def test_missing_free_or_ambiguous_prices_are_not_a_safe_estimate(response):
    with pytest.raises(CheckFailed):
        price_rate(response, "Hrs")


def test_identical_public_rates_are_deduplicated():
    response = price_response()
    response["PriceList"] *= 2
    assert price_rate(response, "Hrs") == Decimal("1.25")


def test_stopped_disk_cost_and_contingency_are_included():
    # Fixture rates are test data, not a quote for a current AWS product.
    estimate = cost_estimate(Decimal("1.25"), Decimal("0.08"), Decimal("0.005"),
                             hours=Decimal("8"), disk_gib=Decimal("200"),
                             retention_hours=Decimal("168"), reserve=Decimal("10"))
    assert estimate == {"compute": "10.00", "gp3_storage": "4.00", "public_ipv4": "0.04",
                        "tax_transfer_contingency": "10.00", "total": "24.04"}


class FakeAWS:
    region = "us-east-1"

    def __init__(self, *, account="111111111111", quota=8, usage=0, failed_service=None):
        self.account, self.quota, self.usage, self.failed_service = account, quota, usage, failed_service
        self.calls = []

    def call(self, service, operation, *args):
        self.calls.append((service, operation))
        if service == self.failed_service:
            raise CheckFailed("Network unavailable")
        if service == "sts":
            return {"Account": self.account}
        if service == "service-quotas":
            return {"Quota": {"Value": self.quota}}
        if operation == "describe-instance-types":
            return {"InstanceTypes": [{"InstanceType": name, "VCpuInfo": {"DefaultVCpus": 8},
                                       "MemoryInfo": {"SizeInMiB": 32768}} for name in CANDIDATES]}
        if operation == "describe-instance-type-offerings":
            return {"InstanceTypeOfferings": [{"InstanceType": name} for name in CANDIDATES]}
        if operation == "describe-instances":
            return {"Reservations": [{"Instances": [{"InstanceType": "g5.2xlarge"}]
                                      * self.usage}] if self.usage else []}
        if service == "pricing":
            filters = json.loads(args[args.index("--filters") + 1])
            if any(item["Field"] == "volumeApiName" for item in filters):
                return price_response("0.08", "GB-Mo")
            if "AmazonVPC" in args:
                return price_response("0.005")
            return price_response()
        raise AssertionError((service, operation))


def report(aws, budget="80"):
    return inspect(aws, "111111111111", Decimal("8"), Decimal("200"), Decimal("168"),
                   Decimal("10"), Decimal(budget))


def test_wrong_account_stops_before_other_calls():
    aws = FakeAWS(account="222222222222")
    result = report(aws)
    assert result["status"] == "blocked"
    assert aws.calls == [("sts", "get-caller-identity")]


@pytest.mark.parametrize("aws", [FakeAWS(quota=0), FakeAWS(quota=8, usage=1),
                                 FakeAWS(failed_service="pricing"), FakeAWS(failed_service="ec2")])
def test_no_candidate_is_ready_with_insufficient_quota_usage_or_unknown_prices(aws):
    result = report(aws)
    assert result["status"] == "blocked"
    assert not any(item["cloud_checks_passed"] for item in result["candidates"])


def test_sufficient_quota_and_estimate_only_mark_cloud_checks_complete():
    result = report(FakeAWS())
    assert result["status"] == "cloud_candidate_found"
    assert result["resources_created"] is False
    assert result["limitations"]


def test_public_prices_do_not_override_denied_ec2_checks():
    result = report(FakeAWS(failed_service="ec2"))
    assert all(item["linux_hourly_usd"] is not None for item in result["candidates"])
    assert all(item["memory_gib"] is None for item in result["candidates"])
    assert result["status"] == "blocked"


def test_over_budget_candidate_is_blocked():
    result = report(FakeAWS(), budget="20")
    assert result["status"] == "blocked"
    assert all(not item["within_cloud_allowance"] for item in result["candidates"])
