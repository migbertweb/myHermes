# Remotion Studio blank page — full diagnosis (2026-08-12)

## Symptom
- `remotion studio` serves HTTP 200 (curl shows correct HTML), bundle.js compiles fine ("Built in ~800ms"), but the browser shows a blank white page.
- Firefox console: `Uncaught ReferenceError: $RefreshSig$ is not defined` (source: bundle.js).

## Diagnosis path (what was checked, in order)
1. **Server health**: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/` → 200; `curl -s http://localhost:3000/bundle.js` → 200, 11MB. Server was fine.
2. **Browser vs server**: user's Firefox blank; Playwright Chromium headless with `--enable-logging=stderr` reproduced the same console error → NOT a browser-specific issue.
3. **Version mismatch**: checked all `node_modules/@remotion/*/package.json` versions — all 4.0.509. Not a mismatch (the classic `versions.js` mismatch check).
4. **Bundler swap**: tried webpack default, then `--experimental-rspack` (flag REMOVED in this version → use `--rspack`), then `--rspack`. Identical error at the same bundle.js offset → not bundler-specific.
5. **Runtime vs bun**: tried `./node_modules/.bin/remotion` (node) vs `remotionb` (bun wrapper, used by `bun run dev` scripts in the template). Same error.
6. **Cache**: `rm -rf node_modules/.remotion node_modules/.cache`. Same error.

## Root cause (the actual fix)
- `NODE_ENV=production` was set in the Hermes terminal session environment (injected by the backend — `env | grep NODE` showed `NODE_ENV=production` plus `TERMINAL_*` container vars; it is NOT in ~/.zshrc, ~/.profile, or any shell rc).
- Chain: `react-refresh/runtime.js` does `if (process.env.NODE_ENV === 'production') require('./cjs/react-refresh-runtime.production.js')`.
- The production build **throws on purpose**: "React Refresh runtime should not be included in the production bundle."
- Remotion's `@remotion/bundler/dist/fast-refresh/runtime.js` (which defines `self.$RefreshSig$`) requires `react-refresh/runtime` → the require throws → the fast-refresh entry never runs → every module transformed by the refresh loader calls `$RefreshSig$()` → ReferenceError → blank page.

## Fix
```bash
NODE_ENV=development ./node_modules/.bin/remotion studio --no-open
```
Verified: console clean, Studio renders. User's own terminal is unaffected (no NODE_ENV in their shell).

## Zombie process trap
`process kill` on the background studio wrapper kills the `bunx`/shell parent but leaves the `node (remotion studio)` child bound to :3000. Restart then fails with "Already running on port 3000." Fix:
```bash
pkill -f "remotion studio"   # then verify
ss -tlnp | grep 3000         # must be empty
```

## Red herrings (do NOT repeat)
- Cleaning `node_modules/.remotion` / `.cache` — no effect.
- Switching webpack → rspack — no effect (both inject the same broken refresh runtime).
- Switching bun → node binary — no effect.
- Checking react version / installing react 18 — not needed; root cause was the env var.
