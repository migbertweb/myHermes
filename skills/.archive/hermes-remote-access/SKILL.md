---
name: hermes-remote-access
description: Set up a centralized Hermes Agent on a server and connect from a laptop/workstation via SSH, the API Server, editors (VS Code, VSCodium, Zed, JetBrains), or custom chat UIs.
version: 2.0.0
author: Viernes
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [hermes, remote, ssh, vscode, vscodium, acp, tunnel, centralized, syncthing]
---

# Remote Hermes Access

Connect a laptop/workstation to a centralized Hermes Agent running on a home server. Three approaches, which can be combined:

1. **Remote SSH** — VS Code/VSCodium Remote SSH extension. The Hermes extension runs server-side.
2. **ACP TCP Bridge** — Direct TCP connection via socat. No Remote SSH needed; the extension runs locally and connects to a server-side `hermes acp` instance over TCP.
3. **Syncthing `.hermes` sync** — (Companion to either approach above) Keep config, skills, memory in sync across machines so every device shares the same knowledge.

## Architecture

```
┌──────────────────────┐      SSH / TCP       ┌──────────────────────┐
│   Laptop / Client     │ ◄──────────────────► │   Server (Homeserver)  │
│  ┌─────────────────┐  │                     │  ┌─────────────────┐   │
│  │ VSCodium/VS Code │  │                     │  │  hermes acp (stdio)   │   │
│  │  └─ Hermes Ext   │  │                     │  │  (via Python bridge)│   │
│  │  └─ Remote SSH   │  │                     │  └─────────────────┘   │
│  └─────────────────┘  │                     │  ┌─────────────────┐   │
│  ┌─────────────────┐  │                     │  │  hermes gateway  │   │
│  │ hermes-remote-   │  │                     │  │  (Telegram etc)  │   │
│  │ proxy.py (TCP)   │  │                     │  └─────────────────┘   │
│  └─────────────────┘  │                     └──────────────────────┘
└──────────────────────┘
```

## 1. Prerequisites

- Hermes Agent installed on the server (`hermes setup` done)
- SSH server running on both machines
- Local network connectivity (or VPN/WireGuard for WAN)

## 2. Bidirectional SSH Setup

### A. Laptop → Server

```bash
# On laptop — generate key if needed
ssh-keygen -t ed25519
ssh-copy-id piro@server-ip
# Test
ssh piro@server-ip
```

### B. Server → Laptop

```bash
# On server — generate key
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "hermes@server"
# Show public key for laptop
cat ~/.ssh/id_ed25519.pub
```

On laptop, add that public key to `~/.ssh/authorized_keys`.

```bash
# On laptop — only allow server IP
sudo ufw allow from 192.168.1.8 to any port 22 proto tcp
```

Test:
```bash
ssh user@laptop-ip "echo OK"
```

## 3. VSCodium Remote SSH (with manual REH install)

VSCodium's `open-remote-ssh-for-trae` extension has a bug: it generates download URLs with a trailing dot before the tarball extension (e.g. `1.121.0.` instead of `1.121.03429`). Workaround: pre-install the REH manually on the server.

### Find correct release

```bash
curl -sL https://api.github.com/repos/VSCodium/vscodium/releases/latest | \
  python3 -c "import json,sys; print(json.load(sys.stdin)['tag_name'])"
```

### Find the commit hash the extension expects

Look in the extension's install script output (visible in VSCodium's Remote SSH logs when connection fails) for `DISTRO_COMMIT`.

### Install manually

```bash
COMMIT="<commit-from-extension>"
RELEASE_TAG="<latest-release-tag>"
mkdir -p ~/.vscodium-server/bin/$COMMIT
cd ~/.vscodium-server/bin/$COMMIT
curl -L -o vscode-server.tar.gz \
  "https://github.com/VSCodium/vscodium/releases/download/${RELEASE_TAG}/vscodium-reh-linux-\$(uname -m | sed 's/x86_64/x64/;s/aarch64/arm64/')-${RELEASE_TAG}.tar.gz"
tar -xf vscode-server.tar.gz --strip-components 1
rm vscode-server.tar.gz
```

Then reconnect — the extension finds the server already installed and skips the download.

## 4. ACP TCP Bridge (Direct connection, no Remote SSH)

Expose `hermes acp` over TCP so local editors can connect without SSH.

**Architecture:**

