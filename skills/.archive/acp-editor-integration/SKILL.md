---
name: acp-editor-integration
description: "Set up and troubleshoot Hermes Agent as an ACP (Agent Client Protocol) server for editor integration — VS Code, VSCodium, Zed, and JetBrains IDEs."
version: 1.0.0
author: Viernes
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [acp, editor, ide, vscode, vscodium, zed, jetbrains, integration]
    related_skills: [hermes-agent]
---

# ACP Editor Integration

Hermes Agent can run as an **ACP (Agent Client Protocol) server**, letting ACP-compatible editors talk to Hermes over stdio and render chat messages, tool activity, file diffs, terminal commands, approval prompts, and streamed thinking/response chunks.

## When to use this skill

Use this skill when:
- Setting up Hermes Agent in an editor (VS Code, VSCodium, Zed, JetBrains) for the first time
- The user ran `hermes acp` standalone and got "server closed" or similar
- Troubleshooting ACP connection failures between Hermes and an editor
- Configuring custom ACP agent entries in editor settings
- The user asks about auto-connecting ACP on editor startup, keybindings for fast connect, or extension settings
- Investigating extension source code (checking for hidden settings, spawn behavior, command arguments)

## Prerequisites

1. Hermes Agent installed with the ACP extra (`agent-client-protocol` dependency)
2. An ACP-compatible editor with an ACP client extension/plugin

## Architecture

```
Editor (VS Code / VSCodium / Zed)
    │  spawns `hermes acp` as subprocess
    │  communicates over stdio via JSON-RPC (ACP)
    ▼
Hermes ACP server  ──►  Hermes tools (file, terminal, web, etc.)
    │
    └── ACP session manager (in-memory)
    └── Normal Hermes config (~/.hermes/config.yaml, ~/.hermes/.env)
```

**Key fact:** `hermes acp` is a **stdio server** — it is meant to be spawned as a subprocess by an editor, not run standalone in a terminal. Running it alone will show errors or appear to "close" because no ACP client is connected.

## Setup Steps

### 1. Install ACP dependency

If not already installed:
```bash
# From the Hermes source directory:
pip install -e '.[acp]'

# Or directly:
pip install 'agent-client-protocol==0.9.0'
```

Verify with:
```bash
hermes acp --check
# Expected: "Hermes ACP check OK"
hermes acp --version
```

### 2. Install editor ACP client

| Editor | Extension | Where to get it |
|--------|-----------|-----------------|
| **VS Code / VSCodium** | `formulahendry.acp-client` | VS Code Marketplace or Open VSX |
| **Zed** | Built-in ACP agent support | Zed v0.221.x+ via ACP Registry |
| **JetBrains** | ACP-compatible plugin | JetBrains Marketplace |

### 3. Configure the agent entry

**VS Code / VSCodium** — add to `settings.json`:

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

VSCodium path: `~/.config/VSCodium/User/settings.json`
VS Code path: `~/.config/Code/User/settings.json`

