---
name: ollama-integration
description: "Connect Hermes Agent to local or remote Ollama instances as model providers."
version: 1.0.0
author: Viernes
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [ollama, provider, custom-provider, remote-models, ufw, systemd]
---

# Ollama Integration for Hermes

Connect Hermes Agent to Ollama instances running on the same machine or on another machine on the LAN. Ollama exposes an OpenAI-compatible API at `/v1` that Hermes can consume directly.

## Quick Start (Local)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2:1b

# Ollama runs on http://localhost:11434 by default
# Configure Hermes to use it:
hermes config set model.provider custom:ollama-local
hermes config set model.base_url http://localhost:11434/v1
hermes config set model.default llama3.2:1b
```

## Remote Ollama (Cross-Machine)

Use Ollama running on another machine (e.g. a laptop with GPU) from the Hermes server.

### Step 1 — Make Ollama listen on the network

By default, Ollama binds to `127.0.0.1` only. Override via systemd drop-in:

```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d

# Create override with OLLAMA_HOST=0.0.0.0
printf '[Service]\nEnvironment="OLLAMA_HOST=0.0.0.0:11434"\n' | \
  sudo tee /etc/systemd/system/ollama.service.d/override.conf

sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Verify it's listening on all interfaces:

```bash
ss -tlnp | grep 11434
# Should show: LISTEN 0 4096 *:11434 *:*
```

### Step 2 — Allow remote access through firewall

If the machine has UFW, allow the Hermes server IP only:

```bash
sudo ufw allow from <SERVER_IP> to any port 11434 proto tcp
sudo ufw reload
sudo ufw status | grep 11434
# Expected: 11434/tcp ALLOW <SERVER_IP>
```

Allow SSH from the server too if not already done:

```bash
sudo ufw allow from <SERVER_IP> to any port 22 proto tcp
```

### Step 3 — Configure Hermes (server side)

Add the remote Ollama as a custom provider in the root-level `providers` section of `config.yaml`. This is a **different key** from `model_catalog.providers` (which is for model discovery URLs only).

Edit `~/.hermes/config.yaml` and add:

```yaml
providers:
  ollama-laptop:
    base_url: http://<LAPTOP_IP>:11434/v1
    api_key: ''
    models:
      llama3.2:1b: {}
      gemma3:1b: {}
    model: llama3.2:1b
```

Use Python to edit (since `hermes config set` stores nested values as JSON strings):

```python
python3 -c "
import yaml
with open('/home/piro/.hermes/config.yaml') as f:
    config = yaml.safe_load(f)
config['providers'] = {
    'ollama-laptop': {
        'base_url': 'http://192.168.1.17:11434/v1',
        'api_key': '',
        'models': {'llama3.2:1b': {}, 'gemma3:1b': {}},
        'model': 'llama3.2:1b'
    }
}
with open('/home/piro/.hermes/config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
"
```

The root-level `providers` key is a different section from `model_catalog.providers`. The `model_catalog` section handles model auto-discovery URLs; the root `providers` section defines actual runnable provider endpoints that appear in the `hermes model` picker and in `/model` completions.

### Step 3a — Context length override for small models

Small Ollama models (e.g. `gemma3:1b`, `phi3:mini`, `tinyllama`) often have a context window below Hermes' 64K minimum. Hermes will refuse to initialise with:

```
Failed to initialize agent: Model <name> has a context window of <N> tokens, which is below the minimum 64,000 required by Hermes Agent.
```

Fix by setting `context_length` explicitly on the model inside the provider config:

```yaml
providers:
  ollama-laptop:
    base_url: http://192.168.1.17:11434/v1
    api_key: ''
    models:
      llama3.2:1b: {}
      gemma3:1b:
        context_length: 8192   # 👈 override Hermes' 64K minimum
    model: llama3.2:1b
```

Set `context_length` to the model's actual native context or lower — Hermes will cap at this value instead of enforcing its own minimum. 8K is a safe value for 1B-class models. The default model (`llama3.2:1b`) typically has a larger native context and usually doesn't need this override, but small models like `gemma3:1b` always will.

