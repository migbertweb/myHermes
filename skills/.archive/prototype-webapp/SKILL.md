---
name: prototype-webapp
description: "Build throwaway-to-production web prototypes from a single prompt: Express + SQLite/JSON persistence, minimal EJS/HTML UI, deploy-ready scaffolding with Docker/Dokploy conventions."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [web, prototype, express, sqlite, ejs, dokploy, fullstack]
    related_skills: [plan, spike, subagent-driven-development]
---

# Prototype Webapp

Use this skill when the user asks for a working web app prototype quickly — especially small internal tools, budget apps, kanban, CRUD, dashboards — and wants it runnable locally with optional Dokploy deployment.

## Default stack

- Backend: Express
- Persistence first choice: sql.js when native modules may fail; otherwise better-sqlite3
- Views: EJS for quick server-rendered UI, or plain HTML+JS for API-first apps
- Frontend utilities: optional lightweight inline CSS/JS
- No build step unless requested
- Deploy target: Docker → Dokploy, single container

## File layout

```
project/
├── server.js           # app entry
├── db.js               # persistence layer
├── package.json
├── views/              # EJS if server-rendered
├── public/             # CSS/JS when API + static frontend
└── Dockerfile
```

## Persistence strategy

Prefer the simplest persistence that survives restarts.

- Use sql.js with filesystem export/import when native modules may fail.
- Schema bootstrap must run before `app.listen`.
- Save on every write. Read on startup if file exists.
- All helper wrappers: `run(sql, params)`, `all(sql, params)`, `get(sql, params)`.
- Important: when native DB addons or sql.js are unavailable, fallback to `db.json` sync writes. Avoid implying every prototype must use SQLite.

## Runtime/packaging pitfalls

- Native Node SQLite modules can fail under some Node/AArch64 or restricted install-script environments. If `better-sqlite3` or `sql.js` fail, fall back to a JSON file with `fs.writeFileSync` after each mutation.
- EJS views must only reference locals actually passed from the route. If the view uses `<%- JSON.stringify(stages) %>`, the `res.render('index', ...)` call must include `stages`; otherwise you get `ReferenceError: stages is not defined`.
- When switching a page to API-first frontend data fetching, remove `window.__INITIAL__` or any EJS-injected JSON from the view to prevent stale coupling and render-time crashes.
- Express view cache may retain stale templates after edits. If behavior does not match the saved files, recreate the server process. On Linux, stale port listeners are common: `lsof -tiTCP:PORT -sTCP:LISTEN | xargs kill -9`, then restart `node server.js`.
- **sql.js silent param failure**: `db.exec(sql, params)` silently ignores params — use `db.run(sql, params)` for any statement with `?` placeholders. See `references/persistence-patterns.md` for the #1 silent-failure pitfall.
- **npm `allow-scripts`**: a global `~/.npmrc` with a restricted allowlist blocks `concurrently`, `esbuild`, and `better-sqlite3` from installing binaries. Drop a local `.npmrc` with `allow-scripts=*` if installs report success but `.bin/` symlinks are missing.

## Data APIs

- Server-rendered views: pass data in `res.render('index', { projects, stages })`
- API endpoints: JSON with one model per domain object
- Include EJS-injected `window.__INITIAL__` whenever the frontend needs initial data

## Frontend rules

- Vanilla JS only unless user requests a framework.
- Use `fetch('/')` for initial data streaming only when `window.__INITIAL__` is unavailable.
- Use event delegation sparingly; bind handlers on rendered elements for clarity.
- Escape all dynamic text with a small `escapeHtml()` helper.
- Important: if the page uses API-first JS data loading, do not leave `window.__INITIAL__` or EJS-injected JSON in the view. Mixing both causes duplicate state and often stale or missing render-time variables.

## Fullstack branch (React + Vite + Tailwind)

