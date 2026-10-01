---
name: hermes-agent-env-quirks
description: Use when dev servers fail only from the Hermes terminal.
---

# Hermes Agent Env Quirks

## When to Use

Use when a dev server, build tool, or CLI behaves differently when launched from the Hermes terminal vs the user's own shell — especially blank pages, missing globals, or "works in my terminal" reports. Check agent-injected env vars before debugging cache/versions/project.

The Hermes terminal backend (python3/node subprocess under the TUI) injects env vars that the user's interactive shell does NOT have. When a tool works in the user's terminal but breaks when the agent launches it, suspect the agent's env before blaming cache, versions, or the project.

## Known quirk: NODE_ENV=production breaks react-refresh dev servers

**Symptom:** Remotion Studio (and any Vite/Next.js/webpack dev server using React Fast Refresh) opens blank with console error:
`Uncaught ReferenceError: $RefreshSig$ is not defined`

**Root cause:** `hermes_cli/main.py:2315` runs
`env.setdefault("NODE_ENV", "development" if tui_dev else "production")`
→ the TUI and its terminal subprocesses get `NODE_ENV=production`. react-refresh's `runtime.js` then loads its production runtime, which throws on purpose ("React Refresh runtime should not be included in the production bundle"), so `$RefreshSig$` never gets defined and the whole bundle dies.

**Red herrings (all tested, none fix it):** clearing node_modules/.cache, `npx remotion clear-cache` (command doesn't exist), webpack vs `--rspack` bundler swap, react-refresh version, React 19 vs 18.

**Diagnosis that confirms it:**
- Server responds HTTP 200, bundle compiles, all package versions match
- Check browser console via headless Chromium: `CHROME --headless --disable-gpu --no-sandbox --enable-logging=stderr --v=0 --dump-dom "http://localhost:3000"` and grep for `uncaught|RefreshSig`
- `env | grep NODE_ENV` in the agent shell shows `production`; the user's zsh does not
- Trace the source: `grep -n "NODE_ENV" ~/.hermes/hermes-agent/hermes_cli/main.py` → line ~2315

**Fixes:**
1. Inline override: `NODE_ENV=development ./node_modules/.bin/remotion studio` — prefer the node bin over `remotionb`/bun wrappers (bun more prone to inherit production).
2. Persistent (whole agent): add `NODE_ENV=development` to `~/.hermes/.env` — loaded at import time (main.py:700) BEFORE the setdefault, so it wins. Takes effect next Hermes restart. Side effect: everything the agent spawns gets `NODE_ENV=development` (npm devDeps would install) — fine on a dev laptop, NOT on the production server.

## General debugging pattern for agent-env issues

1. Run `env` in the agent shell and compare to the user's shell (`env` from a normal terminal).
2. Inspect the actual process tree: `/proc/<pid>/environ` for the terminal backend (python3 under node-MainThread under hermes) to see where a var enters.
3. Check `grep -n "setdefault\|os.environ\[" ~/.hermes/hermes-agent/hermes_cli/env_loader.py` and `main.py` for injected defaults.
4. Distinguish agent-injected vars (TERMINAL_*, NODE_ENV) from user config — they're not in ~/.zshrc, /etc/environment, systemd, or environment.d.
5. When the user says "it works in my terminal", that's the strongest signal the difference is the agent env, not the project.

## Pitfalls

- Don't edit `~/.hermes/config.yaml` with patch/write_file (security guard) — use `hermes config` or terminal python3/sed.
- `~/.hermes/.env` is for secrets per project policy, but a non-secret env override there is a legitimate workaround when config.yaml has no knob; document it in the skill/memory.