```
┌─ Laptop ─────────────────────────┐     TCP :8000     ┌─ Server ─────────────────────┐
│ VSCodium/VS Code                  │ ◄──────────────► │ python3 hermes-acp-bridge.py  │
│  └─ Hermes extension              │                  │  └─ asyncio TCP server         │
│       └─ hermes.path ↓            │                  │       └─ spawn per-connection  │
│            ~/hermes-remote-proxy.py│                  │            hermes acp (stdio)  │
└───────────────────────────────────┘                  └──────────────────────────────┘
```

### ⚠️ CRITICAL: Do NOT use socat or pty

`socat` with the `pty` option corrupts the ACP JSON-RPC protocol because a pseudo-terminal changes byte sequences (adds carriage returns, translates control characters). You will get `ACP error -32603: Unhandled client method: session/new` or similar framing errors.

The correct approach is a Python asyncio TCP server that spawns `hermes acp` with **raw pipes** (`asyncio.create_subprocess_exec` with `stdin=PIPE, stdout=PIPE`) and bridges TCP ↔ subprocess bidirectionally.

### Server side — Python ACP bridge

Create `~/.hermes/hermes-acp-bridge.py` (also available as `scripts/hermes-acp-bridge.py` in this skill — use that version; it supports `HERMES_ACP_BIND`/`HERMES_ACP_PORT` env vars):

```python
#!/usr/bin/env python3
"""Bridge TCP connections to hermes acp subprocess.

Connects TCP clients to a local hermes acp process via clean stdio
(pipes, no PTY), preserving the ACP JSON-RPC protocol intact."""

import asyncio, logging, os, shutil, sys

HERMES_ACP = shutil.which("hermes") or "/home/piro/.local/bin/hermes"
BIND_ADDRESS = "192.168.1.8"
BIND_PORT = 8000

logging.basicConfig(level=logging.INFO, stream=sys.stderr)

async def bridge(reader, writer):
    peername = writer.get_extra_info("peername")
    logging.info("New connection from %s", peername)

    proc = await asyncio.create_subprocess_exec(
        HERMES_ACP, "acp",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def tcp_to_proc():
        try:
            while True:
                data = await reader.read(65536)
                if not data: break
                proc.stdin.write(data)
                await proc.stdin.drain()
        except (ConnectionResetError, BrokenPipeError): pass
        finally:
            try: proc.stdin.close()
            except: pass

    async def proc_to_tcp():
        try:
            while True:
                data = await proc.stdout.read(65536)
                if not data: break
                writer.write(data)
                await writer.drain()
        except (ConnectionResetError, BrokenPipeError): pass
        finally:
            try: writer.close()
            except: pass

    async def log_stderr():
        while True:
            line = await proc.stderr.readline()
            if not line: break
            logging.info("[acp:%s] %s", peername, line.decode(errors="replace").rstrip())

    tasks = [asyncio.create_task(tcp_to_proc()),
             asyncio.create_task(proc_to_tcp()),
             asyncio.create_task(log_stderr())]
    try:
        await asyncio.gather(*tasks)
    except: pass
    finally:
        for t in tasks: t.cancel()
        try: proc.kill()
        except: pass
        try: writer.close()
        except: pass
        logging.info("Connection from %s closed", peername)

async def main():
    tcp_server = await asyncio.start_server(bridge, host=BIND_ADDRESS, port=BIND_PORT)
    logging.info("ACP bridge listening on %s:%s", BIND_ADDRESS, BIND_PORT)
    async with tcp_server:
        await tcp_server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
```

### Server side — systemd service

Create `/etc/systemd/system/hermes-acp-bridge.service` (requires sudo):

```ini
[Unit]
Description=Hermes ACP TCP Bridge — Remote editor support
After=network.target

[Service]
Type=simple
User=piro
ExecStart=/usr/bin/python3 /home/piro/.hermes/hermes-acp-bridge.py
# Optional: customize bind address/port (defaults: 192.168.1.8:8000)
# Environment=HERMES_ACP_BIND=0.0.0.0
# Environment=HERMES_ACP_PORT=8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

The bridge script reads `HERMES_ACP_BIND` and `HERMES_ACP_PORT` from the environment — set them via `Environment=` in the `[Service]` block to override defaults without editing the script.

Enable and start:

```bash
sudo systemctl enable --now hermes-acp-bridge.service
```

Verify it's listening:

```bash
ss -tlnp | grep 8000
# Expected: LISTEN 0 100 192.168.1.8:8000 0.0.0.0:* users:((...,"hermes-acp-bridge",...))
```

**Firewall note:** No firewall change needed if the server doesn't have one. The port is bound to the server's LAN IP, so only LAN devices can reach it.

### Laptop side — proxy script

Create `~/hermes-remote-proxy.py` (available as `scripts/hermes-remote-proxy.py` in this skill — supports `HERMES_SERVER_HOST`/`HERMES_SERVER_PORT` env vars):

```python
#!/usr/bin/env python3
"""Hermes ACP Remote Proxy — forwards stdio ↔ TCP to server."""
import socket, sys, select, os

