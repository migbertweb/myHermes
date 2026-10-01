# R2 Channel Archive Reference

## Wire Protocol

Channel objects live at `https://hermes-assets.nousresearch.com/releases/channels/<name>.json`.

### Channel Record Shape

```json
{
  "name": "stable",
  "repository": "NousResearch/hermes-agent",
  "policy": "stable-release",
  "state": "active",
  "head": {
    "buildId": "a1b2c3d4e5f6...",
    "sequence": 42,
    "manifestKey": "releases/channel-builds/a1b2c3d4e5f6.../manifest.json",
    "sha256": "..."
  },
  "delivery": {"kind": "source-branch", "branch": "main"}
}
```

### Manifest Shape

```json
{
  "request": {
    "channel": "stable",
    "commit": "<40-char-sha>",
    "sourceVersion": "0.21.5",
    "buildId": "...",
    "releaseTag": "v0.21.5",
    "identity": {"appId": "...", "version": "0.21.5", ...}
  },
  "packages": [
    {"platform": "darwin", "arch": "arm64", "variant": "bundled", ...}
  ],
  "receiverProtocol": 2
}
```

## Current Status (2026-09-26)

- `releases/channels/stable.json` → **404**
- `releases/channels/canary.json` → **404**
- `releases/channels/main.json` → **404**
- `releases/channels/preview.json` → **404**

Only branch tracking (`main` → `origin/main`) works for source installs. Release channels require the archive to be published.

## Fallback: GitHub Releases

`_published_fallback()` in `source_releases.py` scans GitHub releases as a secondary source:
- `stable` → `GET /releases/latest` (must match `STABLE_TAG_RE`)
- `canary` → scans `/releases?per_page=100&page=1..10` for canary tags

This is NOT the primary path — channel objects outrank it.

## Build Metadata Format

- **Stable tag**: `v<major>.<minor>.<patch>` (e.g., `v0.21.5`) — SemVer, major ≤ 3 digits
- **Canary tag**: `v<major>.<minor>.<patch>+canary.<YYYYMMDD>T<HHMMSS>Z` (e.g., `v0.21.5+canary.20260926T120000Z`)

See `hermes_cli/update_channel.py`: `STABLE_TAG_RE`, `_CANARY_TAG_RE` for the exact regexes.
