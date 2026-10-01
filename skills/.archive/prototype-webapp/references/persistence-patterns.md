# Persistence patterns for prototypes

## Problem

Node.js native SQLite modules often fail in restricted or fresh environments:
- `better-sqlite3` requires node-gyp/prebuild install, which may be blocked or fail on newer Node versions (Node 26 has no prebuild at time of writing; `npm rebuild better-sqlite3` can hang >60s and fail).
- `sqlite3` has similar native build requirements.
- This breaks prototype delivery even though SQLite itself is fine.

## Pattern A: sql.js

Use when:
- You want zero native dependencies.
- The dataset is small to medium; full-database export/import is acceptable.
- Write-ahead log behavior is not required.

Tradeoffs:
- Simpler install: `npm install --ignore-scripts sql.js` (no native build, pure WASM).
- Persistence model: read file → Database → mutate → export → write file.
- Writing the whole `.db` on *every* mutation is wasteful — debounce via a short `setTimeout` (see helper below).
- Concurrent writes are unsafe by default; serialize writes or append-only.
- `db.run(sql, params)` returns `undefined` — get the inserted row id with `db.exec("SELECT last_insert_rowid() as id")[0].values[0][0]`.
- **CRITICAL: never use `db.exec(sql, params)` for statements with bound parameters (`?` placeholders).** sql.js's `exec()` expects raw SQL strings and *silently ignores* any params argument — INSERTs write NULL/empty values, UPDATEs match nothing, no error is thrown.
- Good for prototypes, demos, internal tools.

### Minimal helpers (ESM, tested on Node 26)

```js
import initSqlJs from 'sql.js';
import fs from 'fs';

let _db = null;
let _persistTimer = null;

export async function bootstrap(path) {
  const SQL = await initSqlJs();
  _db = fs.existsSync(path) ? new SQL.Database(fs.readFileSync(path)) : new SQL.Database();
  return _db;
}

// Debounce file writes — batch many mutations per ~50ms tick.
function persist(path) {
  clearTimeout(_persistTimer);
  _persistTimer = setTimeout(() => fs.writeFileSync(path, Buffer.from(_db.export())), 50);
}

// Prepared-statement wrapper — creates a FRESH statement per call.
// DO NOT cache statements with `stmt.reset()` — sql.js statements become
// "Statement closed" after step()/reset() when reused from a cache.
// Always: _db.prepare() → bind → step → getAsObject → free().
export function prepare(sql, path) {
  return {
    all: (...p) => {
      const stmt = _db.prepare(sql);
      stmt.bind(p.map(v => v === undefined ? null : v));
      const rows = [];
      while (stmt.step()) rows.push(stmt.getAsObject());
      stmt.free();
      return rows;
    },
    get: (...p) => {
      const stmt = _db.prepare(sql);
      stmt.bind(p.map(v => v === undefined ? null : v));
      const row = stmt.step() ? stmt.getAsObject() : undefined;
      stmt.free();
      return row;
    },
    run: (...p) => {
      const stmt = _db.prepare(sql);
      stmt.bind(p.map(v => v === undefined ? null : v));
      stmt.step();
      stmt.free();
      persist(path);
      const r = _db.exec("SELECT last_insert_rowid() as id");
      return { lastInsertRowid: r.length ? r[0].values[0][0] : null };
    },
  };
}
```

### Pitfall: Statement caching → "Statement closed" on 2nd request

**Wrong pattern that passes the first call but fails on the second:**
```js
// BUG: caching + stmt.reset() reuses a closed statement
const _cache = new Map();
function _getStmt(sql) {
  if (_cache.has(sql)) return _cache.get(sql);
  const stmt = _db.prepare(sql);
  _cache.set(sql, stmt);
  return stmt;
}
function all(sql, params) {
  const stmt = _getStmt(sql);
  stmt.bind(params);
  while (stmt.step()) ...
  stmt.reset(); // ← after this, statement is "closed" for reuse
  return rows;
}
```

**Symptom**: first API call → HTTP 200 with data. Second call → HTTP 500 with `<pre>Statement closed</pre>`. sql.js `reset()` doesn't fully reset the statement for rebinding. Always create fresh with `_db.prepare()`, always clean up with `stmt.free()`.

### Bootstrap order

`initSqlJs` is async, so the server must boot the DB *before* `app.listen`:

```js
bootstrap(DB_PATH).then(() => app.listen(PORT, …));
```

## Pitfall: npm `allow-scripts` blocks binary install

A global `~/.npmrc` with `allow-scripts=node-pty` (or any restricted allowlist) blocks packages with install scripts from creating `.bin/` symlinks — `concurrently`, `esbuild`, and `better-sqlite3` all silently fail to install their binaries even though the package directory appears in `node_modules/`.

Symptom: `npm install` reports "added N packages" but `ls node_modules/.bin/<pkg>` is empty.

Fix: drop a local `.npmrc` with `allow-scripts=*`, then `rm -rf node_modules package-lock.json && npm install --no-audit --no-fund`. For esbuild: `npm install-scripts approve esbuild && npm rebuild esbuild`. Manual fallback: `ln -sf ../node_modules/vite/bin/vite.js node_modules/.bin/vite`.

## Pitfall: root install wipes client/node_modules

Installing a dep at the *root* can wipe a sibling `client/node_modules`. Re-run `npm install` inside `client/` after touching root deps.

## Pitfall: Vite phantom version — npm silently skips install

`npm create vite@latest` may scaffold `"vite": "^8.1.1"` (doesn't exist). npm reports success but vite/tailwind/plugin-react are silently absent from `node_modules/`. Pin to `^6.0.0` and `@vitejs/plugin-react@^4.3.4`, then reinstall fresh.

## Pattern B: better-sqlite3

Use when performance/concurrency demands it. If `npm rebuild` fails or prebuilds missing for your Node version, fall back to sql.js.

## Decision rule

Start with sql.js for prototypes. Upgrade to better-sqlite3 only if needed.
