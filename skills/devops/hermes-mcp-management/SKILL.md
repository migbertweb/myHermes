---
name: hermes-mcp-management
description: "Add/verify MCP servers in Hermes (default or per-profile)."
category: devops
---

# Hermes MCP Server Management

Adding and verifying MCP servers in Hermes config (`~/.hermes/config.yaml` or `~/.hermes/profiles/<name>/config.yaml`), including the interactive-prompt trap that silently drops the server.

## When to use

- User asks to install/configure an MCP server in Hermes (e.g. `hermes mcp add`, docs with `npx -y pkg`).
- Need to add the same MCP server to multiple profiles (default + coder-back, coder-front, devops-chief, reseach, qualifier).
- Verifying an MCP server connects and exposes tools.

## Workflow

1. **Check requirements** (stdio npx servers): `node --version` — many modern packages require Node 22+ (e.g. `@heroui/react-mcp`). Also confirm `npx` on PATH.
2. **Backup config before any edit** (per `config-backup-rotation` conventions):
   ```bash
   TS=$(date +%Y%m%d_%H%M%S)
   cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$TS
   # per-profile: cp ~/.hermes/profiles/$P/config.yaml ~/.hermes/profiles/$P/config.yaml.bak.$TS
   ```
3. **Add the server — ALWAYS pipe the answer to the enable prompt**:
   ```bash
   printf 'Y\n' | hermes mcp add NAME --command npx --args -y pkg@latest
   ```
   The CLI connects, discovers tools, then asks `Enable all N tools? [Y/n/select]:`. Without the piped `Y`, the prompt auto-cancels and **nothing is saved** (message says "Cancelled", exit 0 — looks successful, is not).
4. **Per-profile addition**: `printf 'Y\n' | hermes -p <profile> mcp add NAME --command npx --args -y pkg@latest` — writes to that profile's own config.yaml.
5. **Verify**:
   ```bash
   hermes mcp list                 # Status column shows ✓ enabled
   hermes mcp test NAME            # Connected + tools discovered
   hermes -p <profile> mcp list    # per-profile check
   ```
6. **Tell the user a restart is pending** — tools load at gateway/session startup. **Do NOT restart gateways without explicit user instruction** (`hermes -p <profile> gateway restart` is the pending action to mention, not to run).

## Pitfalls

- **The enable prompt cancels even with `pty=true`** — only `printf 'Y\\n' |` (or answering interactively in a real terminal) works. If the server already exists, Hermes asks 'Overwrite? [y/N]' first; use a multi-line pipe like `printf 'y\\nY\\n' |` to handle both the overwrite and the enable prompt.
- **Distinguish between CLI skills and MCP servers**: A skill listed in the library (e.g., `composio`) may only provide instructions for using a third-party CLI tool, not necessarily an MCP server implementation for Hermes. Always verify with `hermes mcp list` before assuming an MCP server is active just because a related skill exists.
- **`--url` servers with an auth prompt break the pipe flow**: before "Enable all N tools?", the CLI asks `Does this server require authentication? [Y/n]` (and possibly `API key / Bearer token:`). A piped `printf` can't answer two prompts (first one eats the input → "Cancelled"). Preferred programmatic alternative: write directly to `~/.hermes/config.yaml` using Python (`yaml.safe_load` / `yaml.dump`) to inject `mcp_servers.<name>` with `url` and `headers` (e.g. `Authorization: "Bearer <token>"`), then verify with `hermes mcp test <name>`.
- **Each profile has its own config.yaml** — `hermes mcp add` without `-p` only touches the default. Don't assume one add covers all profiles.
- **`--args` must be the last option** in `hermes mcp add` (nargs consumes everything after it).
- **`env:` block in mcp_servers config only accepts literal values** — no `{env:VAR}` / `${VAR}` resolution there (see native-mcp skill for wrapper-script workarounds).
- **First `npx` run is slow** (downloads package, ~10s+ connect time) — subsequent runs use the npx cache; a slow first `mcp test` is normal, not a failure.
- **Local stdio servers (TypeScript/Node) need deps installed**: if the server uses a local `command: node` with a `dist/` entry point, run `npm install` (and `npm run build` if dist is missing/stale) in the server directory before `hermes mcp test`. A "Cannot find package" or "Connection closed" error usually means missing `node_modules`.
- **Gateway restart note**: the gateway needs a restart to pick up new MCP servers; a running gateway won't see new tools mid-session. `/reload-mcp` exists in-session for CLI/gateway.

## Verification checklist

- [ ] `hermes mcp list` shows the server with ✓ enabled
- [ ] `hermes mcp test NAME` reports Connected + tool count
- [ ] Config YAML still parses: `python3 -c "import yaml; yaml.safe_load(open('...'))"`
- [ ] User informed of pending gateway restart (not executed without approval)

## Discovery / Audit

To find the last MCP configured or audit all MCP servers in a profile:

```bash
# List all configured MCP servers (default profile)
hermes mcp list

# List for a specific profile
hermes -p <profile> mcp list

# Inspect config.yaml directly for mcp_servers block
grep -A 20 '^mcp_servers:' ~/.hermes/config.yaml
# or per-profile
grep -A 20 '^mcp_servers:' ~/.hermes/profiles/<profile>/config.yaml
```

The `mcp_servers` block in config.yaml is the source of truth — it shows every server (stdio + HTTP), their `enabled` state, `url`/`command`, and headers. Check timestamps on config.yaml (`stat ~/.hermes/config.yaml`) to infer last modification.

**Finding what changed last:**
```bash
stat -c %Y ~/.hermes/config.yaml
# compare with previous backup
find ~/.hermes -maxdepth 1 -name 'config.yaml.bak*' -print0 | xargs -0 stat -c '%Y %n'
# diff mcp_servers keys
python3 - << 'PY'
import yaml
prev=yaml.safe_load(open('~/.hermes/config.yaml.bak'))
cur=yaml.safe_load(open('~/.hermes/config.yaml'))
prev_s=set(prev.get('mcp_servers',{}))
cur_s=set(cur.get('mcp_servers',{}))
print('added',cur_s-prev_s)
print('removed',prev_s-cur_s)
PY
```

**Pitfall:** A server may appear in config.yaml but be `enabled: false` — `hermes mcp list` will show it without the ✓ mark.

**Pitfall:** Duplicate keys in YAML silently keep the last value. `context7:` with a nested `context7:` sub-key is parsed as a nested map, not a server name — inspect the parsed keys with Python, not grep, to avoid reporting phantom servers.
