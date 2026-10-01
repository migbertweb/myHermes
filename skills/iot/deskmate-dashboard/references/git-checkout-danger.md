# Git Checkout Danger — Uncommitted Changes Lost

## What Happened (2026-07-19)

After integrating the WS2812B LED module into DeskMate, the user wanted to test without it to isolate a display issue. `git checkout -- main/main.c main/CMakeLists.txt` was used to revert the LED changes. **However, main.c had accumulated many uncommitted fixes** from prior sessions (layout scale changes, button active-low fix, POP always-visible, sensación removal, forecast font sizing). All of these were lost because there was only a single initial commit.

## Symptoms

- Display shows old layout (missing font size changes, POP at wrong scale)
- Button not responding correctly (active-low logic missing negation)
- "Sensación térmica" line present when it should be removed
- Forecast temperatures and POP at scale 1 instead of scale 2

## Prevention

```bash
# BEFORE reverting any feature, commit current state:
cd /home/migbert/proyectos/deskmate
git add -A
git commit -m "WIP: current state before reverting feature X"
```

Then revert safely:
```bash
git checkout -- <files>  # safe now — changes are in previous commit
```

Or use `git stash`:
```bash
git stash push main/main.c main/CMakeLists.txt
# ... do work ...
git stash pop
```

## Recovery

If changes were lost and the skill (`deskmate-dashboard`) is up to date, the code can be reconstructed from the skill's documented layout, pitfalls, and code examples. session_search may also recover diffs from prior agent sessions.
