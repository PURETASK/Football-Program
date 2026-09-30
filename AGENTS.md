# NFL FIDOS — Base44 Dev Environment

## Architecture

- **Backend**: Pure Python stdlib HTTP server (`src/nfl_fidos/`). No pip dependencies. Entry point: `python -m nfl_fidos.server`. Serves API on port 8080.
- **Frontend**: React 19 + Vite 8 + TypeScript. Lives in `frontend/`. Vite dev server on port 5173, proxies `/health` and `/v1` to the backend. App base path is `/app/`.
- **Database**: SQLite at `NFL_FIDOS_DATABASE` (defaults to `.runtime/nfl_fidos.sqlite3`). In compose, stored in the `db-data` volume at `/data/nfl_fidos.sqlite3`.

## Running in Base44

```bash
docker compose -f docker-compose.base44.yml up -d --build
```

Two services:
- `api` — Python backend (built from `Dockerfile.dev`, source bind-mounted, `PYTHONPATH=/app/src`). Seeds demo data on startup (idempotent — returns "already_seeded" if data exists), then starts the server.
- `web` — Vite dev server (node:22-alpine, `frontend/` bind-mounted, port 3000→5173)

## Auth & Demo Data

- The app requires a signed Bearer token. Tokens are issued with `NFL_FIDOS_AUTH_SECRET`.
- A development placeholder secret is auto-generated via `generate_development_secrets` and delivered through `/run/base44/app.env`.
- Demo data is seeded by the `seed` compose service using `scripts/seed_demo_data.py`.
- To issue a demo token for the UI's "Connect your organization" dialog:
  ```bash
  docker compose -f docker-compose.base44.yml exec api python scripts/issue_demo_token.py --role program_owner --ttl-seconds 86400
  ```
  Use org ID `ORG-DEMO-FIDOS-001` (pre-filled in the dialog).

## Vite Config

`frontend/vite.config.ts` reads `VITE_API_PROXY_TARGET` (defaults to `http://127.0.0.1:8080`) so the proxy target works both locally and in compose (where it points to `http://api:8080`). `allowedHosts: true` accepts the preview's external hostname.

## Verification

- Backend health: `curl http://localhost:8080/health`
- Frontend: open `http://localhost:3000/app/` in the preview
- After loading, use the session dialog (key icon) to paste a demo token