SERVER_HOST = '192.168.1.8'
SERVER_PORT = 8000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10)
try:
    sock.connect((SERVER_HOST, SERVER_PORT))
except Exception as e:
    print(f"Error connecting: {e}", file=sys.stderr)
    sys.exit(1)
sock.settimeout(None)

poll = select.poll()
poll.register(sys.stdin, select.POLLIN)
poll.register(sock, select.POLLIN)

try:
    while True:
        for fd, event in poll.poll(500):
            if event & select.POLLIN:
                if fd == sys.stdin.fileno():
                    data = os.read(sys.stdin.fileno(), 65536)
                    if not data: raise SystemExit
                    sock.sendall(data)
                elif fd == sock.fileno():
                    data = sock.recv(65536)
                    if not data: raise SystemExit
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
            elif event & (select.POLLHUP | select.POLLERR | select.POLLNVAL):
                raise SystemExit
except (BrokenPipeError, ConnectionError, SystemExit):
    pass
finally:
    sock.close()
```

Make executable: `chmod +x ~/hermes-remote-proxy.py`

### Configure VS Code/VSCodium extension

Set `hermes.path` to the proxy script path:

```json
"hermes.path": "/home/migbert/hermes-remote-proxy.py"
```

The extension spawns the proxy, which connects to the server's ACP bridge transparently.

## Related References

- `references/api-server-setup.md` — activación y troubleshooting del API Server de Hermes (OpenAI-compatible, puerto 8642)

## Verification

- **SSH:** `ssh user@host "echo OK"`
- **ACP bridge:** `echo '{"jsonrpc":"2.0","method":"ping","id":1}' | nc server-ip 8000`
- **Editor:** Open Hermes panel, send a test message

### 5.1 Gateway (Telegram) Verification

When the user asks "is Telegram connected?" or reports sending a message that hasn't arrived, follow this diagnostic chain:

**A. Check gateway service status**

SSH to the server and check the systemd user service:

```bash
ssh piro@server-ip "systemctl --user status hermes-gateway"
```

Key indicators:
- `Active: active (running)` — service is alive
- `Active: inactive/dead` — start with `systemctl --user start hermes-gateway`

**B. Verify bot token is valid**

Use Telegram's `getMe` endpoint directly from the server:

```bash
ssh piro@server-ip 'TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2-); curl -s --connect-timeout 10 "https://api.telegram.org/bot${TOKEN}/getMe"'
```

Expected response: `{"ok":true,"result":{"id":...,"is_bot":true,"first_name":"...","username":"..."}}`
- `404 Not Found` → bad token (check `.env` format, no whitespace around `=`)
- Connection timeout → server cannot reach `api.telegram.org` (check DNS/firewall)

**C. Check gateway logs for errors**

```bash
ssh piro@server-ip "journalctl --user -u hermes-gateway --since '1 hour ago' --no-pager"
```

What to look for:
- `NetworkError: httpx.ConnectError` — transient network blip; usually self-heals with fallback IPs
- `WARNING gateway.platforms.telegram_network` — common; the gateway tries fallback IPs automatically
- A single warning with no repeats → transient, ignore
- Repeating errors every polling cycle → real connectivity problem

**D. Verify message delivery**

The gateway consumes Telegram updates via long polling, so `getUpdates` will return `[]` even after successful message receipt. Instead, check the sessions database:

```bash
ssh piro@server-ip "python3 -m json.tool ~/.hermes/sessions/sessions.json"
```

Look for a session with `"platform": "telegram"` and a recent `"updated_at"` timestamp. The `origin.message_id` field shows the last processed message ID.

**E. Check channel directory freshness**

```bash
ssh piro@server-ip "cat ~/.hermes/channel_directory.json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(\"Updated:\", d[\"updated_at\"]); print(\"Telegram channels:\", len(d[\"platforms\"][\"telegram\"]))'"
```

A recent `updated_at` timestamp confirms the gateway is alive and updating its state.

**F. Understand session isolation**

When the agent is in a CLI session (laptop) and a Telegram message arrives, the gateway starts a **separate session on the server** — it does NOT route into the active CLI conversation. This is expected behavior:

```
Telegram message ──► gateway (server) ──► new server session
CLI chat (laptop) ─────────────────────► different session (here)
```

To see messages from both channels in one place, either:
- Use only one channel at a time
- Install the gateway on the same machine as the active CLI session

## 6. API Server — OpenAI-Compatible HTTP Endpoint

An alternative to ACP/SSH: expose Hermes via the Gateway's built-in API Server adapter. Any OpenAI-compatible chat UI (custom plugins, curl scripts, third-party apps) can use Hermes as a backend provider.

### ⚠️ Critical: gateway ≠ API server

The gateway process (`hermes gateway run`) connects to messaging platforms (Telegram, Discord, etc.) as a client — it **does NOT** expose an HTTP API endpoint for local tools by default. The API Server is a **separate, opt-in feature** inside the gateway that must be explicitly enabled via env vars. Without `API_SERVER_ENABLED=true`, the gateway will **not** listen on any HTTP port even though it's running.

### Enable the API Server

```bash
# Enable in ~/.hermes/.env
API_SERVER_ENABLED=true
API_SERVER_HOST=127.0.0.1       # use 0.0.0.0 or LAN IP for remote clients
# API_SERVER_PORT=8642          # default is 8642 — uncomment to override
API_SERVER_KEY=$(python3 -c "import secrets; print(secrets.token_hex(16))")
API_SERVER_MODEL_NAME=hermes-agent
```

After adding these, restart the gateway:
```bash
systemctl --user restart hermes-gateway
```

⚠️ **Known issue: gateway may hang on restart.** The old process can get stuck in `deactivating (stop-sigterm)` state for 60+ seconds. If `systemctl --user restart` times out, kill it forcefully and start again:

```bash
systemctl --user kill -s SIGKILL hermes-gateway
systemctl --user start hermes-gateway
```

Verify it's listening:
```bash
ss -tlnp | grep 8642
curl -s http://127.0.0.1:8642/v1/models | head -200
```

### DMS Plugin Client Configuration

When using a DMS desktop plugin (e.g. `dms-ai-assistant-Hermes`) as the client to a remote API Server:

1. **Set the endpoint in plugin settings:**
   - Provider: `custom` (OpenAI-compatible)
   - Base URL: `http://<server-ip>:8642` (e.g. `http://192.168.1.8:8642`)
   - API Key: your `API_SERVER_KEY`

