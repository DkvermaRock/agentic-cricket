# Agentic Cricket — revised delivery plan

October 21, 2026 · Direction accepted; milestone 1 preparation started

The user accepted the reset after the deployment and prototype work did not produce the desired experience. Start milestone 1 preparation and keep deployment troubleshooting paused. Preserve the repository and existing cloud projects. This plan changes the order of delivery; the [product requirements](REQUIREMENTS.md) remain the record of the long-term vision.

## Outcome we need to deliver

A user opens one website link, sees convincing cricket, understands which player decisions came from an agent, and can later create and develop a player within a limited budget.

The original vision remains: persistent players with unique names, skill constraints, learning and progression; club ownership and transfers; autonomous team-building agents; and a broadcast-style Agent Arena. The next prototype should prove the hardest parts before assembling that complete product.

## What the current work actually establishes

- The Python POC demonstrates finite creation budgets, normalized name uniqueness, saved matches and a per-player contextual-bandit learner in a synthetic batting model.
- The Babylon.js viewer demonstrates moving procedural characters, cameras and replay controls. Its current art does not meet the desired realism.
- The Docker build succeeded on Render. The supplied failure log showed missing `DATABASE_URL`; subsequent public operation has not been verified. That failure does not establish a problem with the rendering engine or learning model.
- The fresh Supabase project was verified healthy in the previous setup work. Creating more databases is not a remedy for visual quality or an incomplete game loop.
- Real GPU performance, production animation, LLM-assisted tactics, full team matches and a live video broadcast have not been demonstrated.

Keep reusable simulation tests and the event/replay design. Evaluate the current scene as prototype code rather than production artwork. No wholesale rewrite or new cloud subscription is justified solely by the deployment failure.

## First decision: what must the next demo prove?

Proceed with **visual quality first**, following acceptance of the recommended sequence. The first shot brief is in [VISUAL_PROTOTYPE.md](VISUAL_PROTOTYPE.md). The user selected a **US$300 total planning ceiling** for assets and temporary GPU access. Preparing the prototype does not establish a completed engine migration or authorize asset purchases.

If learning is the priority, start with milestone 2 and a simple score/replay interface, then proceed to milestone 1. Do not present a polished management screen as proof of realistic cricket animation.

## Milestone 1 — a small visual prototype worth watching

**User-facing deliverable:** one browser link containing a clearly labeled, 20–40-second cricket animation prototype, with reliable play and replay controls. It should require no database configuration, account creation or terminal commands from the viewer.

Limit the scene to one pitch, one stadium viewpoint, one bowler, one batter and the supporting actors needed for a believable delivery. Produce a complete run-up, release, bounce, shot, ball follow and result. A second outcome is useful only after the first looks convincing.

The production inputs are explicit: a rigged cricket character, compatible cricket-specific motion, bat/ball contact alignment, foot placement, lighting, materials, camera timing and original or licensed audio. Confirm asset rights and the animation pipeline before committing to a schedule. Generic motion and more visual effects will not solve incorrect cricket movement.

### Rendering recommendation

For the stated broadcast-realism ambition, **Unreal Engine is the leading candidate for the visual prototype**. Start with a short rendered sequence to assess actual art and motion quality. It requires access to an Unreal-capable workstation or cloud machine and suitable assets; those prerequisites are not currently established in this workspace.

Babylon.js remains a credible option when direct browser interaction, simple delivery and low hosting cost are the first priorities. It still requires production assets and skilled animation work. Its current procedural scene is not evidence of the quality ceiling of the engine.

| Path | What the viewer receives | What must be established |
| --- | --- | --- |
| Unreal visual prototype | A recorded animation embedded in a static webpage | Usable Unreal runtime, assets, motion quality and a correctly labeled recording |
| Babylon visual prototype | An interactive WebGL scene on a static webpage | Browser-ready assets, convincing motion and measured performance on a reference GPU |

Select one route for the prototype. A second engine experiment is warranted only if the selected route fails a specific quality or delivery requirement. Do not build two full rendering stacks.

**Exit gate:** the user can open the link on the target device and judge a real cricket sequence. Review a fixed reference shot for believable bowling, grounded movement, bat/ball contact and readable camera direction. Record remaining visual defects. If it does not look good enough, revise the art/animation approach before adding clubs or leagues.