### Step 4 — Switch to the Ollama model

```bash
# Interactive picker — ollama-laptop will now appear in the list
hermes model

# Or switch directly
hermes config set model.provider ollama-laptop
hermes config set model.default llama3.2:1b
```

Or switch mid-session with `/model ollama-laptop/llama3.2:1b`.

## Verification

### From the Hermes server, test connectivity:

```bash
# List models
curl -s http://<LAPTOP_IP>:11434/api/tags

# Check OpenAI-compatible endpoint
curl -s http://<LAPTOP_IP>:11434/v1/models

# Quick inference test
curl -s http://<LAPTOP_IP>:11434/api/generate \
  -d '{"model":"llama3.2:1b","prompt":"Say hello","stream":false}'
```

### Via Hermes:

```bash
hermes chat -q "Hello, what model are you?" --provider ollama-laptop --model llama3.2:1b
```

### Sanity check — primary provider still works

After adding a custom Ollama provider, verify your main/default provider hasn't been affected:

```bash
# List models from the active provider
curl -s -m 10 "$(hermes config get model.base_url)/models" | python3 -m json.tool | head -20

# Or just test with a quick query
hermes chat -q "Hi, respond with OK" --provider "$(hermes config get model.provider)" --model "$(hermes config get model.default)"
```

This catches accidental config corruption (e.g. if the YAML edit accidentally removed or flattened the `model` section).

## Pitfalls

- **UFW blocks inbound by default:** Even if Ollama is listening on `0.0.0.0`, UFW's `deny (incoming)` policy will drop the connection. Always add an explicit allow rule.
- **Small models need `context_length` override to work with Hermes:** Models with native context < 64K tokens (e.g. `gemma3:1b` at 32K) cause Hermes to refuse initialisation. Add `context_length: <N>` under the model entry in the provider config to override Hermes' minimum check (see Step 3a). Set it to the model's actual native window or lower — Hermes caps at this value.
- **`hermes config set` stores nested objects as YAML strings:** The CLI serializes dict values as JSON strings. After setting a config value with a JSON object, use Python's `yaml.dump()` to rewrite the file as proper nested YAML (see Step 3 for the fix).
- **Use root-level `providers`, not `model_catalog.providers`:** The `model_catalog.providers` section is for model auto-discovery URLs — it fetches model lists from external endpoints. It does NOT define a selectable runtime provider. To add a custom LLM endpoint that appears in `hermes model` and `/model`, use the root-level `providers:` key in `config.yaml` with the format shown in Step 3.
- **Ollama binds to 127.0.0.1 by default:** Always verify with `ss -tlnp | grep 11434` after configuration. If it shows `127.0.0.1:11434`, the systemd override didn't apply correctly.
- **Service needs restart after config change:** `sudo systemctl daemon-reload && sudo systemctl restart ollama` — `daemon-reload` is required after adding/modifying a drop-in.
- **API key not needed:** Ollama by default requires no API key. Set `api_key: ''` or omit it.
- **LAN-only:** Keep the bind to `0.0.0.0` only on trusted networks. For WAN access, use a VPN/Tailscale and bind to the tunnel interface instead.
- **Ping the laptop first:** Before debugging Ollama, confirm basic connectivity: `ping <LAPTOP_IP>` and `ssh user@<LAPTOP_IP> "echo OK"`.

## Scripts & References

- `scripts/verify-remote-ollama.py` — Standalone connectivity + inference test for remote Ollama. Run with: `python3 scripts/verify-remote-ollama.py <HOST> [PORT]`.
- `references/remote-ollama-session-trace.md` — Exact commands, error messages, and diagnostics from a successful setup session.

## Related Skills

- `hermes-remote-access` — Set up Hermes itself on a server and connect editors.
- `llama-cpp` — Local GGUF inference (alternative to Ollama for on-server models).