2. **Patch the plugin's `checkHermesMode()` function** to recognise the server IP so it enters "Hermes Mode" (displays model info, session tracking, token metrics). Edit `AIAssistantService.qml`:

   ```javascript
   // Before (localhost-only):
   isHermesMode = p === "custom" && (url.includes("127.0.0.1:8420") || url.includes("localhost:8420") || url.includes("hermes"));

   // After (also matches server IP + default API port):
   isHermesMode = p === "custom" && (url.includes("127.0.0.1:8420") || url.includes("localhost:8420") || url.includes("192.168.1.8:8642") || url.includes("hermes"));
   ```

3. **Optional: suppress privacy warning for LAN IP.** The plugin shows "Remote provider: avoid sensitive data" for any non-localhost URL. Edit `AIAssistant.qml` to recognise your server's IP as local:

   ```javascript
   // Before:
   const isRemote = !localCapable || (!baseUrl.includes("localhost") && !baseUrl.includes("127.0.0.1"))

   // After (adds server LAN IP exception):
   const isRemote = !localCapable || (!baseUrl.includes("localhost") && !baseUrl.includes("127.0.0.1") && !baseUrl.includes("192.168.1.8"))
   ```

4. **Apply changes:** `dms restart` to pick up modified QML files.

### Fallback: Direct LLM Provider

If the API Server is not available or you prefer a simpler setup, the DMS plugin supports LLM providers **directly** — no Hermes required:

- **Gemini** — uses `GOOGLE_API_KEY`, select "Gemini" provider in plugin settings
- **OpenCode Zen** — select "Custom" with Base URL `https://opencode.ai/zen/v1` and your API key
- **Ollama** — select "Ollama" provider for local models

This bypasses Hermes entirely and is often more reliable for desktop widgets.

Full API Server details in `references/api-server-setup.md` — covers response format, streaming, session tracking, metadata badges, and pitfalls.

### API Server pitfalls

- **Missing `aiohttp`**: The API Server adapter requires `aiohttp` in the Hermes venv. If the gateway logs show `WARNING gateway.run: API Server: aiohttp not installed`, install it:
  ```bash
  uv pip install aiohttp --python ~/.hermes/hermes-agent/venv/bin/python
  ```
- **Missing `idna`**: The gateway's Telegram platform depends on `httpx` which needs `idna`. If the gateway crashes with `ModuleNotFoundError: No module named 'idna'`:
  ```bash
  uv pip install idna --python ~/.hermes/hermes-agent/venv/bin/python
  ```