**Honesty requirement:** a rendered recording proves visual quality only. A 60 FPS video export does not prove real-time rendering, responsive gameplay or agent-controlled outcomes. A static website can distribute the recording without a running database or GPU server.

## Milestone 2 — prove the player agent and its skill limits

**User-facing deliverable:** a small lab with three clearly differentiated player profiles, visible tactical decisions and a before/after training report.

Reuse the existing simulation as a baseline. Separate ability from learned decision quality. Compare weak, medium and strong attributes using controlled scenarios; then train a selected player's decision policy without silently raising its attributes. Retain per-player identity, practice history, versioned policies and rejected candidates.

Evaluate on protected scenarios across several seeds and opponent styles. Report uncertainty and the heuristic baseline, not just a favorable match. A learner can be useful without improving after every session. Any claim of cricket accuracy still requires rules review and calibration.

Introduce an LLM experiment for bounded tactical planning or post-match reflection. Use structured output, a timeout and a legal fallback. Compare cost, latency and decision quality against the existing policy before assigning it a production role. The rules engine remains responsible for legal actions and outcomes.

**Exit gate:** a reproducible report shows skill-dependent behavior, independent player state and accepted or rejected learning updates. Exact saved decisions and outcomes survive reloads. No LLM or autonomous-improvement claim is based only on generated explanations.

## Milestone 3 — connect the agent to one complete over

**User-facing deliverable:** the player profile and agent policy produce an over that the selected renderer presents faithfully, with scoreboard, decision labels and replay.

Define a versioned event contract: player/policy identity, delivery context, validated action, outcome, timing and presentation parameters. The renderer consumes these events. A later training run must not change an already saved replay.

For a browser renderer, serve match events to the viewer. For Unreal, first connect the event consumer to the rendering project; then separately prove the spectator output and website playback path. A disconnected cinematic is not completion of this milestone.

**Exit gate:** multiple uncurated event sequences render correctly; score and replay agree with the server; the user can explain how the selected player's abilities and choices affected the over. Record where animation coverage still fails, including misses and wickets.

This is also the first **real-time 60 FPS** gate: name the reference GPU and resolution, run a warmed-up ten-minute scenario, and record actual frame times, stalls and dropped frames. If delivery uses encoded video, measure renderer FPS, encoder output, audio sync and end-to-end latency separately. Choose test hardware and cost limits before making a performance commitment.

## Milestone 4 — a hosted, persistent playable demo

**User-facing deliverable:** open one verified public URL, create a uniquely named player within budget, play, train, reload and find the same player and history.

Add persistence and access control when that loop is ready. Reuse the existing healthy Supabase project if suitable; no new project is required merely to restart planning. Configure and test the application connection end to end before handing over a link. A single-provider application/database setup is an alternative if it measurably reduces operational complexity, subject to its cost and durability terms.

For Unreal-based live presentation, budget GPU rendering and video delivery separately from the website/API/database. For browser rendering, the viewer's device renders the scene; this reduces server GPU requirements but still needs device testing.

**Exit gate:** verify from a clean browser session that the actual public URL loads, any login works, a complete over plays, player learning persists, and a service restart preserves state. Preserve the user's game data during checks. Give the user a short walkthrough and measured limitations.

## Expand only after these gates

The next release adds legal squads and short matches, rewards and progression, atomic transfers, and the autonomous manager Agent Arena. Retain the requirements for equal budget constraints, persistent player identity, controlled learning and public match histories. Monetization follows evidence that owners return to their players and spectators return to matches.

## Ownership, resources and estimates

Engineering covers simulation, policy evaluation, event integration, the website and deployment. A 3D generalist or technical animator must supply or adapt cricket motion and assets; engine choice does not replace this work. The visual prototype also needs a reference device and, for Unreal, suitable editor/rendering access.

The user has selected visual quality first, set the US$300 prototype ceiling, and subsequently asked to continue with notification whenever paid resources are created. Follow the [current AWS readiness and cost record](AWS_VISUAL_PROTOTYPE.md): announce the actual resource and verified expected charge before starting billing, establish the asset/engine prerequisites and implement stop/cleanup controls. Estimate dates after checking the selected assets and toolchain; the current evidence does not support a reliable promise of ESPN-level production in a fixed number of days.

Every milestone should end with something reviewable: a working link or artifact, a short acceptance record, actual measurements and explicit limitations. The next milestone begins only when the preceding result is useful to the user.
