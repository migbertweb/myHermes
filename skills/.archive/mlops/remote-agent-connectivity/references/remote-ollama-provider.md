# Remote Ollama as Hermes Model Provider

Configure Hermes Agent on a server to consume models from an Ollama instance
running on a separate machine (e.g., a laptop on the same LAN).

## Architecture

```
Hermes Agent (server)         Ollama (laptop)
  ┌──────────────────┐          ┌──────────────┐
  │  HTTP client ──────────►    │  localhost    │
  │  (OpenAI-compat)    │  │    │  :11434/v1    │
  │                    │     │  │  llama3.2:1b  │
  │  model.provider:   │     │  │  gemma3:1b    │
  │    custom:ollama   │     │  └──────────────┘
  │  model.base_url:   │     │
  │    http://laptop   │     │
  │    :11434/v1       │     │
  └──────────────────┘          LAN
```

Ollama exposes an **OpenAI-compatible API** at `http://<host>:11434/v1`,
so Hermes can use it as any other OpenAI-compatible provider.

## Step 1 — Expose Ollama on the network

Ollama binds to `127.0.0.1` by default. To reach it from another machine
on the LAN, set `OLLAMA_HOST`:

### Via systemd override (recommended)

```ini
# /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
# create the override.conf above
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### Via environment variable (ad-hoc)

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

Verify from the server:
```bash
curl http://<laptop-ip>:11434/api/tags     # list models
curl http://<laptop-ip>:11434/v1/models    # OpenAI-compatible model list
```

## Step 2 — Configure Hermes to use the remote Ollama

Use `hermes config set` to point to the remote endpoint:

```bash
hermes config set model.provider "custom:ollama-local"
hermes config set model.base_url "http://<laptop-ip>:11434/v1"
hermes config set model.default "llama3.2:1b"
```

Or manually in `~/.hermes/config.yaml`:

```yaml
model:
  default: llama3.2:1b
  provider: custom:ollama-local
  base_url: http://192.168.1.17:11434/v1
```

The `custom:<name>` provider tells Hermes to use the configured
`base_url` as an OpenAI-compatible endpoint without additional auth.
If the Ollama endpoint requires no API key (Ollama default), no
`api_key` is needed.

## Step 3 — Test

```bash
hermes chat -q "Say hello" -m llama3.2:1b --provider custom:ollama-local
```

Or if the default is already set:
```bash
hermes chat -q "Say hello"
```

## Pitfalls

- **Ollama binds to 127.0.0.1 out of the box.** You MUST change
  `OLLAMA_HOST` for remote access. `curl` from another machine will
  hang or refuse — check `ss -tlnp | grep 11434` to confirm the bind
  address.
- **sudo required for systemd override.** If you're SSHing into the
  laptop and the user needs a password for sudo, use `ssh -tt` or
  ask the user to run the commands locally. Non-TTY sudo won't work.
- **Firewall on the laptop.** Ensure port 11434 isn't blocked by a
  local firewall (ufw, firewalld). On Arch: `sudo ufw allow from
  <SERVER_IP> to any port 11434 proto tcp`.
- **Ollama has no auth by default.** Anyone on the LAN can hit the API
  once it's on `0.0.0.0`. For production or untrusted networks, set
  `OLLAMA_HOST` to the specific LAN IP (not `0.0.0.0`) or add a
  reverse proxy with authentication.
- **Model names.** Use the exact model tag from `ollama list`
  (e.g. `llama3.2:1b`, not `llama3.2` if the tag matters).
- **Custom provider naming.** The `custom:<name>` label is arbitrary
  but should be descriptive (e.g. `custom:laptop-ollama`). Only one
  custom provider can be active at a time unless you use the
  `model_catalog.providers` section.
