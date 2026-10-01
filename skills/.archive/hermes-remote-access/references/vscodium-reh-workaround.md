# VSCodium Remote SSH — REH Installation Workaround

## Problem

The `open-remote-ssh-for-trae` extension (v0.0.4 and similar) generates malformed
download URLs for the VSCodium REH (Remote Extension Host). The URL template
`${version}.${release}` produces `1.121.0.` instead of `1.121.03429` when
`DISTRO_VSCODIUM_RELEASE` is empty, resulting in a 404.

Error in logs:
```
https://github.com/VSCodium/vscodium/releases/download/1.121.0./vscodium-reh-linux-x64-1.121.0..tar.gz
Error downloading server from ... 404 Not Found
```

## Solution

Pre-install the REH manually on the server at the path the extension expects.

### Steps

1. From the VSCodium Remote SSH logs, find `DISTRO_COMMIT` (e.g. `824c4c46...`).

2. Check the latest VSCodium release tag:
   ```bash
   curl -sL https://api.github.com/repos/VSCodium/vscodium/releases/latest | \
     python3 -c "import json,sys; print(json.load(sys.stdin)['tag_name'])"
   ```

3. Install manually:
   ```bash
   COMMIT="<distro-commit>"
   TAG="<latest-tag>"  # e.g. 1.121.03429
   mkdir -p ~/.vscodium-server/bin/$COMMIT
   cd ~/.vscodium-server/bin/$COMMIT
   curl -L -o vscode-server.tar.gz \
     "https://github.com/VSCodium/vscodium/releases/download/${TAG}/vscodium-reh-linux-x64-${TAG}.tar.gz"
   tar -xf vscode-server.tar.gz --strip-components 1
   rm vscode-server.tar.gz
   ```

4. Reconnect in VSCodium — the extension finds the server installed and skips
   the download.

## Notes

- The commit hash `824c4c46a288b839f13b24022655329c2aeb9f81` corresponds to
  VSCodium server v1.121.03429.
- The server install path is `~/.vscodium-server/bin/<COMMIT>/bin/codium-server`.
- VSCodium's template also renames `codium` → `trae` in executable names, but
  the `SERVER_APP_NAME` check uses `codium-server`, so the original names work.
