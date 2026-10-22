# Milestone 1 — the first delivery

October 21, 2026 · Preproduction; no engine footage produced

[View the concept storyboard](concepts/first-delivery-storyboard.png). It is generated planning artwork, not an engine capture, animation sample or acquired asset pack. Shot anatomy and continuity still require cricket review; the contact frames should not be treated as motion reference.

## Shot to build

A right-handed batter plays a controlled cover drive for four against a right-arm medium-pace bowler. Original teal/navy and sand/navy uniforms, late-afternoon lighting, one readable stadium viewpoint and natural cricket audio. Establish a believable cricket action before adding detailed crowds or elaborate VFX.

The sequence is 30 seconds, including a slow-motion replay. The authored outcome illustrates the visual target and is not an agent evaluation. Label the viewing page **Visual prototype · recorded animation** when actual footage exists.

| Time | Camera / action | What must read clearly |
| --- | --- | --- |
| 0–4 s | Wide establishing view | Real pitch proportions, actor positions, original stadium identity |
| 4–10.5 s | Stable end-on view behind the bowler | Grounded run-up, gather and front-foot plant |
| 10.5–11.15 s | Continue end-on through release and bounce | Legal bowling action, visible ball path, batter tracking the delivery |
| 11.15–14.7 s | Cut on contact into cover-side ball follow | Front-foot drive, bat/ball contact, follow-through and credible field response |
| 14.7–17.5 s | Boundary and result | Ball reaches the rope on the ground; score changes once to 4/0 after 0.1 overs |
| 17.5–27.5 s | Labeled quarter-speed replay | Repeat 10.5–13 s from a side-on camera; show actual contact without rescoring |
| 27.5–30 s | Settle and end frame | Clean stopping point and replay affordance in the eventual player |

At 60 export frames per second the sequence contains 1,800 frames. This is an output specification, not a measured rendering rate. The frame-accurate cut list is [visual-shot-plan.json](visual-shot-plan.json).

## Asset requirements

| Asset | Minimum usable input | Current status |
| --- | --- | --- |
| Cricketer | Skinned character with suitable skeleton, kit, pads, gloves and helmet; permitted use in output and target engine | Not selected |
| Bowling motion | Run-up, gather, delivery stride, release and follow-through; legal cricket arm action | Missing |
| Batting motion | Guard, front-foot preparation, drive and recovery; editable contact frame | Missing |
| Fielding motion | Ready stance, short chase and pickup/stop attempt | Missing |
| Props | Correct bat, ball, stumps and bails at consistent real-world scale | Existing procedural props are references; final assets need review |
| Environment | Pitch, grass, boundary and limited stadium background with usable material rights | Existing procedural scene is a layout reference |
| Audio | Licensed/original bat impact and restrained crowd/stadium ambience | Not selected |

Prefer a shared skeleton or a documented retargeting path. Verify foot plant, hand placement, bat grip, contact alignment and helmet/pad clipping on the actual motions. Keep source/license receipts with selected assets. Do not purchase a pack based only on a still image or assume a generic sports motion is a cricket delivery.

## Runtime and sourcing check

The current workspace has Blender and ffmpeg. It has no Unreal editor executable, NVIDIA/DRI rendering device, cricket asset files or authenticated AWS profile. It cannot presently execute the recommended Unreal scene or certify GPU performance.

Official reference destinations are [Unreal Linux requirements](https://dev.epicgames.com/documentation/en-us/unreal-engine/linux-development-requirements-for-unreal-engine), [Unreal downloads](https://www.unrealengine.com/en-US/download) and the [Fab cricket catalog search](https://www.fab.com/search?q=cricket). Initial documentation/catalog requests were blocked by the environment proxy with HTTP 403. Required domains have been added to the saved environment draft; that save does not prove runtime access. No specific purchasable pack, current price or license has been verified.

The next execution prerequisite is either an accessible Unreal-capable GPU machine with appropriate licensing/assets, or an explicitly chosen alternative rendering route. The user selected **up to US$300 total** for planning the first prototype. This is a ceiling, not a production estimate or a guarantee that suitable cricket animation can be obtained within it. The budget question explicitly did not authorize purchases.

## Budget and procurement gate

| Category | Proposed ceiling | Evidence required before spending |
| --- | --- | --- |
| Character, props and cricket motion | US$180 | Exact products, actual prices/taxes, rights to use them in the intended output, previewed bowling/batting motion and compatible rig/import path |
| Temporary GPU runtime and storage | US$80 | Authenticated target account, exact machine/region, OS/engine availability, current all-in rates, maximum run duration and stop/cleanup procedure |
| Reserve | US$40 | An identified shortfall; not an automatic spending allocation |
| Total | **US$300** | Track actual purchases and cloud cost against the cap |

The caps can be rebalanced within the total only after actual options are known. Do not provision a continuously running streaming service for this recorded prototype. A short rendering session can be stopped after exporting the review footage, and the video can be distributed separately.

The next decision packet must identify one specific asset/motion set and one accessible rendering machine, including license terms, full cost and remaining allowance. No exact pack or provider price is currently verified, so there is no purchase proposal ready to approve yet. A production cricket title or guaranteed broadcast realism is outside this US$300 feasibility budget.

## Review and completion

If a generated concept storyboard is supplied, it is art direction only. It must be visibly labeled **Concept storyboard — not engine footage** and must not be used to claim that assets, motion, rendering or a game already work.

Actual milestone acceptance requires a rendered video or executable browser scene, a working viewing link, and review of the delivery action. Check foot sliding, front-foot position, hand-to-ball release, bat contact, ball trajectory, camera cuts, correct score timing and replay labeling. Fix those before investing in denser crowds, more stadiums or a wider game scope.

Record output resolution, engine version, hardware, asset versions and any rendering/encoding failures with the real artifact. Real-time 1080p60 remains a later measured gate. No prerecorded video, generated still or timer setting establishes that performance.
