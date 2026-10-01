#!/usr/bin/env bash
# hermes-desktop-safe — launch Hermes Desktop guaranteeing node-pty (pty.node) is
# compiled for the current Electron ABI. If missing or the ABI changed, runs the
# native rebuild + repackage (the steps in hermes-desktop-maintenance SKILL.md);
# otherwise launches the packaged app directly (fast, no recompile).
#
# Drop in ~/.local/bin, chmod +x, and alias:  hdesk='hermes-desktop-safe'
set -euo pipefail

REPO="$HOME/.hermes/hermes-agent"
DESKTOP="$REPO/apps/desktop"
BIN="$DESKTOP/release/linux-unpacked/Hermes"

electron_ver=$(node -p "require('$REPO/node_modules/electron/package.json').version" 2>/dev/null || echo "")
abi_stamp="$DESKTOP/.native_abi_stamp"

needs_build=0
if [ ! -x "$BIN" ]; then
  needs_build=1
elif ! find "$DESKTOP/release" -name 'pty.node' -path '*build/Release*' | grep -q .; then
  needs_build=1
elif [ -n "$electron_ver" ] && { [ ! -f "$abi_stamp" ] || [ "$(cat "$abi_stamp" 2>/dev/null)" != "$electron_ver" ]; }; then
  needs_build=1
fi

if [ "$needs_build" -eq 1 ]; then
  echo "-> node-pty native missing or Electron ABI changed (electron=$electron_ver). Native rebuild..."
  cd "$DESKTOP"
  PATH="$REPO/node_modules/.bin:$PATH" \
    electron-rebuild -w node-pty --only node-pty --build-from-source -f
  npm run build
  PATH="$REPO/node_modules/.bin:$PATH" \
    NODE_OPTIONS=--max-old-space-size=16384 \
    node scripts/run-electron-builder.mjs --dir
  printf '%s' "$electron_ver" > "$abi_stamp"
  echo "OK: node-pty compiled for electron=$electron_ver"
fi

cd "$DESKTOP"
exec "$BIN" "$@"
