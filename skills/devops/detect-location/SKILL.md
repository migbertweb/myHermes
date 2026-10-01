---
name: detect-location
description: Detect and announce which Hermes instance (laptop or server) is running, with environment capabilities.
---

# Detect Location

Run this at session start to determine definitively whether you're on the **laptop** or the **server**.

Always load this skill (`skill_view name=detect-location`) on the first turn of a new session unless `environment_hint` in the system prompt already identifies the location.

## Detection Logic

Run these checks in order:

```bash
echo "hostname=$(hostname) user=$(whoami)"
```

### Laptop (CachyOS / migbert)
- hostname: `cachyos-x8664`
- user: `migbert`
- IP: `192.168.1.17`
- Has display (Hyprland/Wayland)
- Has Zen Browser (Firefox) — CDP **not compatible**
- Has Brave Origin Beta installed (`brave-origin-beta`, v150, Chromium-family) — CDP compatible via `/browser connect`
- Has agent-browser + Chrome headless at `~/.agent-browser/browsers/` (default, funciona sin display)
- Has Firecrawl key + DDGS search
- Hermes gateway runs as systemd user service
- Main model: deepseek-v4-flash-free via OpenCode

### Server (piro / 192.168.1.8)
- hostname: `piro`
- user: `piro`
- IP: `192.168.1.8`
- No display (headless)
- Has Dashscope provider (Qwen models)
- Ollama points to laptop (`192.168.1.17:11434`)
- llama-cpp points to laptop (`192.168.1.17:8080`)
- No Firecrawl, no DDGS configured
- No agent-browser installed
- SSH access to laptop via `cachy` host (ed25519 key)

## Detection Result

After detection, add a holographic fact:

```python
fact_store(
  action='add',
  entity='hermes-instance',
  content='location=laptop (or server)',
  tags='environment,location',
  trust_delta=1.0
)
```

And save a memory note:

```python
memory(
  action='add',
  target='memory',
  content='Running on LAPTOP (CachyOS, migbert@192.168.1.17) — has display, agent-browser, Firecrawl, DDGS. Zen Browser only (no Chromium-family for CDP).'
)
```

(Or analogously for server.)