- **Gateway timeouts on restart**: The old process may refuse to exit cleanly (stuck `deactivating (stop-sigterm)`). Use `systemctl --user kill -s SIGKILL hermes-gateway` then start again. This also triggers a systemd auto-restart cycle — just wait 5-10s after the kill.

## 7. Syncing `.hermes` Across Machines with Syncthing

When running Hermes on multiple machines, you typically want **two independent instances** that share credentials, skills, and cron jobs — but each with its own personality (`config.yaml`), session history (`state.db`), and memory (`memory_store.db`).

**Syncthing** (peer-to-peer file sync) keeps `~/.hermes/` in sync over LAN — while excluding machine-local data that must stay per-machine.

This pattern works for any multi-instance setup:
- **Server (24/7)**: always-on gateway, simple tasks, background jobs
- **Laptop (dev workstation)**: interactive sessions, heavy development, custom config

Each has its own `.env` (API keys stay per-machine — `.env` is excluded from sync on both sides), `config.yaml`, sessions, and memory. Shared across machines: `secrets.yaml`, `skills/`, `cron/`, `auth/`.

See `references/syncthing-hermes-sync.md` for the full setup: static binary install, systemd user service, device pairing, and the exact `.stignore` exclusion patterns.

> **Quick pitfall:** After manually editing Syncthing's `config.xml` to add a new device or folder, run `systemctl --user restart syncthing.service` on the server. Syncthing does NOT auto-reload device/folder additions — it will reject the laptop connection with "unknown device" until restarted.

## 8. Removing a Client Hermes Install (Transitioning to Centralized)

When moving from a client-local Hermes setup to a centralized server-only setup, **do not just `rm -rf ~/.hermes`** — the `.hermes/` directory is likely synced with the server via Syncthing, and deleting it on the client would replicate the deletion.

### Safe removal procedure

Run these commands **on the client machine** (or via SSH):

```bash
# 1. Stop and disable all Hermes systemd services
systemctl --user stop hermes-gateway.service hermes-tunnel.service 2>/dev/null || true
systemctl --user disable hermes-gateway.service hermes-tunnel.service 2>/dev/null || true

# 2. Remove systemd unit files
rm -f ~/.config/systemd/user/hermes-gateway.service
rm -f ~/.config/systemd/user/hermes-tunnel.service
systemctl --user daemon-reload

# 3. Remove the binary
rm -f ~/.local/bin/hermes

# 4. Remove the local agent code (excluded from Syncthing via .stignore)
rm -rf ~/.hermes/hermes-agent/

# 5. ⚠️ LEAVE ~/.hermes/ INTACT — it's Syncthing-synced with the server
#    Removing it would replicate the deletion server-side
```

### After removal

- **DMS/desktop plugins** that pointed to `127.0.0.1:8420` (local Gateway) must be reconfigured to point to the **server's Gateway** IP (e.g. `192.168.1.8:8420`). See `dms-plugin-development` skill for guidance.
- **SSH alias** on the client: `alias hermes='ssh user@server hermes'` to use the server's Hermes from the client terminal.
- The residual `hermes-gateway.service` showing `not-found failed failed` in `systemctl --user list-units` is a stale systemd cache entry — harmless, clears on next logout/reboot.

## Pitfalls

- **VSCodium REH URL bug:** The `open-remote-ssh-for-trae` extension generates malformed download URLs (`1.121.0.` instead of `1.121.03429`). Manual REH install is the fix. See `references/vscodium-reh-workaround.md`.
- **socat + pty corrupts ACP:** Never use `socat EXEC:"...",pty` for ACP bridges. The PTY modifies byte sequences and breaks JSON-RPC framing. Use the Python asyncio bridge (section 4) with raw pipes instead.
- **socat + systemd user service:** If you do use socat, `status=216/GROUP` is a systemd user service group resolution issue. Use a system-level service (`/etc/systemd/system/`) instead.
- **UFW on laptop:** If the laptop has a firewall, allow SSH only from the server IP: `sudo ufw allow from SERVER_IP to any port 22 proto tcp`
- **Arch Linux laptop:** SSH server is `openssh` package, service is `sshd`.
- **ACP is stdio-based:** The Hermes VS Code extension uses Agent Client Protocol (ACP) over stdio, not HTTP. Port tunnels don't work; use Remote SSH or the TCP bridge approach above.
- **Server bridge scripts:** Available under this skill at `scripts/hermes-acp-bridge.py` (server side) and `scripts/hermes-remote-proxy.py` (laptop side). See `references/acp-bridge-tradeoffs.md` for the socat vs Python comparison.
