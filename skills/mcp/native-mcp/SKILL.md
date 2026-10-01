---
name: native-mcp
description: "MCP client: connect servers, register tools (stdio/HTTP)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MCP, Tools, Integrations]
    related_skills: [mcporter]
---

# Native MCP Client

Hermes Agent has a built-in MCP client that connects to MCP servers at startup, discovers their tools, and makes them available as first-class tools the agent can call directly. No bridge CLI needed -- tools from MCP servers appear alongside built-in tools like `terminal`, `read_file`, etc.

## When to Use

Use this whenever you want to:
- Connect to MCP servers and use their tools from within Hermes Agent
- Add external capabilities (filesystem access, GitHub, databases, APIs) via MCP
- Run local stdio-based MCP servers (npx, uvx, or any command)
- Connect to remote HTTP/StreamableHTTP MCP servers
- Have MCP tools auto-discovered and available in every conversation

For ad-hoc, one-off MCP tool calls from the terminal without configuring anything, see the `mcporter` skill instead.

## Prerequisites

- **mcp Python package** -- optional dependency; install with `pip install mcp`. If not installed, MCP support is silently disabled.
- **Node.js** -- required for `npx`-based MCP servers (most community servers)
- **uv** -- required for `uvx`-based MCP servers (Python-based servers)

Install the MCP SDK:

```bash
pip install mcp
# or, if using uv:
uv pip install mcp
```

## Quick Start

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

**Important:** The `env:` block only accepts literal values — template syntax like `{env:MY_VAR}` or `${MY_VAR}` does NOT resolve here. See "Variable Resolution in env:" in the Configuration Reference for details and workarounds.

```yaml
mcp_servers:
  github:
    command: "uvx"
    args: ["mcp-server-time"]
```

Restart Hermes Agent. On startup it will:
1. Connect to the server
2. Discover available tools
3. Register them with the prefix `mcp_time_*`
4. Inject them into all platform toolsets

You can then use the tools naturally -- just ask the agent to get the current time.

## Configuration Reference

Each entry under `mcp_servers` is a server name mapped to its config. There are two transport types: **stdio** (command-based) and **HTTP** (url-based).

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

**Important:** The `env:` block only accepts literal values — template syntax like `{env:MY_VAR}` or `${MY_VAR}` does NOT resolve here. See "Variable Resolution in env:" in the Configuration Reference for details and workarounds.

```yaml
mcp_servers:
  github:
    command: "npx"             # (required) executable to run
    args: ["-y", "pkg-name"]   # (optional) command arguments, default: []
    env:                       # (optional) environment variables for the subprocess
      SOME_API_KEY: "value"
    timeout: 120               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

**Important:** The `env:` block only accepts literal values — template syntax like `{env:MY_VAR}` or `${MY_VAR}` does NOT resolve here. See "Variable Resolution in env:" in the Configuration Reference for details and workarounds.

```yaml
mcp_servers:
  github:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) HTTP headers
      Authorization: "Bearer sk-..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### All Config Options

| Option            | Type   | Default | Description                                       |
|-------------------|--------|---------|---------------------------------------------------|
| `command`         | string | --      | Executable to run (stdio transport, required)     |
| `args`            | list   | `[]`    | Arguments passed to the command                   |
| `env`             | dict   | `{}`    | Environment variables for the subprocess (literal values only!) |
| `url`             | string | --      | Server URL (HTTP transport, required)             |
| `headers`         | dict   | `{}`    | HTTP headers sent with every request              |
| `timeout`         | int    | `120`   | Per-tool-call timeout in seconds                  |
| `connect_timeout` | int    | `60`    | Timeout for initial connection and discovery      |

Note: A server config must have either `command` (stdio) or `url` (HTTP), not both.

### ⚠️ Variable Resolution in `env:` Block — Only Literal Values

Hermes resolves `${VAR}` templates in `command`, `args`, `url`, and `headers` fields, but **NOT** in the `env:` block values. The `env:` dict is passed verbatim to the subprocess — any template syntax like `{env:MY_VAR}`, `${MY_VAR}`, or `$MY_VAR` is sent as a literal string.

```yaml
# 🚫 BROKEN — template is not resolved, subprocess receives literal "{env:TOKEN}"
mcp_servers:
  my-server:
    command: "npx"
    args: ["-y", "some-package"]
    env:
      API_TOKEN: "{env:API_TOKEN}"   # passes literal text "{env:API_TOKEN}"

# ✅ CORRECT — literal value goes through as-is
mcp_servers:
  my-server:
    command: "npx"
    args: ["-y", "some-package"]
    env:
      API_TOKEN: "sk-real-token-value-here"
```

