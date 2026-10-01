---
name: debugging-techniques
description: "Systematic debugging methodology and language-specific debugger recipes for Python (pdb/debugpy) and Node.js (inspect/CDP)."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [debugging, python, nodejs, pdb, debugpy, inspect, cdp, root-cause]
    related_skills: [test-driven-development]
---

# Debugging Techniques

This umbrella skill covers the full spectrum of debugging — from systematic root-cause methodology through language-specific debugger tooling. It consolidates three previously separate skills into one class-level reference.

## References

- `references/systematic-debugging.md` — Four-phase root cause investigation framework (read errors, reproduce, trace data flow, fix the root cause, not symptoms). Essential BEFORE reaching for any debugger.
- `references/python-debugpy.md` — Python debugging with `breakpoint()` / pdb / debugpy DAP / remote-pdb. Hermes-specific recipes for gateway, tui_gateway, and subprocess debugging.
- `references/node-inspect-debugger.md` — Node.js debugging with `node inspect` CLI REPL and programmatic CDP via `chrome-remote-interface`. Hermes-specific recipes for ui-tui Ink components, Vitest tests, and heap snapshots.

## How to Choose Your Approach

1. **Don't know where to start?** Load `references/systematic-debugging.md` first. Follow the 4-phase process BEFORE touching any debugger.
2. **Python code (Hermes gateway, agent, tests)?** Load `references/python-debugpy.md`. Start with `breakpoint()`.
3. **Node.js code (ui-tui, Ink components, Vitest)?** Load `references/node-inspect-debugger.md`. Start with `node inspect`.
4. **Long-running process you can't restart?** `debugpy` (Python) or CDP attach (Node.js) — both support attaching to a running PID.
5. **Post-mortem on a crash?** `python -m pdb -c continue script.py` (Python) or `kill -SIGUSR1 <pid>` + inspect (Node).

## Quick Reference: Debugging by Language

### Python

| Tool | Use case | Start command |
|------|----------|--------------|
| `breakpoint()` | Quick inline debugging | Add to source, run normally |
| `python -m pdb` | No source edits needed | `python -m pdb script.py` |
| `debugpy` | Remote attach, long-running | `python -m debugpy --listen 5678 --wait-for-client script.py` |
| `remote-pdb` | Simplest remote debug | `remote_pdb.set_trace(port=4444)` + `nc localhost 4444` |
| `pytest --pdb` | Test debugging | `pytest -x --pdb -p no:xdist` |

**Key pitfall:** pdb under pytest-xdist silently does nothing. Always use `-p no:xdist`.

### Node.js

| Tool | Use case | Start command |
|------|----------|--------------|
| `node inspect` | Built-in CLI debugger | `node inspect script.js` |
| CDP (`chrome-remote-interface`) | Automated/programmatic | `npm i -g chrome-remote-interface` + driver script |
| `--inspect` | Attach to running process | `kill -SIGUSR1 <pid>` then `node inspect -p <pid>` |

**Key pitfall:** Breakpoints hit emitted JS, not TypeScript source. Use `--enable-source-maps` with CDP clients.

## Common Debugging Patterns (Language-Agnostic)

### The "Why is this undefined?" Recipe
1. Add a print/tracepoint above the crash line
2. If print is insufficient → breakpoint at the crash site
3. Walk up the call stack to find where the bad value originates
4. Fix at the source, not at the symptom

### The "Intermittent Failure" Recipe
1. Check recent changes (git diff, git log)
2. Run with verbose output and logging
3. If possible, add instrumentation at component boundaries
4. Reproduce under the debugger with controlled conditions

### The "Deadlock / Hang" Recipe
- Python: `remote-pdb` at the suspect handler → `nc` in → `w` for stack → `!import asyncio; asyncio.all_tasks()`
- Node: `--inspect` (no `-brk`) → let it hang → `debug> pause` → `bt`

## Pitfalls Across All Debugging

1. **Never commit `breakpoint()` or `set_trace()`.** Add a pre-commit grep: `rg -n 'breakpoint\(\)|set_trace\(' --type py`
2. **pytest-xdist kills pdb.** Use `-p no:xdist` or `-n 0`.
3. **SSH / headless environments.** `breakpoint()` hangs when there's no TTY. Use `remote-pdb` or `debugpy` instead.
4. **Post-debug cleanup.** Always check for stray debugger calls and kill any debugged processes that are still paused.
5. **Threading.** pdb only debugs the current thread. Use `debugpy` (DAP) for thread-aware debugging.
