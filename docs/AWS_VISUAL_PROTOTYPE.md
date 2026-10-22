# Remote visual prototype — execution readiness

October 21, 2026 (America/Los_Angeles)

AWS Console authentication and an STS identity check succeeded. AWS CLI 2.38.4 was installed in the development workspace after verification of its official GPG signature. The temporary profile is `cricket-visual`; authentication can expire and must not be embedded in the project or a machine image.

**No paid resources or asset purchases have been created by this work.** There is no remote Unreal workstation, completed Unreal scene or rendered cricket video yet.

## What is now prepared

- [Unreal starter project](../rendering/unreal/BoundaryVisual.uproject), targeting 5.7 with editor scripting, Sequencer scripting and Movie Render Queue enabled. This is configuration only; the editor has not executed it.
- [Asset manifest template](../rendering/unreal/asset-manifest.example.json), recording the meshes, clips, sockets, release/contact timing and license evidence needed to build the delivery.
- [Read-only AWS checker](../deploy/aws_visual_preflight.py), which checks identity, G/VT vCPU quota, existing GPU usage, regional instance offerings and current public Linux/GP3/IPv4 prices. It contains no provisioning operation.
- The [30-second shot plan](visual-shot-plan.json) and [concept storyboard](concepts/first-delivery-storyboard.png). The storyboard remains generated artwork, not engine footage.

The checker considers `g4dn.2xlarge`, `g5.2xlarge` and `g6.2xlarge` in `us-east-2` by default; `--region us-east-1` is also supported. A candidate must have at least 32 GiB RAM, sufficient unused vCPU quota, a regional offering and a verified estimate within the cloud allowance. An offering is not evidence of immediate capacity, and a passing report is not an engine or asset validation. Pricing requests use the supported `us-east-1` Price List API endpoint with the target region supplied as a product filter.

Run from the repository root with AWS CLI v2 and a valid profile:

```sh
python deploy/aws_visual_preflight.py --expected-account YOUR_12_DIGIT_ACCOUNT_ID
```

In the current development workspace, add `--aws /workspace/cloud-tools/aws/aws` to use the installed wrapper. It stores credentials in a private temporary directory outside the repository. The JSON report is written to the ignored `build/cloud/aws-visual-preflight.json`; a blocked check exits with status 2. An account mismatch stops subsequent account queries. Missing or ambiguous prices never count as zero cost.

## Account and network status

Sign-in and STS work in `us-east-1`. The first network additions became usable during the checks. AWS then reported two account restrictions: the `us-east-1` on-demand G/VT GPU quota is **0 vCPUs**, and an organization service control policy explicitly denies EC2 description operations there. No attempt was made to change that policy or provision around it.

The user's Console was in `us-east-2` (Ohio). After the network additions took effect, **Ohio EC2 queries succeeded**. All three candidate types are offered there, each with 8 vCPUs and 32 GiB RAM. Their GPUs are respectively NVIDIA T4, A10G and L4. Existing pending/running/stopping GPU instance usage was zero, and the Ohio on-demand G/VT quota was **0 vCPUs**.

There was no existing GPU quota request. A request to raise Ohio's quota to **8 vCPUs** was submitted and returned **PENDING**. The request itself creates no billable resource. Approval time is unknown; check Service Quotas before considering a launch. `build/cloud/aws-visual-preflight-us-east-2.json` contains the local readiness evidence. The saved network draft includes:

```text
ec2.us-east-1.amazonaws.com
servicequotas.us-east-1.amazonaws.com
api.pricing.us-east-1.amazonaws.com
ssm.us-east-1.amazonaws.com
cloudformation.us-east-1.amazonaws.com
ec2.us-east-2.amazonaws.com
servicequotas.us-east-2.amazonaws.com
ssm.us-east-2.amazonaws.com
cloudformation.us-east-2.amazonaws.com
sts.us-east-2.amazonaws.com
```

Calls now reach both regions in this session. Review, save and publish the environment draft to retain the configuration; restoration in a new task has not been tested. SSM and CloudFormation are included for the subsequent managed worker setup; no worker stack or remote commands have been submitted. Additional download/storage endpoints may need configuration once an actual engine/asset source is selected. Do not remove organization controls automatically. Successful EC2 description operations do not establish launch permission or available capacity.

## Engine and motion prerequisites