This is especially tricky when an MCP server's docs show `{env:VAR}` syntax (common in Claude Desktop configs) — Hermes does NOT support that in `env:` values. If the server also calls `dotenv.config()` to load a `.env` from its own directory, see workarounds below.

**Workarounds to avoid putting secrets in config.yaml:**

1. **Wrapper script** — Create a shell script that sources `~/.hermes/.env` then execs the MCP server. The `command:` field points to the wrapper, no `env:` block needed since the script injects the vars.

2. **Global install + server's own `.env`** — Install the MCP package globally (`npm install -g ...`), run its OAuth/setup wizard (which writes a `.env` next to the installed files), and point `command` at the installed entry point. The server's `dotenv.config()` picks it up from its own directory.

3. **Inline literal values** — Fastest but least secure: paste secrets directly into the `env:` block. Acceptable for local single-user setups where the config file is not shared.

4. **`hermes mcp add --env KEY=VALUE`** — The CLI tool accepts env vars as `KEY=VALUE` arguments and writes them as literal values into the config. Prefer this over manually editing the YAML.

### ⚠️ Variable Resolution in `env:` Block — Only Literal Values

Hermes resolves `${VAR}` templates in `command`, `args`, `url`, and `headers` fields, but **NOT** in the `env:` block values. The `env:` dict is passed verbatim to the subprocess — any template syntax like `{env:MY_VAR}`, `${MY_VAR}`, or `$MY_VAR` is sent as a literal string.

```yaml
# 🚫 BROKEN — template is not resolved, subprocess receives literal "{env:TOKEN}"
mcp_servers:
  my-server:
    command: "npx"
    args: ["-y", "some-package"]
    env:
      API_TOKEN: "{env:API_TOKEN}"   # passes literal text "{env:API_TOKEN}"

# ✅ CORRECT — use the actual value directly
mcp_servers:
  my-server:
    command: "npx"
    args: ["-y", "some-package"]
    env:
      API_TOKEN: "sk-real-token-value-here"   # literal value
```

This is especially tricky when the MCP server's own docs show `.env`-style config for Claude Desktop — Claude Desktop resolves `{env:VAR}` templates, but Hermes does not. If the server also calls `dotenv.config()` to load a `.env` from its own directory, see workarounds below.

**Workarounds for passing env vars without putting secrets in config.yaml:**

1. **Wrapper script** — Create a shell script that sources `~/.hermes/.env` then runs the MCP server:

   ```bash
   #!/bin/bash
   # ~/.hermes/scripts/youtube-mcp-wrapper.sh
   set -a; source ~/.hermes/.env; set +a
   exec npx -y @a.ardeshir/youtube-mcp "$@"
   ```
   
   Config references the wrapper as `command` (no `env:` block needed since the script sources it).

2. **Global install + server's own `.env`** — Install the MCP package globally, run its OAuth setup wizard (which writes a `.env` next to the installed files), and point `command` at the installed entry point. The server's `dotenv.config()` loads the `.env` from its own directory.

3. **Literal values in config.yaml** — Fastest but least secure: paste the values directly into the `env:` block. Only do this for local, single-user setups where the config file is not shared.

## How It Works

### Startup Discovery

When Hermes Agent starts, `discover_mcp_tools()` is called during tool initialization:

1. Reads `mcp_servers` from `~/.hermes/config.yaml`
2. For each server, spawns a connection in a dedicated background event loop
3. Initializes the MCP session and calls `list_tools()` to discover available tools
4. Registers each tool in the Hermes tool registry

### Tool Naming Convention

MCP tools are registered with the naming pattern:

```
mcp_{server_name}_{tool_name}
```

Hyphens and dots in names are replaced with underscores for LLM API compatibility.

Examples:
- Server `filesystem`, tool `read_file` → `mcp_filesystem_read_file`
- Server `github`, tool `list-issues` → `mcp_github_list_issues`
- Server `my-api`, tool `fetch.data` → `mcp_my_api_fetch_data`

### Auto-Injection

After discovery, MCP tools are automatically injected into all `hermes-*` platform toolsets (CLI, Discord, Telegram, etc.). This means MCP tools are available in every conversation without any additional configuration.

