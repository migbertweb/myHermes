---
name: remote-agent-connectivity
description: Establishing and maintaining persistent connectivity between a local client (laptop) and a remote Hermes Agent (homeserver).
---

# Remote Agent Connectivity

This skill governs the architecture and configuration required to treat a remote Hermes Agent installation as a local service, avoiding redundant installations and maintaining a single, unified personality/memory across devices.

## Architecture Pattern: Centralized Brain
The homeserver acts as the "Brain" (hosting the agent process, memory, skills, and credentials), while the laptop acts as a "Client" (VScodium via Remote SSH, Open WebUI, or Terminal).

**Key insight:** Hermes does NOT expose an OpenAI-compatible HTTP API. It communicates over:
- **ACP (Agent Client Protocol)** over stdio — used by the Hermes VS Code extension
- **Gateway** over messaging platforms (Telegram, Discord)
- **CLI** directly in the terminal

This means Open WebUI cannot connect to Hermes directly; it must connect to an LLM provider (OpenRouter, Ollama, etc.) separately.

## Workflows

### 1. VS Code Remote SSH (Recommended for Hermes ACP Extension)
The [Hermes VS Code extension](https://github.com/joaompfp/hermes-vscode) uses **ACP over stdio** — it spawns `hermes acp` as a local subprocess, NOT an HTTP API. Port tunneling does NOT work for this.

**Setup:**
- Install VS Code Remote SSH extension on the laptop
- Configure an SSH host in `~/.ssh/config`:
  ```
  Host serverhogar
      HostName 192.168.1.8
      User piro
  ```
- Connect VScodium to the remote host via Remote SSH
- The Hermes extension (extensionKind: "workspace") runs on the server
- It spawns `hermes acp` directly on the server where Hermes is already installed

**VSCodium-specific: If the Remote SSH extension fails with a 404 downloading the server REH:**
The `open-remote-ssh-for-trae` extension (v0.0.4) has a bug in URL generation (trailing dot in version). Fix by installing the VSCodium REH manually on the server:
```bash
# Find latest release tag
RELEASE=$(curl -s https://api.github.com/repos/VSCodium/vscodium/releases/latest | python3 -c "import json,sys;print(json.load(sys.stdin)['tag_name'])")
COMMIT="<commit-from-extension-script>"
mkdir -p ~/.vscodium-server/bin/$COMMIT
cd ~/.vscodium-server/bin/$COMMIT
curl -L -o vscode-server.tar.gz "https://github.com/VSCodium/vscodium/releases/download/$RELEASE/vscodium-reh-linux-x64-$RELEASE.tar.gz"
tar -xf vscode-server.tar.gz --strip-components 1
rm vscode-server.tar.gz
```
The extension will find the pre-installed server and skip the broken download.

### 2. Port Tunneling (Laptop $\\rightarrow$ Server)
Use when forwarding specific services (Open WebUI pointing to OpenRouter, local dev services). NOT for Hermes ACP.

- **Tool:** `autossh` for automatic reconnection. On Arch: `sudo pacman -S autossh`
- **Implementation:** Create a systemd service on the laptop:
  ```ini
  [Unit]
  Description=Service Tunnel
  After=network.target
  [Service]
  User=<laptop-user>
  ExecStart=/usr/bin/autossh -M 0 -N -R 8000:localhost:8000 user@server
  Restart=always
  RestartSec=10
  [Install]
  WantedBy=multi-user.target
  ```
- **Prerequisite:** SSH key-based authentication.
- **Caveat:** Only useful if something on the server is actually listening on the target port.

### 3. Reverse Access (Server $\\rightarrow$ Laptop)
Allowing the Agent to SSH into the laptop to read files or run commands.

- **Laptop-side preparation:**
  1. Install SSH server (Arch: `sudo pacman -S openssh && sudo systemctl enable --now sshd`)
  2. Open port 22 for the server's IP only: `sudo ufw allow from <server-ip> to any port 22 proto tcp`
- **Server-side setup:**
  1. Generate an SSH key pair on the homeserver: `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""`
  2. Show the public key for the user to add to the laptop: `cat ~/.ssh/id_ed25519.pub`
  3. User adds it on laptop: `echo "<public-key>" >> ~/.ssh/authorized_keys`
- **Usage:** `ssh <laptop-user>@<laptop-ip> "ls ~/"`

## 4. Remote Ollama Provider

Use Ollama running on a laptop as a Hermes model provider. This allows
the server-side Hermes to run inference on the laptop's local models
instead of relying on cloud APIs.

See `references/remote-ollama-provider.md` for full setup:
- Expose Ollama on the network (`OLLAMA_HOST`)
- Configure Hermes with a custom provider pointing to `http://<laptop>:11434/v1`
- Pitfalls: sudo required for systemd override, firewall rules, no auth by default

## Pitfalls & Lessons
- **Symmetric Auth:** Ensure both sides have keys exchanged to avoid "Permission denied" or interactive prompt hangs.
- **Hermes is not an API server:** Do not plan around Hermes exposing an OpenAI-compatible port. The ACP protocol is stdio-based, not HTTP.
- **Laptop SSH must be enabled:** The laptop needs its own SSH server running and firewall open for the server's IP specifically.
- **Connection refused vs timeout in diagnostics:**
  - `timed out` = firewall is blocking (fix the firewall/UFW)
  - `connection refused` = firewall is open but no service listening (fix the SSH server)
- **VSCodium REH install failure:** The `open-remote-ssh-for-trae` extension can have URL generation bugs. Workaround is manual server installation (see workflow 1).
- **Docker DNS:** Standard Docker bridges cannot see `localhost` of the host machine without specific network configurations or the `host.docker.internal` alias.
- **Find laptop IP from server:** Check `arp -a` or SSH logs (`sudo journalctl -u ssh | grep "Accepted"`).
- **ACP TCP Bridge — use Python asyncio, not socat:** The `socat` tool with `pty` corrupts the ACP JSON-RPC protocol. Use the Python asyncio bridge from `hermes-remote-access` skill instead, which uses raw pipes (byte-perfect). If socat is used, omit the `pty` option and test thoroughly.
