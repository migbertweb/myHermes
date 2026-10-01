# Remote Ollama Session Trace

Detailed commands and diagnostics from a successful Hermes ↔ remote Ollama setup session.

## Environment

- **Server:** Linux (192.168.1.8) — Hermes Agent host
- **Laptop:** CachyOS / Arch Linux (192.168.1.17) — Ollama host, user `migbert`
- **Ollama models:** `llama3.2:1b`, `gemma3:1b`

## Step-by-Step Commands Used

### 1. Check Ollama status on laptop

```bash
ssh migbert@192.168.1.17 "
  ps aux | grep ollama | grep -v grep
  ss -tlnp | grep 11434
  ollama list
"
```

Typical output — Ollama listening only on 127.0.0.1:

```
LISTEN 0 4096 127.0.0.1:11434 0.0.0.0:*
```

### 2. Diagnosing firewall

From server, test raw TCP:

```bash
timeout 3 bash -c 'echo > /dev/tcp/192.168.1.17/11434'
```

If this times out but ping/SSH work, likely UFW (or other firewall) blocking inbound.

### 3. Check UFW status

```bash
ssh migbert@192.168.1.17 "sudo ufw status verbose"
```

Expected: `Status: active`, `Default: deny (incoming)`, no 11434 rule.

### 4. Fix: systemd override for OLLAMA_HOST

```bash
ssh migbert@192.168.1.17 "
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment=\"OLLAMA_HOST=0.0.0.0:11434\"\n' | \
  sudo tee /etc/systemd/system/ollama.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart ollama
"
```

Verify: `ss -tlnp | grep 11434` → `*:11434`

### 5. Fix: UFW rule

```bash
ssh migbert@192.168.1.17 "
sudo ufw allow from 192.168.1.8 to any port 11434 proto tcp \
  comment 'Ollama - Hermes server'
sudo ufw reload
"
```

### 6. Configure Hermes providers (root-level)

Use the root-level `providers` section — **not** `model_catalog.providers` (which is for model auto-discovery URLs only and does NOT make the provider selectable):

```bash
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

Verify the provider shows up:

```bash
python3 -c "
import sys; sys.path.insert(0, '/home/piro/.hermes/hermes-agent')
from hermes_cli.config import get_compatible_custom_providers, load_config
for p in get_compatible_custom_providers(load_config()):
    print('✅', p['name'], '-', p['base_url'], '- models:', list(p.get('models',{}).keys()))
"
```

### 7. Verify end-to-end

```bash
# From server, test connection
curl -s http://192.168.1.17:11434/v1/models
curl -s http://192.168.1.17:11434/api/tags

# Via Hermes (one-shot)
hermes chat -q "Hola" --provider ollama-laptop --model llama3.2:1b
```

## Pitfalls Encountered

| Problem | Cause | Fix |
|---------|-------|-----|
| Connection timeout from server | UFW default deny inbound | Add explicit `ufw allow` rule |
| `hermes config set` produces YAML string | CLI serializes dict as JSON string | Rewrite with Python `yaml` module directly |
| Ollama only on 127.0.0.1 | Default config | Systemd drop-in with `OLLAMA_HOST=0.0.0.0` |
| `sudo` needs TTY over SSH | No PTY allocated | Use `echo PASSWORD \| sudo -S` or `ssh -tt` |
| Custom provider not showing in `hermes model` / `/model` | Used `model_catalog.providers` (discovery only) instead of root-level `providers` | Use root-level `providers` section with `base_url`, `models`, `model` keys |
| Small model rejected: "context window below minimum 64,000" | `gemma3:1b` has 32K native context | Add `context_length: 8192` to the model entry in the provider's `models` dict |
