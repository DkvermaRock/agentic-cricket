# Boundary Unreal starter

This is an **unexecuted starter project**, not a completed scene or rendered footage. No licensed characters, motion, environment assets or video are included. There is no installed Unreal editor in the current workspace.

The selected route remains Unreal for a recorded 30-second first-delivery prototype. Target Unreal 5.7 initially; confirm pack compatibility before installing a different version. The engine project enables Python editor scripting, Sequencer scripting and Movie Render Queue. Renderer settings request Lumen, virtual shadow maps, TSR and Vulkan SM6 on Linux. These settings alone do not establish visual quality or a frame-rate result.

## Open after installing Unreal

Obtain the editor through your own Epic account at <https://www.unrealengine.com/linux> for Linux, or the Epic Games Launcher for Windows. The current AWS plan is a temporary Linux GPU workstation to avoid a Windows licensing premium; machine pricing and quota still need verification.

Open `BoundaryVisual.uproject` in the editor. A project with no authored level is expected at this stage. Do not substitute generated concept artwork for rendered footage.

Copy `asset-manifest.example.json` to `asset-manifest.local.json` when actual assets arrive. Import purchased source assets under `/Game/ThirdParty/` and record their Unreal object paths, animation release/contact times, attachment sockets and license evidence. That folder and the local manifest are ignored by Git. Rig compatibility and motion quality must be checked in the editor before filling the review flags.

## Build the first sequence

Use [the shot plan](../../docs/visual-shot-plan.json) as the timing source: 60 fps, 1,800 frames, release at 630, planned contact at 669 and one score update at 882. The replay occupies frames 1,050–1,650 and repeats source frames 630–780 at quarter speed. Match the source clips to those events; adjust the plan if the real action needs different timing rather than stretching an incorrect bowling action.

The level, animation retargeting, ball attachment/detachment, bat contact, fielding and Sequencer camera cuts are still to be authored. Render Queue should export a numbered 1920×1080 PNG sequence at 60 fps with sufficient warm-up. Encode the reviewed frames only after checking gaps, camera cuts and contact. Label the eventual viewing page `Visual prototype · recorded animation`. Frame-time and streaming performance require separate measurements later.

See [AWS readiness and costs](../../docs/AWS_VISUAL_PROTOTYPE.md) for the current blockers and asset research.
