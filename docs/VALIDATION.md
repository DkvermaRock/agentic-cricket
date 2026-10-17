# Validation record — 2026-10-17

Validated in the cloud development workspace. These results do not certify a Render deployment or a Supabase connection.

| Check | Result |
| --- | --- |
| Locked installation, `bash scripts/install.sh` | Passed; Python dependencies, npm dependencies, TypeScript check and production bundle |
| Backend and provisioning safeguards, SQLite only | 30 passed; 1 PostgreSQL-only RLS check skipped |
| Backend and provisioning safeguards with local PostgreSQL 17 | 48 passed; 1 SQLite RLS variant skipped because RLS applies to PostgreSQL |
| Chromium browser suite | 4 passed, including moving 3D ball, pause, camera changes, complete 17/0 exhibition, unique-name rejection, training, saved replay, mobile layout and API failure |
| Docker production build | Passed; locked dependencies and pinned base images, TLS verification retained |
| Render-style container smoke check | Passed with PostgreSQL, required password, custom PORT, UID 10001 and read-only root filesystem |
| Container restart | Player identity, 54 remaining coins, 2,000 practice balls, learning report and exact saved match retained |
| Development startup script | Health, website and API verified; original development club preserved |
| Actual Supabase project / Render service | Not provisioned by this run; credentials unavailable |
| Real GPU / sustained 1080p60 / encoded live stream | Not tested |

The Python test run emits one upstream Starlette warning about the legacy HTTPX TestClient integration. Tests complete successfully. Vite reports a large main bundle: approximately 1.37 MB uncompressed / 333 KB gzip, plus lazy shader/loader chunks.

## What the checks establish

Concurrent requests cannot overspend the club balance or bypass normalized-name uniqueness. Simulated ability distributions respond to initial attributes. Player policies, practice memory, reports and exact match outcomes persist independently. Competing training requests cannot consume the same allowance twice. A rejected candidate does not replace the deployed policy. A non-owner PostgreSQL role with table privileges cannot read rows or insert club state through the default RLS configuration.

Learning tests use held-out delivery samples and a paired utility comparison with a 95% interval. The utility is runs minus six times wickets. This is an experiment against the synthetic outcome model, not evidence of real cricket accuracy, unlimited autonomous improvement, or superiority over the included heuristic baseline.

Supabase helper tests mock the Management API. They verify that planning is read-only, creation uses the intended organization/region, existing projects are reused, and missing credentials, ambiguous organizations, unknown/paid plans and unavailable regions stop creation. They do not establish account authorization or project quota availability.

## Visual evidence and performance

These are browser captures of the actual Docker-served scene, not concept art:

- [Arena screenshot](screenshots/arena.png)
- [End-on camera screenshot](screenshots/end-on.png)

The high-quality capture used Chromium's **SwiftShader software renderer**, with a 1320 × 676 drawing buffer. A short sample including loading and a quality/camera change reported roughly **1 FPS**, median frame interval 714 ms and p95 1480 ms. Balanced software rendering was approximately 2–4 FPS during functional checks. These are diagnostic observations on this constrained CPU environment, not controlled GPU benchmarks. They clearly do **not** demonstrate the 60 FPS target.

The in-app performance download records renderer, resolution, actual frame intervals and current FPS. It does not infer performance from the requested animation timer. High graphics enables full resolution, bloom and filtered shadows; Balanced reduces resolution and effects when software rendering is detected.

## Next visual acceptance gate

Before calling the arena broadcast quality:

1. Run a warmed-up, complete replay on named desktop and mobile GPU devices at a declared resolution. Record median/p95 frame times and dropped frames; for 60 FPS, budget approximately 16.7 ms per frame.
2. Replace procedural cricketers with licensed, optimized skinned glTF assets, cricket-specific motion capture, ball/bat contact alignment, proper foot placement, and convincing catching/throwing transitions.
3. Profile draw calls, shadow passes, post-processing and stadium geometry; improve level of detail and culling against measured bottlenecks.
4. Complete the cricket rules and synchronize all participants before representing the challenge as a full match.
5. If a single shared video broadcast is required, add an authoritative spectator session, capture/encoding, streaming delivery and independent frame-drop measurements. Current browser event replays are not a shared live video broadcast.

Babylon.js keeps remote hosting simple and is the implemented path for this POC. Unreal remains a possible later rendering replacement for a photorealistic production. That would require an actual Unreal project, assets, event consumer, GPU hosting and video delivery work; none is implied by these browser results.
