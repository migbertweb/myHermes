#!/usr/bin/env bash
set -euo pipefail

LABEL="${MNEMOSYNE_DASHBOARD_LAUNCHD_LABEL:-io.mnemosyne.dashboard}"
HOST="${MNEMOSYNE_DASHBOARD_HOST:-127.0.0.1}"
PORT="${MNEMOSYNE_DASHBOARD_PORT:-8765}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PLUGIN_DIR="${MNEMOSYNE_DASHBOARD_PLUGIN_DIR:-$HERMES_HOME/plugins/mnemosyne-dashboard}"
PYTHON_BIN="${MNEMOSYNE_DASHBOARD_PYTHON:-$HERMES_HOME/hermes-agent/venv/bin/python}"
DATA_DIR="${MNEMOSYNE_DASHBOARD_DATA_DIR:-$HERMES_HOME/plugin-data/mnemosyne-dashboard}"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This installer is for macOS launchd only." >&2
  exit 1
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python not found or not executable: $PYTHON_BIN" >&2
  exit 1
fi

if [[ ! -f "$PLUGIN_DIR/server.py" ]]; then
  echo "Mnemosyne dashboard server.py not found under: $PLUGIN_DIR" >&2
  exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$DATA_DIR"

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array>
    <string>$PYTHON_BIN</string>
    <string>$PLUGIN_DIR/server.py</string>
    <string>--host</string><string>$HOST</string>
    <string>--port</string><string>$PORT</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$DATA_DIR/launchd.out.log</string>
  <key>StandardErrorPath</key><string>$DATA_DIR/launchd.err.log</string>
  <key>WorkingDirectory</key><string>$PLUGIN_DIR</string>
</dict></plist>
PLIST

launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

echo "Installed and started $LABEL"
echo "Plist: $PLIST"
echo "URL: http://$HOST:$PORT/"
echo "Status: launchctl print gui/$(id -u)/$LABEL"
