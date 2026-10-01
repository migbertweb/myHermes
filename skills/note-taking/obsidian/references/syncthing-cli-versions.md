# Syncthing CLI — v1.x vs v2.x Differences

## Config location

| Version | Config path |
|---------|-------------|
| v1.x (Ubuntu package, manual install) | `~/.config/syncthing/config.xml` |
| v2.x (Arch Linux, CachyOS package) | `~/.local/state/syncthing/config.xml` |

## CLI commands comparison

### Add a folder to the config

**v1.x:**
```bash
syncthing cli config folders add --id my-vault --label "My Vault" --path /home/user/vaults/principal
```

**v2.x:**
```bash
# Same syntax — but folder IDs are case-sensitive and must match on both sides
syncthing cli config folders add --id my-vault --label "My Vault" --path /home/user/vaults/principal
```

> Note: If the server pushes a folder to the laptop (via auto-accept or announcement), the folder may already exist with an incorrect path. In v2.x, the path defaults to the label name.

### Add a device to a folder

**v1.x:**
```bash
syncthing cli config folders my-vault devices add --device-id=DEVICE_ID
```

**v2.x:**
```bash
syncthing cli config folders my-vault devices add --device-id=DEVICE_ID
```

### Set the folder path (after incorrect auto-config)

**v1.x:** also positional
**v2.x:** positional arg
```bash
syncthing cli config folders my-vault path set "/home/user/vaults/principal"
```
> No `--set` flag — just pass the path as the argument after `set`.

### List folders

**Both versions:**
```bash
syncthing cli config folders list
```

### Dump folder config as JSON

**Both versions:**
```bash
syncthing cli config folders my-vault dump-json
```

### Override folder (accept remote state)

**v2.x only:**
```bash
syncthing cli operations folder-override
```
> v1.x doesn't support this via CLI — use REST API instead.

## REST API (works on both)

The API is identical between versions:

```bash
# Get API key
# v1.x path:
APIKEY=*** -oP 'apikey="\K[^"]+' ~/.config/syncthing/config.xml)
# v2.x path:
APIKEY=*** -oP 'apikey="\K[^"]+' ~/.local/state/syncthing/config.xml)

# Rescan
curl -s -X POST -H "X-API-Key: $APIKEY" "http://127.0.0.1:8384/rest/db/scan?folder=FOLDER_ID"

# Status
curl -s -H "X-API-Key: $APIKEY" "http://127.0.0.1:8384/rest/db/status?folder=FOLDER_ID"

# Override
curl -s -X POST -H "X-API-Key: $APIKEY" "http://127.0.0.1:8384/rest/db/override?folder=FOLDER_ID"
```

## Key differences at a glance

| Feature | v1.x | v2.x |
|---------|------|------|
| Config path | `~/.config/syncthing/` | `~/.local/state/syncthing/` |
| `operations rescan` CLI | ✅ yes | ❌ no (use REST API) |
| `folder-override` CLI | ❌ no (use REST API) | ✅ yes |
| `--gui-address` flag | ✅ yes | ✅ yes |
