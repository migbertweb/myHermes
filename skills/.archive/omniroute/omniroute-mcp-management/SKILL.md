---
name: omniroute-mcp-management
description: Use when enabling/troubleshooting OmniRoute MCP integration.
---

# OmniRoute MCP Management

Guidelines for enabling the Model Context Protocol (MCP) on an OmniRoute gateway and connecting it to Hermes Agent for advanced routing control and tool-based visibility.

## Architecture

OmniRoute provides an embedded MCP server that exposes ~100+ tools (`mcp_omniroute_*`). This is separate from the LLM provider path. While the provider path handles the chat completion, the MCP path allows the agent to manage the gateway itself (switching combos, monitoring quotas, flushing cache, managing plugins).

## Setup Workflow

### 1. Enable MCP on the Gateway
By default, the MCP server is disabled. It must be enabled via the OmniRoute API:

- **Endpoint**: `PUT /api/settings`
- **Payload**: `{"mcpEnabled": true, "mcpTransport": "streamable-http"}`
- **Auth**: Requires a key with `manage` scope.

### 2. Connect to Hermes Agent
Add the MCP server to the `config.yaml`. Since the MCP server requires a Bearer token, it is best to inject it directly into the config to avoid CLI prompt hangs.

**Config block:**
```yaml
mcp_servers:
  omniroute:
    url: http://localhost:20128/api/mcp/stream
    headers:
      Authorization: Bearer <OMNIROUTE_MANAGE_KEY>
    timeout: 180
    connect_timeout: 60
```

### 3. Verification
Test the connection and tool discovery:
```bash
hermes mcp test omniroute
```
Expected: `✓ Connected`, `✓ Tools discovered: 100+`.

## Key Tools (mcp_omniroute_*)

- **Routing**: `omniroute_list_combos`, `omniroute_switch_combo`, `omniroute_simulate_route`.
- **Monitoring**: `omniroute_get_health`, `omniroute_check_quota`, `omniroute_cost_report`.
- **Optimization**: `omniroute_cache_flush`, `omniroute_set_budget_guard`, `omniroute_set_routing_strategy`.
- **Extended**: `omniroute_web_search`, `omniroute_web_fetch`, `omniroute_memory_*`.

## Pitfalls & Lessons

- **Auth Source**: The `manage` API key is often NOT in the `.env` file of Hermes; it lives in the OmniRoute gateway's own internal database (`/app/data/storage.sqlite` in the Docker container, table `api_keys`).
- **Docker Container Data Persistence**: When deployed via Docker (`diegosouzapw/omniroute`), database state lives in `/app/data` (`storage.sqlite`). Standalone `docker run` without a volume leaves data in the container's volatile write layer (`Mounts: []`). Before recreating the container to change env vars (such as `INITIAL_PASSWORD`), back up the data with `docker cp omniroute:/app/data /host/path` and recreate with `-v /host/path:/app/data`.
- **Local (non-Docker) install**: OmniRoute may run as a plain npm process (`omniroute serve --no-open`).\n  - **Binary Path**: Usually located in the node bin folder (e.g., `~/.hermes/node/bin/omniroute`). If missing, reinstall via `npm install -g omniroute` using the specific node environment.\n  - **DB Location**: The DB lives at `~/.omniroute/storage.sqlite` — but the `key` column is STORED TRUNCATED (`sk-27d...acf9`), the full key is NOT recoverable from there. On the laptop, the full manage key already exists in `~/.hermes/.env` as `OMNIROUTE_API_KEY` — reference it in config.yaml as `Authorization: Bearer ${OMNIROUTE_API_KEY}` (Hermes resolves `${VAR}` in headers, no plaintext needed).
- **Transport defaults to `stdio`**: Even after enabling MCP in the dashboard (`mcpEnabled: true`), the transport may remain `stdio` and the stream endpoint returns `400 Bad Request` with `MCP transport is set to "stdio", not "streamable-http"`. Fix via API with a manage-scope key: `curl -X PUT http://localhost:20128/api/settings -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d '{"mcpEnabled": true, "mcpTransport": "streamable-http"}'`.
- **Session-based Tools**: MCP tools require an `initialize` handshake to establish a `mcp-session-id`. If tools return 0 or 401, verify the transport is `streamable-http` and the Bearer token is correct.
- **Independence from Provider**: Enabling the MCP server does NOT change the LLM models Hermes uses. It only adds a toolset for controlling the gateway. To change the model, use `hermes model` or `/model`.
- **Gateway Restart**: After adding an MCP server to `config.yaml`, restart the Hermes gateway (`hermes gateway restart`). For profile gateways, restart each `hermes-gateway-<profile>` user unit (see Multi-Profile Replication below). TUI sessions run an embedded gateway (`tui_gateway.entry`), so MCP tools only appear in NEW sessions — the session open during the config change does not hot-reload.

