# VSCodium ACP Configuration

## Settings file location

`~/.config/VSCodium/User/settings.json`

## Available extension settings

The ACP Client extension (`formulahendry.acp-client`) defines exactly 4 settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `acp.agents` | (11 default agents) | Agent configurations. Each key is agent name, value has `command`, `args`, and `env`. |
| `acp.autoApprovePermissions` | `"ask"` | How agent permission requests are handled: `"ask"` (prompt every time) or `"allowAll"` (auto-approve everything). |
| `acp.defaultWorkingDirectory` | `""` | Default working directory for agent sessions. Empty uses the current workspace folder. |
| `acp.logTraffic` | `true` | Log all ACP JSON-RPC traffic to the output channel. |

> **Tip:** Set `"acp.autoApprovePermissions": "allowAll"` for a frictionless experience — the extension will not prompt for tool call approval.

## ACP agents entry

```json
{
  "acp.agents": {
    "Hermes Agent": {
      "command": "hermes",
      "args": ["acp"],
      "env": {}
    }
  }
}
```

### ⚠️ Path pitfall: command not found

If connecting fails with `"ACP connection closed"` immediately, the editor likely cannot find `hermes` in its PATH. This happens when:

- `hermes` is installed in `~/.local/bin/`
- `~/.local/bin/` is added to PATH only in shell profiles (`.bashrc`, `.zshrc`)
- VSCodium (Electron) inherits the **system base PATH** when launched from a desktop launcher, not the shell's PATH

**Fix:** use the absolute path to `hermes`:

```json
{
  "acp.agents": {
    "Hermes Agent": {
      "command": "/home/<user>/.local/bin/hermes",
      "args": ["acp"],
      "env": {}
    }
  }
}
```

Adjust `<user>` to your actual username. After changing, **reload the VSCodium window** (`Ctrl+Shift+P` → "Developer: Reload Window") for the config to take effect.

> **Note on login-shell behavior:** The ACP Client extension spawns agents via the user's login shell (`zsh -l -c '...'` on macOS/Linux) which sources shell profiles and adds `~/.local/bin` to PATH. However, the `$SHELL` env var may not always be set correctly in the Electron environment (VSCodium), so the absolute path fix is still the most reliable approach.

## Keybinding for one-key connect

The ACP client registers these default keybindings:

| Key | Command |
|-----|---------|
| `Ctrl+Shift+A` | `acp.openChat` — Open the chat panel |
| `Escape` | `acp.cancelTurn` — Cancel current agent turn |

The `acp.connectAgent` command **accepts an agent name as a string argument**, enabling direct connection without the QuickPick menu. Override a keybinding in `~/.config/VSCodium/User/keybindings.json`:

```json
[
    {
        "key": "ctrl+shift+alt+a",
        "command": "acp.connectAgent",
        "args": "Hermes Agent"
    }
]
```

Now pressing `Ctrl+Shift+Alt+A` connects directly to Hermes Agent with no dialogs.

## Auto-connect on startup

The ACP Client extension **does not have a built-in auto-connect setting**. This was confirmed from the extension's source code (`package.json` contributes.configuration.properties) — the only settings are the 4 listed above.

**Workarounds for near-auto-connect:**
1. **Keybinding** (recommended): One keystroke to connect — set up as described above.
2. **Wrapper script** with `--command` flag:
   ```bash
   #!/bin/bash
   codium "$@" &
   sleep 3
   codium --command "acp.connectAgent"
   ```
   Note: this shows the QuickPick picker (only "Hermes Agent" as choice, press Enter). Combine with `autoApprovePermissions: "allowAll"` for instant use after selecting.
3. Combined with `autoApprovePermissions: "allowAll"`, connecting and using the agent is a single action.

## Extension

- Name: **ACP Client**
- ID: `formulahendry.acp-client`
- Available on: Open VSX Registry (default for VSCodium) and VS Code Marketplace
- The extension may also be installed by tools like OpenCode or other setup scripts automatically

## How to use

1. Open VSCodium
2. Activity Bar → ACP Client icon → Select "Hermes Agent" → Connect
3. Or Command Palette (`Ctrl+Shift+P`) → `ACP: Start Agent` → Select "Hermes Agent"

## Verification

Run `hermes acp --check` to confirm the ACP adapter is healthy before connecting from the editor.
