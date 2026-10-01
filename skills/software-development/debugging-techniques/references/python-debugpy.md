# Python Debugging (pdb + debugpy)

## Quick Reference

| Tool | Use case | Start command |
|------|----------|--------------|
| `breakpoint()` | Quick inline debugging | Add to source, run normally |
| `python -m pdb` | No source edits needed | `python -m pdb script.py arg1` |
| `debugpy` | Remote attach / long-running | `python -m debugpy --listen 5678 --wait-for-client script.py` |
| `remote-pdb` | Simplest remote/agent-friendly | `pip install remote-pdb` then `set_trace(port=4444)` + `nc localhost 4444` |
| `pytest --pdb` | Test debugging | `pytest -x --pdb -p no:xdist` |

## pdb Commands (inside `(Pdb)` prompt)

| Command | Action |
|---------|--------|
| `n` | step over |
| `s` | step into |
| `c` | continue |
| `bt` / `w` | backtrace / where |
| `l` / `ll` | list source / full function |
| `u` / `d` | move up/down stack |
| `p expr` / `pp expr` | print / pretty-print |
| `!stmt` | execute arbitrary Python |
| `interact` | full Python REPL (Ctrl+D to exit) |
| `b file:line` | set breakpoint |
| `b func, cond` | conditional breakpoint |
| `cl N` | clear breakpoint N |
| `q` | quit |

## Recipes

### Local breakpoint
```python
breakpoint()  # drops into pdb at this line
```

### Debug a pytest test
```bash
scripts/run_tests.sh tests/foo_test.py::test_bar --pdb -p no:xdist
# Or directly:
source .venv/bin/activate
python -m pytest tests/foo_test.py::test_bar --pdb
```

### Remote debug with debugpy (attach to running process)
```bash
# In target process:
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()
debugpy.breakpoint()

# Or launch directly:
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py
```

### Remote debug with remote-pdb (agent-friendly)
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)  # blocks until connection
```
Then: `nc 127.0.0.1 4444` → you get a `(Pdb)` prompt.

### Attach to already-running PID
```bash
python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
```
Note: May need `echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope` on hardened kernels.

## Hermes-Specific Debugging

### Tests (in Hermes repo)
Always add `-p no:xdist` because pdb does NOT work under pytest-xdist.

### `run_agent.py` / CLI — one-shot
Add `breakpoint()` near the suspect line, then run `hermes` normally.

### `tui_gateway` subprocess
Use `remote-pdb` at the specific RPC handler:
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)
```
Trigger the matching slash command from the TUI, then `nc 127.0.0.1 4444`.

### `_SlashWorker` subprocess
Same pattern — `remote-pdb` with `set_trace()` inside the worker's exec path.

### Gateway (`gateway/run.py`)
Long-lived. Use `remote-pdb` at a handler, or `debugpy --wait-for-client` if restarting.

## Pitfalls

1. **pdb under pytest-xdist silently does nothing.** Use `-p no:xdist` or `-n 0`.
2. **`breakpoint()` in CI / non-TTY hangs.** Never commit. Pre-commit grep: `rg -n 'breakpoint\(\)' --type py`
3. **`PYTHONBREAKPOINT=0`** disables all `breakpoint()`. Check if your breakpoint isn't hitting.
4. **`debugpy.listen` blocks only with `wait_for_client()`.** Without it, execution continues.
5. **Threads.** pdb debugs only the current thread. Use `debugpy` (DAP) for multi-threaded.
6. **asyncio.** pdb works in coroutines but `await` inside pdb requires Python 3.13+.
7. **`scripts/run_tests.sh` strips credentials.** Debug with raw pytest first if the bug depends on user config.
8. **Forking / multiprocessing.** pdb does NOT follow forks. Debug one process at a time.

## Verification Checklist

- [ ] `python -c "import debugpy; print(debugpy.__version__)"` works
- [ ] Port is actually listening: `ss -tlnp | grep 5678`
- [ ] First breakpoint actually hits
- [ ] Stray `breakpoint()` / `set_trace()` removed before commit