> **⚠️ Path warning:** If `hermes` is in `~/.local/bin/`, VSCodium may not find it when launched from a desktop launcher (the Electron process inherits the system base PATH, not the shell's extended PATH). This causes `"ACP connection closed"` immediately on connect. Fix: use the absolute path — `"command": "/home/<user>/.local/bin/hermes"`. See `references/vscodium-config.md` for details.
>
> **Login-shell nuance:** The extension spawns agents via the user's login shell (`zsh -l -c '...'` on macOS/Linux) which sources shell profiles, making `~/.local/bin` accessible. However, `$SHELL` is not always set in the Electron context (VSCodium launched from desktop), so the absolute path is still the more reliable fix.

### **Recommended settings for smoother use**

Add these alongside the agent config:

```json
{
  "acp.autoApprovePermissions": "allowAll",
  "acp.defaultWorkingDirectory": "",
  "acp.logTraffic": true
}
```

- `allowAll` — skips the approval prompt for every tool call
- `logTraffic` — set to `false` if the ACP Traffic output channel is too noisy

**The extension has exactly these 4 settings** — `agents`, `autoApprovePermissions`, `defaultWorkingDirectory`, `logTraffic`. No auto-connect or other hidden settings exist (confirmed from source code at `src/config/AgentConfig.ts` and `package.json`).

### **Keybinding for one-key connect**

The `acp.connectAgent` command accepts a string argument (agent name). Add to `keybindings.json`:

```json
[
    {
        "key": "ctrl+shift+alt+a",
        "command": "acp.connectAgent",
        "args": "Hermes Agent"
    }
]
```

Now pressing `Ctrl+Shift+Alt+A` connects directly without the QuickPick menu.

**Zed** — add to Zed settings:

```json
{
  "agent_servers": {
    "hermes-agent": {
      "type": "custom",
      "command": "hermes",
      "args": ["acp"]
    }
  }
}
```

Or use the ACP Registry: open the Agent Panel → Add Agent → Search for "Hermes Agent". Requires `uv` on PATH.

**JetBrains** — point an ACP-compatible plugin at `/path/to/hermes-agent/acp_registry`

### 4. Connect

**VS Code / VSCodium:**
1. Open the **ACP Client** panel from the Activity Bar (left sidebar)
2. Select **"Hermes Agent"** from the agent list
3. Click **Connect** (or the start button)
4. Start chatting in the panel

**Quick connect (if keybinding set up):** Press `Ctrl+Shift+Alt+A` (or whichever key you configured) — connects directly without the agent picker.

Alternatively: Command Palette (`Ctrl+Shift+P`) → `ACP: Start Agent` → select "Hermes Agent"

**Zed:**
1. Open the Agent Panel
2. Click "Add Agent" or run `zed: acp registry`
3. Search for and install "Hermes Agent"
4. Start a new Hermes external-agent thread

## Common Pitfalls

### "ACP server closed" when running `hermes acp` standalone

This is **expected behavior**. The ACP server is a stdio protocol server — it only works when an editor spawns it as a subprocess. Running it alone in a terminal shows no client connected, and the server exits (or shows a `PermissionError` on stdin).

**Fix:** Don't run it standalone. Follow step 4 (above) to launch it from your editor's ACP Client panel.

### "ACP connection closed" when connecting from editor

If the error appears immediately (not after a delay), the editor cannot spawn or find `hermes`. See the **Path pitfall** warning in section 3 and `references/vscodium-config.md`.

If the error appears after a longer delay, check provider credentials with `hermes doctor` and `hermes model`.

### No auto-connect on startup

The ACP Client extension does **not** have a "connect on startup" setting (confirmed from source code — only 4 settings exist). If the user asks for this:

1. **Check if they really need it** — with `autoApprovePermissions: allowAll` + a keybinding, connecting is one keystroke away.
2. **If they insist**, the best available workaround is a wrapper script that launches VSCodium then sends `codium --command "acp.connectAgent"` after a short delay. Note this still shows the QuickPick (user presses Enter) unless combined with a custom keybinding that passes the agent name as argument.
3. Do NOT waste time looking for a hidden config setting or suggesting custom extensions — the absence was confirmed in the package.json and extension source.

### PermissionError on stdin

When running `hermes acp` inside certain environments (e.g., inside another agent's terminal tool), stdin may not be available as an async reader. This is an environment limitation, not a Hermes bug.

**Fix:** Run from a real terminal or let the editor spawn the process.

### Extension not finding Hermes

If the ACP Client extension can't find or launch `hermes`:
1. Verify `hermes` is on your `PATH`
2. Try the full path in the command: `"command": "/home/user/.local/bin/hermes"`
3. Run `hermes acp --check` to confirm the ACP adapter is healthy
4. Restart the editor after making config changes

### Agent shows in editor but no response

Check provider credentials:
```bash
hermes doctor
hermes model
```

ACP mode uses the same config as CLI — `~/.hermes/.env` and `~/.hermes/config.yaml`.

## Configuration and credentials

ACP mode inherits all Hermes configuration from:
- `~/.hermes/config.yaml` — settings
- `~/.hermes/.env` — API keys
- `~/.hermes/skills/` — skills
- `~/.hermes/state.db` — sessions

Provider resolution uses Hermes' normal runtime resolver. Configure with:
```bash
hermes model
```

## Session behavior

ACP sessions are tracked in-memory while the server runs. Each session stores:
- Session ID
- Working directory (bound to the editor's cwd for file/terminal tools)
- Selected model
- Conversation history
- Cancel event

Working directory is bound to the editor's project root, so file and terminal tools run relative to the workspace, not the server process cwd.

## Approval prompts

ACP has simpler approval options than the CLI:
- **Allow once** — this single tool call
- **Allow for session** — all matching calls in this ACP session (resets when editor restarts)
- **Allow always** — permanent allowlist entry (survives restarts)
- **Deny** — reject this call

## References

See `references/` directory in this skill for editor-specific setup details.