## Multi-Profile Replication (Hermes profiles)

Each Hermes profile is fully independent: own config.yaml, own `.env`, own gateway service.

- Config: `~/.hermes/profiles/<name>/config.yaml`
- Env: `~/.hermes/profiles/<name>/.env` (usually already has `OMNIROUTE_API_KEY` since profiles use OmniRoute as provider)
- Service: `hermes-gateway-<name>.service` (systemd user unit)

To enable the MCP server on a profile:

1. **Back up**, then append the same `mcp_servers.omniroute` block to that profile's config.yaml (python3 insert; keep `Authorization: Bearer ${OMNIROUTE_API_KEY}` — never the raw key).
2. **Validate** all profile configs parse and carry the block:
   `python3 -c "import yaml,glob; [print(f.split('/')[-2], 'OK' if (lambda d: (d.get('mcp_servers') or {}).get('omniroute',{}).get('url','').endswith('/api/mcp/stream'))(yaml.safe_load(open(f))) else 'MAL') for f in glob.glob('/home/migbert/.hermes/profiles/*/config.yaml')]"`
3. **Restart**: `systemctl --user restart hermes-gateway-<name> ...` (all names in one call).
4. **Verify**: `systemctl --user is-active hermes-gateway-<name>` plus `journalctl --user -u hermes-gateway-<name>.service --since "1 min ago" | grep -i mcp`.

Note: the journalctl line `WARNING tools.mcp_tool: MCP server 'omniroute' tool 'omniroute_github_skills_scan': suspicious description content` is BENIGN — a content filter on one tool's description, not a connection failure. All gateways log it and still connect fine.

## Chat Admission Semaphore (HTTP 503 "capacity is busy")

Hermes requests carry 100+ tools (the omniroute MCP toolset alone is ~107), which trips OmniRoute's admission middleware and causes `503 Structurally heavy chat request capacity is busy` when the single heavy-request slot is held by another concurrent request (kanban task, MoA parallel refs, gateway + kanban overlap). Adding models to OmniRoute does NOT fix this — it's a process-local semaphore, not provider capacity.

- Source: `src/shared/middleware/chatBodyAdmission.ts` in the omniroute npm package.
- Defaults (env vars, applied at process start): `OMNIROUTE_CHAT_MAX_HEAVY_IN_FLIGHT=1` (only ONE heavy request in flight), `OMNIROUTE_CHAT_HEAVY_TOOL_COUNT=64`, `OMNIROUTE_CHAT_HEAVY_ESTIMATED_TOKENS=32000`, `OMNIROUTE_CHAT_LARGE_BODY_BYTES=262144`.
- A request is "heavy" if tools ≥ 64 OR estimated structure tokens ≥ 32k OR body ≥ 256KB — Hermes trips the tool-count threshold on every request.
- Fix: set `Environment=OMNIROUTE_CHAT_MAX_HEAVY_IN_FLIGHT=3` and `Environment=OMNIROUTE_CHAT_HEAVY_TOOL_COUNT=200` in `~/.config/systemd/user/omniroute.service`, then `systemctl --user daemon-reload && systemctl --user restart omniroute` (~5s downtime). With tool threshold at 200, normal Hermes requests stop being classified heavy entirely.
- Verify: `tr '\0' '\n' < /proc/$(pgrep -f "node .*omniroute serve" | head -1)/environ | grep OMNIROUTE_CHAT` + a POST to `/v1/chat/completions` with a Bearer key from `~/.hermes/.env`.
- Full diagnosis + source analysis: `references/chat-admission-semaphore.md`.
