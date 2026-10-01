---
name: hermes-desktop-maintenance
description: >-
  Mantenimiento y troubleshooting de la app desktop de Hermes (Electron) en Linux.
  Cubre: módulos nativos faltantes (pty.node), rebuild post-actualización,
  errores de empaquetado, electron-rebuild, y re-empaquetado del .asar.
category: software-development
triggers:
  - hermes desktop fails to start after update
  - pty.node error
  - native module error in Hermes Desktop
  - Electron ABI mismatch in Hermes
  - Failed to load native module
  - wake word transcribes but nothing happens
  - hey hermes no reply / no audible response
---

# Hermes Desktop Maintenance (Linux)

## Voice / wake word diagnostics

For "hey hermes" transcribes but nothing happens / no reply — a different pipeline
than the native-module crashes below. See
`references/voice-wake-word-diagnostics.md`: stage-by-stage flow, gui.log markers,
state.db session forensics, and the dictation-vs-conversation distinction
(mic button inserts text into the input; ear icon auto-submits).

## When This Applies

Hermes Desktop crashes on launch after an update with an error like:

```
Error: Failed to load native module: pty.node, checked: build/Release, build/Debug, prebuilds/linux-x64
```

Or more generally, any native Node.js module (`*.node`) that fails to load in the
packaged Electron app after `git pull` + `npm install`.

## Root Cause

`node-pty` (v1.1.0 at time of writing) ships prebuilt binaries only for:
- `darwin-arm64`, `darwin-x64`
- `win32-arm64`, `win32-x64`

**No prebuild exists for `linux-x64`.** On Linux, the module must be compiled
from source against the specific Electron ABI version. A plain `npm install`
skips this step — it finds no matching prebuild and leaves `build/Release/`
empty. `stage-native-deps.mjs` then copies an empty directory, and the packaged
`.asar` ships without `pty.node`.

### The REAL recurring root cause on this repo: blocked install-scripts

The crash after `hermes update` / `git pull` + `npm install` has a sharper root
cause than a *fresh* install: **the Hermes repo enforces an `allowScripts`
policy that blocks npm install-scripts.** When active, `npm ci` / `npm install`
prints:

```
npm warn install-scripts 6 packages had install scripts blocked because they are not covered by allowScripts:
npm warn install-scripts   electron@40.10.2 (postinstall: node install.js)
npm warn install-scripts   node-pty@1.1.0 (install: node scripts/prebuild.js || node-gyp rebuild; ...)
```

Consequence: neither `electron`'s `install.js` (populates
`node_modules/electron/dist/`) nor `node-pty`'s `node-gyp rebuild` (produces
`build/Release/pty.node`) ever runs. So even a *successful* install leaves both
binaries missing and the packaged app crashes on launch. **The fix must not rely
on npm running those scripts** — it must (a) run `node install.js` for Electron
and (b) compile node-pty explicitly (see Permanent Avoidance).

## Fix Steps

Run all commands from `apps/desktop/` inside the Hermes repo:

```bash
cd ~/.hermes/hermes-agent/apps/desktop
```

### 1. Rebuild native modules for Electron

Run from the **repo root** (`~/.hermes/hermes-agent`), not `apps/desktop/`:

```bash
# Electron's postinstall was blocked by allowScripts — restore dist/ manually:
cd ~/.hermes/hermes-agent/node_modules/electron && node install.js

# Compile node-pty against the pinned Electron ABI (v4 CLI — NO --electron-version,
# NO --build-from-source, NO --only; those flags error or are ignored in v4):
cd ~/.hermes/hermes-agent
./node_modules/.bin/electron-rebuild -f -w node-pty
```

The compiled output lands in:
`node_modules/node-pty/build/Release/pty.node`

### 2. Rebuild the desktop dist

```bash
npm run build
```

This runs: `vite build` (renderer), `bundle-electron-main.mjs` (main process),
and `stage-native-deps.mjs` which copies `pty.node` from
`node_modules/node-pty/build/Release/` into
`dist/node_modules/node-pty/build/Release/`.

### 3. Repackage the app

```bash
PATH="../../node_modules/.bin:$PATH" \
  NODE_OPTIONS=--max-old-space-size=16384 \
  node scripts/run-electron-builder.mjs --dir
```

This creates a fresh `release/linux-unpacked/` with `pty.node` properly
unpacked alongside the `.asar`.

### 4. Verify

```bash
./release/linux-unpacked/Hermes
```

Check that no `Uncaught Exception: Error: Failed to load native module: pty.node`
appears in the output. Warnings about `gitstatus`, `fs.Stats constructor is
deprecated`, and `dbus/object_proxy.cc: UnitExists` are normal Chromium/Electron
noise on Linux — not a problem.

