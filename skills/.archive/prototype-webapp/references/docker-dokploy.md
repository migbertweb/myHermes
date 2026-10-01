# Docker + Dokploy deployment for Express + React prototypes

When deploying to Dokploy or any Docker host, use a multi-stage Alpine build that compiles the React frontend and bundles only production artifacts.

## Multi-stage Dockerfile (node:alpine)

```dockerfile
# ─── Stage 1: Build frontend ────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund

# Client deps + build
COPY client/package.json client/package-lock.json client/
RUN cd client && npm ci --no-audit --no-fund
COPY client/ client/
RUN cd client && npx vite build

# ─── Stage 2: Production image ──────────────────────────────
FROM node:22-alpine AS production

WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/client/dist ./client/dist
COPY package.json server.js db.js auth.js ./
RUN mkdir -p /app/data && chown -R node:node /app
USER node

ENV PORT=3001
ENV NODE_ENV=production
EXPOSE 3001
CMD ["node", "server.js"]
```

Key decisions:
- `node:22-alpine` — ~120 MB final image. Slim enough for Dokploy.
- `USER node` — not root in production.
- `client/dist/` is the Vite build output served by Express SPA fallback.
- `DB_PATH` env var (default `/app/data/workapp.db`) → persist via Docker volume.

## docker-compose.yml for Dokploy

```yaml
services:
  app:
    build: .
    restart: unless-stopped
    ports:
      - "3001:3001"
    volumes:
      - app_data:/app/data
    environment:
      - NODE_ENV=production
      - DB_PATH=/app/data/workapp.db
      - JWT_SECRET=${JWT_SECRET:-change-me-in-production}
      - ADMIN_USER=${ADMIN_USER:-admin}
      - ADMIN_PASS=${ADMIN_PASS:-change-me}
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3001/api/auth/me"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

volumes:
  app_data:
```

## Dokploy specifics

1. Dokploy auto-detects build method. If it picks **Nixpacks** (default), it'll run `npm install && npm run build` from the root — wrong for multi-stage Dockerfile. Switch to **Dockerfile** in the app settings.
2. Environment variables go in the Dokploy UI (not `.env` file): `JWT_SECRET`, `ADMIN_USER`, `ADMIN_PASS`, `DB_PATH`.
3. The `DB_PATH` must point to `/app/data/workapp.db` so the volume captures it. The `db.js` should read `process.env.DB_PATH || path.join(__dirname, 'workapp.db')`.
4. Port mapping: Dokploy has a "Port" field → set to `3001`.
5. Healthcheck: hit `/api/auth/me` — fast, stateless, confirms server + DB are alive.

## .dockerignore

```
node_modules
client/node_modules
client/dist
workapp.db
*.log
.env
.git
.gitignore
README.md
```

## Pitfall: DB wiped on every Dokploy redeploy (VOLUME NOT MOUNTED)

**The docker-compose.yml has `volumes: app_data:/app/data` but Dokploy does NOT use docker-compose by default.** Dokploy builds from the Dockerfile as a standalone container. The volume declared in the compose file is ignored — `/app/data` lives inside the container filesystem and gets destroyed on every redeploy.

**Symptom**: After deploying, the app starts fresh — all data gone, admin re-seeded.

**Fix**: In Dokploy Dashboard → your app → **Volumes** tab (or Advanced → Storage):
- Add a volume mount: container path `/app/data` → host path or named volume
- Use a named Docker volume (e.g. `workapp_data`) so it persists across redeploys

**Verification**: Create test data → redeploy → data still exists.

## Pitfall: Nixpacks vs Dockerfile

Dokploy defaults to Nixpacks which runs `npm ci` + `npm run build` from the project root. The root `build` script does `cd client && npm run build` — but Nixpacks installs root deps without devDependencies, so `vite` is missing. Result: `sh: 1: vite: not found`.

Fix: switch to Dockerfile in Dokploy settings (one dropdown). The multi-stage Dockerfile handles the separation correctly.

## Pitfall: DB_PATH must be configurable

Hardcoding `path.join(__dirname, 'workapp.db')` means the DB is created next to server.js in the container filesystem — lost on redeploy. Always support an env override:

```js
const DB_PATH = process.env.DB_PATH || path.join(__dirname, 'workapp.db');
```

## Production CMD

Use `CMD ["node", "server.js"]` (exec form), not `CMD node server.js` (shell form). Exec form sends SIGTERM correctly, important for graceful shutdown on Dokploy redeploys.

## Image size

| Stage | Size |
|---|---|
| node:22-alpine base | ~85 MB |
| + node_modules (prod only) | ~10 MB |
| + client/dist | ~1 MB |
| + server source | ~5 KB |
| **Total** | **~120 MB** |
