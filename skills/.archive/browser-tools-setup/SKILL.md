---
name: browser-tools-setup
description: Configure and troubleshoot browser tools in Hermes Agent, including local-mode Chromium/Chrome installation via agent-browser CLI, CDP connection, and cloud provider setup.
version: 2.0.0
author: Viernes
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [browser, chromium, agent-browser, local-mode, cdp, setup, arch]
---

# Browser Tools Setup

Guidelines for setting up and maintaining the browser toolset in Hermes Agent.
Covers all three backends:

1. **Local agent-browser** — headless Chromium driven programmatically (no visible window)
2. **CDP connect** — attach to a running Chromium-family browser (Brave, Chrome, Edge)
3. **Cloud providers** — Browserbase, Firecrawl, Browser Use (no local browser needed)

## Prerequisites

- Node.js (for agent-browser CLI)
- `npm` in PATH

### npm Global Install Path

If `npm install -g` fails with **EACCES**, configure a user-level prefix:

```bash
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

This avoids needing sudo for global npm packages.

## Option A: Local agent-browser (headless, no visible window)

Hermes spawns its own dedicated Chromium — does not use the system browser, no visible window.

### Install agent-browser

```bash
npm install -g agent-browser
```

### Install bundled Chromium

```bash
agent-browser install
```

On Arch Linux / CachyOS (no apt/dnf/yum), `--with-deps` will fail. Install without it:
- Chromium downloads and runs fine without system deps on modern distros
- If you see missing `.so` errors, install manually: `sudo pacman -S nss nspr libxcomposite libxdamage libxrandr alsa-lib atk at-spi2-core cups libxkbcommon`

### Verification

```bash
agent-browser --version           # should show version number
~/.agent-browser/browsers/chrome-*/chrome --version  # should launch and report version
```

### PATH persistence

Add to shell profile if agent-browser was installed to custom prefix:
```bash
export PATH="$HOME/.npm-global/bin:$PATH"
```

## Option B: CDP connect to running browser

Use existing Chromium-family browsers (Brave, Google Chrome, Chromium, Edge).

### Auto-connect

In Hermes CLI:
```
/browser connect
```

Hermes auto-detects Brave, Chrome, Chromium, and Edge from common Linux install paths.

### Manual launch + connect

Start the browser with a dedicated profile and remote debugging:

```bash
brave --remote-debugging-port=9222 \
      --user-data-dir=$HOME/.hermes/chrome-debug \
      --no-first-run --no-default-browser-check &
```

Then in Hermes CLI:
```
/browser connect ws://127.0.0.1:9222
```

**Compatibility:**
- ✓ Brave (Chromium-based) — works
- ✓ Google Chrome — works
- ✓ Chromium — works
- ✓ Microsoft Edge — works
- ✗ Zen Browser (Firefox-based) — not compatible with CDP
- ✗ Firefox — not compatible with CDP

## Option C: Cloud providers (no local install)

Set credentials in `~/.hermes/.env`, then configure via `hermes setup tools`:

| Provider | Env vars needed | Plan |
|----------|----------------|------|
| Firecrawl | `FIRECRAWL_API_KEY` | Free tier |
| Browserbase | `BROWSERBASE_API_KEY` | Free hours/mo |
| Browser Use | `BROWSER_USE_API_KEY` | Paid |

**Browserbase does NOT need `BROWSERBASE_PROJECT_ID`** — the API key alone resolves the project (verified 2026-08-13; old docs/training data saying otherwise are outdated). Never ask for or set it.

For the standalone `browse` CLI + Stagehand SDK (driving Browserbase from your own scripts, not just Hermes browser tools), see `references/browserbase-cli-stagehand-v4.md` — covers CLI install, session verification, and the Stagehand v4 API that breaks v3-era templates.

Firecrawl can be used as both web extract backend AND browser provider:
```
hermes setup tools → Browser Automation → Firecrawl
```

When a cloud provider is set, Hermes auto-routes private URLs (localhost, 192.168.x.x, etc.) to the local agent-browser sidecar.

## How the browser engine resolves

The resolution chain in `~/.hermes/config.yaml`:

```yaml
browser:
  engine: auto   # auto = prefer agent-browser local, fall through to cloud
```

Order:
1. If cloud provider credentials exist → use cloud (Browserbase > Browser Use > Firecrawl)
2. If `cdp_url` is set or `/browser connect` active → use CDP
3. If `camofox` URL set → use Camofox
4. Otherwise → agent-browser local mode

## Troubleshooting

### SPA behind Cloudflare: login bypass via token injection

When a Single-Page Application (React/Vue) is behind Cloudflare and `browser_click` login fails (Cloudflare blocks fetch or interferes with form submission), use the workflow in `references/spa-auth-bypass.md`:

1. Discover the login API endpoint from the JS bundle (`grep -oP 'login|/api/'`)
2. Authenticate via curl, extract the auth token
3. Base64-encode the token for transport past tool-output truncation
4. Inject into browser localStorage via `atob()` in `browser_console`
5. Reload — the SPA's auth check picks up the token

### "Browser not found" or "Failed to launch"

1. Check binary presence: `ls ~/.agent-browser/browsers/chrome-*/chrome`
2. Run manually to see missing libraries: `~/.agent-browser/browsers/chrome-*/chrome --version`
3. Install missing libs (Arch): `sudo pacman -S nss nspr libxcomposite libxdamage libxrandr alsa-lib atk at-spi2-core cups libxkbcommon`
4. Install missing libs (Debian): `sudo apt install -y libnss3 libnspr4 libatk1.0-0t64 libcups2t64 libgbm1 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libasound2t64 libpango-1.0-0`

### npm install -g fails with EACCES\n\nUse user-level prefix (see Prerequisites section above).\n\n### Chromium Sandbox / AppArmor block (Ubuntu 23.10+)\n\nOn newer Ubuntu versions, Chromium's sandbox is often blocked by AppArmor when run as a non-privileged user without specific namespaces enabled, causing `browser_navigate` to timeout or fail silently.\n\n**Fix:** Use the `agent-browser` CLI to launch with the `--no-sandbox` flag.\n\n```bash\nnpx agent-browser open \"<url>\" --args \"--no-sandbox\"\n```\n\n**Warning:** If the `agent-browser` daemon is already running, flags passed to `open` are ignored. You must close existing sessions first:\n```bash\nnpx agent-browser close --all\n```

### agent-browser install --with-deps fails on Arch

Expected — there's no apt/dnf/yum. Just use `agent-browser install` (without `--with-deps`). The bundled Chromium ships with its own shared libraries and works on modern distros.