### Connection Lifecycle

- Each server runs as a long-lived asyncio Task in a background daemon thread
- Connections persist for the lifetime of the agent process
- If a connection drops, automatic reconnection with exponential backoff kicks in (up to 5 retries, max 60s backoff)
- On agent shutdown, all connections are gracefully closed

### Idempotency

`discover_mcp_tools()` is idempotent -- calling it multiple times only connects to servers that aren't already connected. Failed servers are retried on subsequent calls.

## Transport Types

### Stdio Transport

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

**Important:** The `env:` block only accepts literal values — template syntax like `{env:MY_VAR}` or `${MY_VAR}` does NOT resolve here. See "Variable Resolution in env:" in the Configuration Reference for details and workarounds.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

The subprocess inherits a **filtered** environment (see Security section below) plus any variables you specify in `env`.

### HTTP / StreamableHTTP Transport

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

**Important:** The `env:` block only accepts literal values — template syntax like `{env:MY_VAR}` or `${MY_VAR}` does NOT resolve here. See "Variable Resolution in env:" in the Configuration Reference for details and workarounds.

```yaml
mcp_servers:
  github:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

If HTTP support is not available in your installed `mcp` version, the server will fail with an ImportError and other servers will continue normally.

## Security

### Environment Variable Filtering

For stdio servers, Hermes does NOT pass your full shell environment to MCP subprocesses. Only safe baseline variables are inherited:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Any `XDG_*` variables

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

**Important:** The `env:` block only accepts literal values — template syntax like `{env:MY_VAR}` or `${MY_VAR}` does NOT resolve here. See "Variable Resolution in env:" in the Configuration Reference for details and workarounds.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### Credential Stripping in Error Messages

If an MCP tool call fails, any credential-like patterns in the error message are automatically redacted before being shown to the LLM. This covers:

- GitHub PATs (`ghp_...`)
- OpenAI-style keys (`sk-...`)
- Bearer tokens
- Generic `token=`, `key=`, `API_KEY=`, `password=`, `secret=` patterns

## Troubleshooting

### "MCP SDK not available -- skipping MCP tool discovery"

The `mcp` Python package is not installed. Install it:

```bash
pip install mcp
```

### "No MCP servers configured"

No `mcp_servers` key in `~/.hermes/config.yaml`, or it's empty. Add at least one server.

### "Failed to connect to MCP server 'X'"

Common causes:
- **Command not found**: The `command` binary isn't on PATH. Ensure `npx`, `uvx`, or the relevant command is installed.
- **Package not found**: For npx servers, the npm package may not exist or may need `-y` in args to auto-install.
- **Timeout**: The server took too long to start. Increase `connect_timeout`.
- **Port conflict**: For HTTP servers, the URL may be unreachable.

### "MCP server connects but API calls fail with auth errors (e.g. 'invalid_client', '401', 'unauthorized')"

The MCP server starts and connects fine, but every tool call returns an auth error. This usually means the `env:` block is passing template strings as literal values instead of resolved credentials.

**Diagnosis:** Check the MCP server's startup message. If it says "Authenticated with OAuth" but calls fail with "invalid_client", the server found *something* in `env:` — likely a literal `{env:MY_VAR}` string. The server can't distinguish between a real credential and a template placeholder; it just uses whatever string it received.

**Fix:** Replace any `{env:...}`, `${...}`, or `$VAR` patterns in the `env:` block with actual literal values. The `env:` block does NOT support variable resolution. See the Configuration Reference above for workarounds (wrapper script, global install, or inline values).

**Verification:** Restart Hermes after fixing, then call a read-only tool. If it returns real data, auth is working.

### "MCP server connects but API calls fail with auth errors (e.g. 'invalid_client', '401', 'unauthorized')"

The MCP server starts and connects fine, but every tool call returns an auth error. This usually means the `env:` block is passing template strings as literal values instead of resolved credentials.

**Diagnosis:** Check the MCP server's startup log message. If it says "Authenticated with OAuth" (or similar success) but calls fail with "invalid_client", the server found *something* in its env — likely a literal `{env:MY_VAR}` string. The server can't distinguish between a real credential and a template placeholder; it just uses whatever string it received.

**Fix:** Replace any `{env:...}`, `${...}`, or `$VAR` patterns in the `env:` block with actual literal values. The `env:` block does NOT support variable resolution. Use the workarounds described in the Configuration Reference (wrapper script, global install + dotenv, or inline values).

**Verification:** Restart Hermes after fixing the config, then call a read-only MCP tool. If it returns real data, auth is working.

### "MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available"

Your `mcp` package version doesn't include HTTP client support. Upgrade:

```bash
pip install --upgrade mcp
```

### Tools not appearing

- Check that the server is listed under `mcp_servers` (not `mcp` or `servers`)
- Ensure the YAML indentation is correct
- Look at Hermes Agent startup logs for connection messages
- Tool names are prefixed with `mcp_{server}_{tool}` -- look for that pattern

### Connection keeps dropping

The client retries up to 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 60s). If the server is fundamentally unreachable, it gives up after 5 attempts. Check the server process and network connectivity.

## Examples

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

**Important:** The `env:` block only accepts literal values — template syntax like `{env:MY_VAR}` or `${MY_VAR}` does NOT resolve here. See "Variable Resolution in env:" in the Configuration Reference for details and workarounds.

```yaml
mcp_servers:
  github:
    command: "uvx"
    args: ["mcp-server-time"]
