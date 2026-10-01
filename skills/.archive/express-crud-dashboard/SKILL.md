---
name: express-crud-dashboard
description: Build self-contained Express + EJS dashboards and CRUD tools quickly, with a known-good fallback when native Node DB modules are blocked by install-script approval. Use for single-file deploy, internal tools, kanban, project trackers, or any lightweight admin UI backed by JSON storage.
---

# Express + EJS CRUD Dashboard

## Trigger
Build a small internal dashboard or tool with server-rendered pages and a JSON file store, without fighting native addon installs.

## Stack default
- Runtime: Node.js + Express + EJS
- Storage: `lowdb` v7 + `lodash` + JSON file, unless the user explicitly wants SQLite after successful install
- Frontend: vanilla JS, no build step; hydrate initial page data through `window.__INITIAL__` to cut first-load API calls

## Step 1 — Scaffold
```bash
npm init -y
npm install express ejs lowdb lodash
mkdir -p public views
```

## Step 2 — Server layout
- Top-level `server.js` only: imports, middleware, routes, `app.listen`.
- CRUD shape: `/`, GET detail, POST/PUT/DELETE resource, GET `/api/:id`.
- Persistence helper: `data` object with arrays, `writeData()` sync after every mutation; `nextId(arr)` from max id +1.

## Step 3 — Data flow: API-first, not page-parse-first
Use real API endpoints for data and render the home page from `/api/...` rather than scraping the HTML shell. This removes the need for `window.__INITIAL__` and avoids parsing server-rendered markup into project cards.

If you still want initial hydration, keep it minimal and make it safe: only pass small, bounded arrays, and always make the client recover by calling `/api/...` when the global is missing or malformed.

### Verification before claiming success
After starting the server, confirm actual readiness instead of assuming:
- `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/` → expect `200`
- `curl -s -X POST .../projects ...` → expect `{"success":true,"id":N}`
- `curl -s .../api/projects` → expect JSON array with the created project

If `/` returns `500`, the failure is in the server or view layer, not “the app works but the user did it wrong.”

## Step 3.1 — View-change cleanup
Express can keep an old EJS template in memory after edits. When a view change should have fixed an error but `/` still returns the same stack trace:
1. Kill any process bound to the app port.
2. Confirm the port is actually free.
3. Restart the server from the same directory.
4. Re-test `/` before testing mutations.

## Step 4 — Views
- `views/index.ejs`: shell with header, empty state, grid, modal form, detail view. Do **not** require `stages`, `line_items`, or unrelated server variables in the home render path.
- Keep CSS inline in `public/style.css` with CSS vars. No framework.

## Step 4.1 — Client behavior
- Call `/api/projects` for list state.
- Call `/api/stages/:projectId` for detail/kanban state.
- Show empty state when arrays are empty; don’t depend on server-rendered `project-card` elements existing.

## Step 5 — Storage/DB choice
Preferred for quick tools: plain JSON file with explicit `writeData()` after every mutation. Use `lowdb` only if the user asks for it or you need atomic adapters. This avoids native addon pitfalls on environments where `better-sqlite3` and `sqlite3` install scripts are blocked.

## Step 5 — API CRUD helpers
- `all(sql, params)` / `run(sql, params)` wrappers are SQLite-specific; with JSON storage use in-memory array `.filter()/.map()`.
- Use loose equality `==` on ids coming from URL params because persisted JSON often stores numbers as strings inconsistently.

## Step 6 — Robustness
- Force UTF-8 on `fs.readFileSync` / `fs.writeFileSync`.
- If `better-sqlite3` / `sqlite3` install scripts are blocked, don’t keep retrying native installs. Switch to pure-JavaScript JSON persistence immediately.
- Always clean `README`, `LICENSE`, and `package.json` scripts before publishing to Hermes.
- Serve the app with `node server.js` or background it with Hermes `terminal(background=true)`. Do not mix shell `&` backgrounding inside foreground terminal calls.

## Pitfalls
- Express `res.json` before `res.render` causes “Headers already sent.” JSON first, HTML render in `GET /`.
- In EJS, do not pass huge arrays through `JSON.stringify` without limits.
- URL param ids are strings; compare with `String(x) == req.params.id`, not `===`.
- If install scripts are blocked by smart approval, uninstalling then reinstalling repeats the block; switch to pure-JS storage instead.
- Don’t bind client rendering to `window.__INITIAL__` existing; an API-first client survives template changes.
- `better-sqlite3`/`sqlite3` install failures are recoverable by moving to a JSON-file server store; do not record them as permanent tool failures.
- When seeding child records in a loop, calling `nextId()` inside `.map()` can produce duplicate ids under array mutation. Compute a single base id first, then derive sequential child ids deterministically.
- Express/EJS can retain a stale template in memory after edits. After changing `views/*.ejs`, kill any process on the app port, confirm the port is free, restart the server, and retest `GET /` before testing mutations.
- On Linux, `EADDRINUSE` during restart usually means a previous server process is still bound to the port. Detect with `lsof -tiTCP:<port> -sTCP:LISTEN` and `kill -9` before restarting.
- When browser automation refs become stale or unavailable, debug the UI by executing JS in the browser console: open the modal, fill form fields, dispatch a `submit` event, and inspect `console.log` output for request payloads and responses.