## Architecture Notes

### electron-builder packaging flow

```
npm run build
  ├─ vite build               → dist/index.html + JS/CSS assets
  ├─ bundle-electron-main.mjs → dist/electron-main.mjs
  └─ stage-native-deps.mjs    → dist/node_modules/node-pty/{lib/,build/Release/,package.json}

npm run builder -- --dir
  └─ electron-builder
       ├─ before-pack.mjs  → runs stage-native-deps again per target
       ├─ asar packing     → dist/ → app.asar (with asarUnpack for **/*.node)
       └─ after-pack.mjs   → (optional signing)
```

### asarUnpack config

From `package.json`, the `build` field:

```json
"asarUnpack": ["**/*.node", "**/prebuilds/**", "dist/**"]
```

The `dist/**` pattern unpacks everything under `dist/` from the asar so native
binaries can be loaded directly by Node.js (which cannot `require()` from inside
an archive). The asar still records the file entries — without that record,
Electron won't redirect `require()` calls to the unpacked location.

### Why `pty.node` specifically

Hermes Desktop uses `node-pty` to spawn the embedded terminal (xterm.js).
It is the only native module dependency in the desktop app. If Electron's ABI
changes (which happens on every minor Electron version bump), the bundled
binary must be recompiled.

## Pitfalls

- **`electron-rebuild` v4 CLI flag drift**: passing `--electron-version 40.10.2`,
  `--build-from-source`, or `--only node-pty` to the v4 CLI throws
  `ERR_PARSE_ARGS_UNKNOWN_OPTION` or is silently ignored. The v4 CLI reads the
  Electron version from the workspace `package.json` (`build.electronVersion`).
  Correct invocation (from repo root):
  `./node_modules/.bin/electron-rebuild -f -w node-pty`. Do NOT pass version flags.
- **`node-gyp rebuild --target <ver>` fallback fails on Electron**: bare
  `node-gyp` looks for headers under `~/.cache/node-gyp/<ver>` (Node layout), not
  Electron's, and errors `gyp: <ver> not found`. Only `electron-rebuild` (or
  `@electron/rebuild`'s JS API with `ELECTRON_VERSION` set) resolves Electron
  headers correctly. Never fall back to bare `node-gyp rebuild`.
- **Forgetting to repackage after `stage-native-deps`**: copying the binary to
  `dist/` is not enough — the `.asar` in `release/` is immutable and must be
  regenerated via `npm run pack`.
- **Direct file copy into `app.asar.unpacked/` won't work**: Electron only
  redirects `require()` calls to unpacked files if the `.asar` records their
  paths. Adding files manually looks correct but the asar has no routing entry —
  the module cannot be found.
- **The launcher content-hash stamp lies about native deps**: `hermes desktop`
  (cmd_gui in `hermes_cli/main.py`) compares a JS *content hash* to decide whether
  to rebuild. If the JS is unchanged but `pty.node` was wiped by a blocked install,
  the stamp says "up to date" → build skipped → crash. Any durable fix must add a
  real precondition (`pty.node` present) to `_desktop_build_needed`.

## Recurrence After `hermes update` (why the stamp lies)

The bundled launcher (`hermes desktop`) decides whether to rebuild by comparing a
content hash of the **JS sources** (`_desktop_build_needed` in `hermes_cli/main.py`,
stamp stored under `$HERMES_HOME`). It does **not** check for `pty.node` or the
Electron ABI version.

Consequence: if the JS sources are unchanged but the native binary is missing or
stale — fresh clone, a `hermes update` that bumped Electron, or a switch to a new
machine — the stamp "matches" → the launcher skips the build → `pty.node` is never
compiled → the app crashes on launch with the native-module error even though it
just printed `✓ Desktop packaged app is up to date (content stamp matches)`.

The only launcher flags that force the native rebuild are `--force-build` (ignores
the stamp) and a real source change. Neither prevents the recurrence automatically
on the next update.

## Permanent Avoidance (launcher wrapper)

A wrapper that checks the *real* precondition — `pty.node` present AND the Electron
ABI unchanged — and only then runs the heavy native rebuild (steps 1–3 above). On
the common case it launches the already-packaged app directly (fast). See
`scripts/hermes-desktop-safe.sh`.

Usage: drop the script in `~/.local/bin`, `chmod +x`, alias `hdesk='hermes-desktop-safe'`
in your shell rc, and run `hdesk` instead of `hermes desktop`. The wrapper records
the compiled Electron ABI in `apps/desktop/.native_abi_stamp`; if Electron is
upgraded it rebuilds once, then launches fast on subsequent runs. This is the
durable fix for the recurring crash — the user-facing answer to "how do I stop
this from happening again?".