```

Registers tools like `mcp_time_get_current_time`.

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

**Important:** The `env:` block only accepts literal values — template syntax like `{env:MY_VAR}` or `${MY_VAR}` does NOT resolve here. See "Variable Resolution in env:" in the Configuration Reference for details and workarounds.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    timeout: 30
```

Registers tools like `mcp_filesystem_read_file`, `mcp_filesystem_write_file`, `mcp_filesystem_list_directory`.

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

**Important:** The `env:` block only accepts literal values — template syntax like `{env:MY_VAR}` or `${MY_VAR}` does NOT resolve here. See "Variable Resolution in env:" in the Configuration Reference for details and workarounds.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
    timeout: 60
```

Registers tools like `mcp_github_list_issues`, `mcp_github_create_pull_request`, etc.

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

**Important:** The `env:` block only accepts literal values — template syntax like `{env:MY_VAR}` or `${MY_VAR}` does NOT resolve here. See "Variable Resolution in env:" in the Configuration Reference for details and workarounds.

```yaml
mcp_servers:
  github:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
      X-Team-Id: "engineering"
    timeout: 180
    connect_timeout: 30
```

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

**Important:** The `env:` block only accepts literal values — template syntax like `{env:MY_VAR}` or `${MY_VAR}` does NOT resolve here. See "Variable Resolution in env:" in the Configuration Reference for details and workarounds.

```yaml
mcp_servers:
  github:
    command: "uvx"
    args: ["mcp-server-time"]

  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"

  company_api:
    url: "https://mcp.internal.company.com/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
    timeout: 300
```

All tools from all servers are registered and available simultaneously. Each server's tools are prefixed with its name to avoid collisions.

## Sampling (Server-Initiated LLM Requests)

Hermes supports MCP's `sampling/createMessage` capability — MCP servers can request LLM completions through the agent during tool execution. This enables agent-in-the-loop workflows (data analysis, content generation, decision-making).

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

**Important:** The `env:` block only accepts literal values — template syntax like `{env:MY_VAR}` or `${MY_VAR}` does NOT resolve here. See "Variable Resolution in env:" in the Configuration Reference for details and workarounds.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "my-mcp-server"]
    sampling:
      enabled: true           # default: true
      model: "gemini-3-flash" # model override (optional)
      max_tokens_cap: 4096    # max tokens per request
      timeout: 30             # LLM call timeout (seconds)
      max_rpm: 10             # max requests per minute
      allowed_models: []      # model whitelist (empty = all)
      max_tool_rounds: 5      # tool loop limit (0 = disable)
      log_level: "info"       # audit verbosity
```

Servers can also include `tools` in sampling requests for multi-turn tool-augmented workflows. The `max_tool_rounds` config prevents infinite tool loops. Per-server audit metrics (requests, errors, tokens, tool use count) are tracked via `get_mcp_status()`.

Disable sampling for untrusted servers with `sampling: { enabled: false }`.

## Notes

- MCP tools are called synchronously from the agent's perspective but run asynchronously on a dedicated background event loop
- Tool results are returned as JSON with either `{"result": "..."}` or `{"error": "..."}`
- The native MCP client is independent of `mcporter` -- you can use both simultaneously
- Server connections are persistent and shared across all conversations in the same agent process
- Adding or removing servers requires restarting the agent (no hot-reload currently)
