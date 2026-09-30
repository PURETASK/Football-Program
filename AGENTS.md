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
- Demo data is seeded on API startup (idempotent — returns "already_seeded" if data exists).
- **Quick connect**: The SessionDialog has a "Quick connect (demo)" button that calls `GET /v1/dev/demo-token` to auto-issue a demo token. This endpoint is gated to `NFL_FIDOS_ENV=local` only — it returns 404 in production.
- To issue a demo token manually via CLI:
  ```bash
  docker compose -f docker-compose.base44.yml exec api python scripts/issue_demo_token.py --role program_owner --ttl-seconds 86400
  ```
  Use org ID `ORG-DEMO-FIDOS-001` (pre-filled in the dialog).
- **Proxy note**: The Vite proxy (Node.js) lowercases header names. The backend's Authorization header lookup is case-insensitive to handle this.

## Vite Config

`frontend/vite.config.ts` reads `VITE_API_PROXY_TARGET` (defaults to `http://127.0.0.1:8080`) so the proxy target works both locally and in compose (where it points to `http://api:8080`). `allowedHosts: true` accepts the preview's external hostname. A `rootRedirect` plugin redirects `/` to `/app/` in dev mode.

## Production

- The production `Dockerfile` builds the frontend (Node stage) and serves it from the Python server (single container, port 8080).
- Uses `pip install -e .` (editable) so the server resolves `PROJECT_ROOT` to `/app/` and finds the built frontend at `/app/frontend/dist/`.
- Requires `NFL_FIDOS_AUTH_SECRET` (32+ chars) via a secret manager file or env var.

## Verification

- Backend health: `curl http://localhost:8080/health`
- Frontend: open `http://localhost:3000/app/` in the preview
- After loading, use the session dialog (key icon) to paste a demo token
