---
name: hermes-update-channels
description: Manage Hermes update channels (main, stable, canary).
version: 1.0.0
author: agent
license: MIT
metadata:
  hermes:
    tags: [hermes, update, channels, source-install]
    related_skills: [hermes-config-management, hermes-profile-management]
---

## When to Use

Use when:
- `hermes update` reports "commits behind" and you want to understand if this is normal or a failure
- You want to switch from dev tracking (`main`) to a release channel (`stable`/`canary`) or back
- You need to verify if a release channel is actually published and usable
- You're troubleshooting why `hermes update` fails with "Channel object not found"

# Hermes Update Channel Management

Covers the `hermes update --set-channel` workflow, channel availability, and the difference between dev tracking (`main`) and release channels (`stable`, `canary`).

## Key Concepts

- **Install identity**: Each source install has a sha16 ID (`install_id()` from path) — channels are recorded per-install in `config.yaml` under `update.installs[<sha16>].channel`.
- **Default channel**: Source installs track `main` (dev branch tip). No config entry = `main`.
- **Release channels** (`stable`, `canary`): Require R2 archive metadata at `https://hermes-assets.nousresearch.com/releases/channels/<name>.json`. Currently **not published** (404).
- **Switching**: `hermes update --set-channel <name>` writes the record; next `hermes update` fetches that channel's target.
- **Warning on downgrade**: Switching to an older channel warns: "Switching to an older stable release may not read state written by canary. Back up your data first."

## Procedure: Check Current Channel

```bash
hermes update --check          # shows active channel + behind count
hermes update --install-id     # prints this install's sha16 ID + path
```

## Procedure: Switch Channel

```bash
hermes update --set-channel stable   # persists to config.yaml
hermes update --set-channel canary
hermes update --set-channel main     # back to dev tracking
```

## Procedure: Verify Channel Availability

Before switching, confirm the channel exists in the R2 archive:

```bash
curl -s -o /dev/null -w "%{http_code}" "https://hermes-assets.nousresearch.com/releases/channels/stable.json"
# 200 = available, 404 = not published
```

If 404, the channel is not usable for source installs — only `main` works.

## Cache Behavior

- Passive check (`hermes --version`, banner) uses 24h cached result (`_UPDATE_CHECK_CACHE_SECONDS`).
- Active check (`hermes update --check`, `hermes update`) always fetches fresh.
- Cache file: `~/.hermes/source-checks/<install_id>.json` (identity-keyed, expires on mismatch).

## Pitfalls & Lessons

- **stable/canary not published**: The R2 channel objects (`releases/channels/*.json`) are 404 as of 2026-09-26. `stable` and `canary` fail with "Channel object not found". Only `main` (branch tracking) works for source installs.
- **main is a moving target**: `main` receives pushes multiple times daily. "Behind" count is normal and expected — it means upstream moved, not that update failed.
- **Config location**: Channel records live in `~/.hermes/config.yaml` under `update.installs[<sha16>].channel` — NOT a top-level `update.channel` key (that would be unsafe across profiles sharing one home).
- **Switching back is instant**: `hermes update --set-channel main` immediately restores dev tracking; next update pulls `origin/main`.
- **Don't confuse with Desktop/bundle channels**: Desktop app bundles have their channel baked in the artifact tag (canary/stable). Source installs are the only ones with configurable channel.
- **Git checkout location**: `~/.hermes` is NOT a git repo. The working checkout is `~/.hermes/hermes-agent` (method: git). `git status` in `~/.hermes` fails.

## Verification

```bash
# After --set-channel
hermes update --check  # shows new channel, fetches fresh
# If channel 404, error will say "Channel object not found: releases/channels/<name>.json"
```

## References

- `references/channel-archive.md` — R2 channel wire protocol, manifest shape, build metadata format.