The user does not yet have an Epic Games account or cricket assets. Create an account from [Unreal's download page](https://www.unrealengine.com/en-US/download). The [Linux binary download](https://www.unrealengine.com/linux) currently requires Epic authentication. No account credentials or engine license acceptance should be committed to this repository.

Epic's [current Linux requirements](https://dev.epicgames.com/documentation/en-us/unreal-engine/linux-development-requirements-for-unreal-engine) recommend Ubuntu 22.04 and 32 GB RAM, and list NVIDIA 570+ for Vulkan. The provisional first choice is `g6.2xlarge` in Ohio with Amazon's `Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04) 20261016`, image `ami-0c824a69d98d87ee5`. EC2 returned its owner as `898082745236`, Linux/UNIX platform, available status and no Marketplace product codes. Its root snapshot is 75 GiB GP3; the plan budgets a 200 GiB encrypted root volume. Revalidate the image at launch. The actual installed driver, Vulkan support and Unreal execution have not been tested on it; no engine is included in this project.

These are researched candidates, **not a shopping cart**. Prices below came from the public Fab listing metadata on October 21; they exclude tax and must be checked at checkout. Personal and Professional are separate license tiers; eligibility and the applicable terms need review before selection.

| Listing | Personal / Professional USD | What the listing establishes | Missing evidence |
| --- | --- | --- | --- |
| [Cricket Animations — voxel vision](https://www.fab.com/listings/f102b4cb-f89d-4f0f-9879-c4f70af3c073) | $59.99 / $119.99 | Named batting idle/shot and running clips; Unreal and Unity formats; explicitly excludes models | No bowling action listed; rig/engine compatibility and motion quality untested |
| [Cricket Batsman — Trishika J](https://www.fab.com/listings/45bca92b-000b-41a3-94a6-1b878c880b2e) | $59.99 / $69.99 | Textured character in Blender/FBX formats | Usable rig, deformation and compatible animation are not established by the description |
| [Cricket Bowler — Trishika J](https://www.fab.com/listings/980baf84-836f-49c3-959d-dabdae62c55e) | $49.99 / $59.99 | Textured character in Blender/FBX formats | The name describes the character, not a verified bowling-motion clip |
| [World Cricket Champions — Shah Rukh](https://www.fab.com/listings/62c36571-049b-4c1a-82d3-059fe6b00a32) | $7.99 / $15.99 | FBX collection described as rigged/animated, with external model attribution | Exact clips, source rights, neutral kit adaptation and usable delivery motion need inspection |

The animation pack's [public showcase](https://youtu.be/yjC1x7r7fYI) is a review input; its motion has not yet been independently inspected in the target rig. A batsman model, bowler model and batting pack do not establish the complete sequence. Select or author a legal bowling action and verify contact/footwork before spending on environment decoration or continuous GPU time.

## Cost controls for the first worker

The total prototype allowance remains **US$300**: assets/motion $180, temporary compute/storage $80, reserve $40. The user requested continued work and notification whenever paid resources are created. Announce the exact resource and verified expected charge before starting billing; a planning estimate is not a purchase or an AWS billing cap.

The checker defaults to eight GPU hours, a 200 GiB GP3 disk retained for seven days, one public IPv4 address during runtime and a $10 tax/data-transfer contingency. It conservatively divides monthly disk prices by 672 hours for planning. It does not assume free-tier coverage, Spot discounts or credits. A contingency is not a quote for unverified transfer or tax charges. Marketplace software fees, snapshots, extra IOPS and continuous streaming are excluded and must not be added silently.

The AWS Price List API returned the following **Ohio Linux on-demand prices** on October 21. GP3 storage is $0.08/GiB-month and public IPv4 is $0.005/hour. The GPU quota increase is still pending. None of these quotes establishes immediate GPU capacity or launch permission.

| Candidate | Compute per hour | Eight-hour plan including storage, IPv4 and $10 contingency |
| --- | --- | --- |
| `g4dn.2xlarge` | $0.7520 | $20.06 |
| `g5.2xlarge` | $1.2120 | $23.74 |
| `g6.2xlarge` | $0.9776 | $21.87 |

The estimate includes the full seven-day disk-retention assumption. These are current public rates, not spend already incurred or a hard budget guarantee. Driver, quota and capacity checks still determine the final selection.

Before launch, resolve an official compatible image, verify quota and prices, stage the engine/assets, and implement/test a timed stop and cleanup procedure. GPU compute stops being billed when stopped; retained disks still cost money. Cleanup requires backing up the project/footage and deleting unnecessary volumes and other billable resources. Budget alerts alone do not stop spending. No launch command or automatic billing guard is implemented in this starter.

| Prototype expenditure initiated by this work | Amount |
| --- | --- |
| Asset purchases | $0 |
| New AWS resources | None |

This ledger is not a statement about existing account-wide AWS charges.

## Validation and next execution step

All **22 focused checker tests passed**. They cover blocked networking, wrong-account refusal, exhausted/zero quota, missing/ambiguous/non-USD prices, existing GPU consumption, retained-disk cost, regional pricing routing and the cloud allowance. Unreal JSON/INI files passed syntax checks only; the editor is not available. No graphics, rendering-speed or gameplay-quality claim follows from these checks.

While AWS reviews the quota request, establish Epic access and resolve the missing bowling/character inputs. Then rerun the checker, revalidate the candidate image, implement the timed stop/cleanup controls, announce the charge, and create a worker only when it has useful work to run. Build and review the actual first delivery before returning to database deployment or a larger arena.