When the user asks for a richer SPA — dashboards, kanban with drag-and-drop, live charts, multi-tab project views — switch from EJS to a Vite-hosted React frontend while keeping the Express+SQLite backend. See `references/fullstack-react-vite.md` for the scaffold layout, Vite proxy config, `concurrently` dev-scripts pattern, Vite version pinning, DnD-kit kanban pattern, Recharts live data, error-handling for eternal "Cargando…" states, mobile hamburger menu, theme toggle, toast notifications, PDF/print export, datalist autocomplete, and responsive patterns. Raid subsets only as needed; the EJS path above is still the default for quick throwaways.

If the user asks for authentication, see `references/diy-jwt-auth.md` — a lightweight JWT + bcryptjs + cookie-parser pattern that adds <100 lines of backend code and <100 lines of React context. Zero native deps, works with sql.js on any platform.

When the terminal tool blocks background server startup, don't spend multiple turns on workarounds — free the port and tell the user to run `node server.js` themselves.

## npm + devDependencies pitfalls

**NODE_ENV=production skips devDependencies**: If `NODE_ENV=production` is set in the shell, `npm install` skips devDependencies (vite, tailwind, nodemon, etc.). The symptom: package installs appear successful but binary symlinks in `node_modules/.bin/` are missing, and `npx tailwindcss` fails with "command not found".

**Solutions** (in order of preference):
1. Run `npm install --include=dev` to explicitly include devDependencies
2. Temporarily unset `NODE_ENV` with `unset NODE_ENV && npm install`
3. Check if binaries exist: `ls node_modules/.bin/ | grep tailwind`

**Tailwind CSS specific**: After fixing devDependencies, you must still build the CSS:
```bash
npx tailwindcss -i ./src/input.css -o ./public/output.css --minify
```

**npx failure**: If `npx` fails with "npm error could not determine executable to run", it's likely because the devDependencies weren't installed. Fix with `npm install --include=dev` first.

**Alternative**: If you can't install devDependencies, you can generate Tailwind CSS with the CDN version in development (not for production).

## Deploy rules

- Dockerfile: multi-stage node:alpine (builder → production). See `references/docker-dokploy.md` for the full Dockerfile, docker-compose, Dokploy-specific env vars, volume setup, and Nixpacks-vs-Dockerfile pitfall.
- Health check: GET `/api/auth/me` or `/` returns HTTP 200
- No exposed DB ports; data file stays in a volume at `/app/data/`
- **Critical**: default DB path in code MUST be inside the volume directory (e.g., `path.join(__dirname, 'data', 'app.db')`, NOT `path.join(__dirname, 'app.db')`). And `fs.mkdirSync(dirname, {recursive:true})` at bootstrap. Otherwise the DB lands outside the volume and gets wiped on every redeploy. Verify: after second deploy, seed data should NOT re-appear in logs.
- **Critical**: every new server-side `.js` file (notify, activity, etc.) must be added to the Dockerfile's `COPY` commands in the production stage. Missing files produce `ERR_MODULE_NOT_FOUND` on deploy. Also run `npm install <pkg>` and commit both `package.json` and `package-lock.json` when adding new dependencies.
- For Dokploy: set build method to `Dockerfile`, not `Nixpacks`. Configure env vars in the UI.

## Subagent workflow

If implementing via subagents:

1. Architectural decisions: stack, layout, schema → one subagent
2. Backend scaffolding: package.json, server, db, routes → second subagent
3. Frontend: views, static assets, interactivity → third subagent
4. Integration: smoke tests via curl/hosted verification → fourth lightweight subagent

## References

- `references/persistence-patterns.md` — sql.js vs better-sqlite3 fallback rules and helper snippets.
- `references/fullstack-react-vite.md` — React + Vite + Tailwind fullstack conventions and patterns.
- `references/diy-jwt-auth.md` — Lightweight JWT + bcryptjs + cookie-parser auth for Express + sql.js.
- `references/pdf-generation.md` — Client-side PDF generation with jsPDF + jspdf-autotable in Vite/React.
- `references/docker-dokploy.md` — Multi-stage Dockerfile, docker-compose, Dokploy deployment specifics.
- `templates/package.json` — starter dependency set for Express + sql.js + EJS.
- `scripts/smoke.sh` — quick startup/health-check script for local verification.
