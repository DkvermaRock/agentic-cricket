# Temporary hosting on Render and Supabase

Supabase stores persistent game state. Render serves the API and compiled website. Babylon.js renders the stadium in the viewer's browser; neither service needs Unreal Engine or a GPU for this architecture.

## 1. Create the Supabase project

The default project name is `agentic-cricket-poc` in `us-east-1`, paired with Render Virginia. A Free organization with an available project slot is required by the supplied helper.

1. Generate a personal access token at <https://supabase.com/dashboard/account/tokens>.
2. Choose a new strong database password and store it in your password manager. This is the password for the new project, so no existing project is needed.
3. Enter the token as `SUPABASE_ACCESS_TOKEN` and the password as `SUPABASE_DB_PASSWORD` in the secure environment settings. For proxy-backed secrets, allow `api.supabase.com` for both. Do not paste either into chat or commit them.
4. With the bindings available, run the helper from the repository root:

```sh
python deploy/create_supabase.py --organizations
python deploy/create_supabase.py
python deploy/create_supabase.py --create
```

The middle command is a read-only plan. The final command creates the project. One authorized organization is selected automatically; if several exist, set `SUPABASE_ORGANIZATION_ID` to the intended organization slug. Optional `SUPABASE_PROJECT_NAME` and `SUPABASE_REGION` override the defaults.

An existing project with the same name in the organization is reused. The helper does not change its password. It refuses unknown/paid plans and unavailable regions. If a create request times out, check the dashboard before rerunning; the request may already have succeeded. The receipt in ignored `build/cloud/supabase-project.json` contains only public project metadata.

Wait until the project is healthy in the dashboard. Open **Connect**, select the **Session pooler**, and copy its PostgreSQL URI. Replace the password placeholder with the URL-encoded database password and include `sslmode=require` (or a supported verified TLS mode). Prefer the IPv4-compatible session pooler for temporary hosting; do not substitute the browser publishable key or service-role key.

## 2. Deploy the repository on Render

Open <https://dashboard.render.com/select-repo?type=blueprint> and select `DkvermaRock/agentic-cricket`, branch `main`. Render should discover `render.yaml`.

- Service: `boundary-agent-arena`, Docker, Virginia, Free plan.
- Supply `DATABASE_URL` using the Supabase session pooler URI in Render's secret environment field.
- The Blueprint enables `CRICKET_REQUIRE_AUTH` and generates `CRICKET_DEMO_PASSWORD`; username defaults to `cricket`.
- After deployment, use Render's service URL and the generated password. `/api/health` is public; the website and other API routes require the shared credentials.

The API creates its schema on first startup, initializes 100 coins only if the club is absent, and enables PostgreSQL row-level security without browser policies. Database access stays on the server. For this POC use the project owner connection supplied by the Connect dialog. Do not reuse a production database with unrelated tables named `club`, `players`, `reports` or `matches`.

Proxy-backed environment secrets are substituted only on allowed HTTPS destinations. A Supabase Management API password binding is **not** a usable raw PostgreSQL credential in this execution environment. Configure the actual `DATABASE_URL` securely at Render; never construct it from an opaque proxy placeholder.

Free-host sleep, startup delays, quotas and current provider terms apply. The Blueprint does not select a paid instance. This is a shared private demo; add real user identity and club-level authorization before a public multiplayer launch.

## 3. Verify the deployed service

1. Health returns `status: ok` and `rules_version: boundary-v2`.
2. An unauthenticated page request receives a password challenge.
3. With the demo credentials, the exhibition loads and the six-ball replay finishes at 17/0.
4. Create one intentionally chosen player, confirm the coin deduction, train it, and save an over.
5. Restart the Render service. Confirm that player ID, remaining coins, training report and saved deliveries persist.
6. Run the Performance report on the intended GPU devices. Record resolution, renderer, median/p95 frame time and sustained playback FPS before making a 60 FPS claim.

These cloud checks require the actual deployed URL. Local Docker/PostgreSQL checks do not establish that Supabase or Render are live.

## Docker outside Render

```sh
docker build -t boundary-arena .
```

Run with a securely supplied PostgreSQL `DATABASE_URL`, `CRICKET_REQUIRE_AUTH=true`, and a random `CRICKET_DEMO_PASSWORD` of at least 16 characters. The image runs as UID 10001 and honors `PORT` (default 8000). If using local SQLite, mount a writable persistent directory at `/var/lib/cricket`; an unmounted container filesystem is not durable storage.

When building behind an HTTPS inspection proxy, supply its trusted CA using BuildKit secret `build_ca` and pass the standard proxy build arguments. Preserve TLS verification. No credentials belong in build arguments, image layers or source control.
