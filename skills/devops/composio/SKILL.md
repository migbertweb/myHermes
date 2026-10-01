---
name: composio
description: Use when managing tools and apps via Composio CLI.
---

# Composio CLI Workflow

Composio provides a unified interface to connect agents to 1000+ apps. This skill covers the lifecycle from installation to tool execution.

## 1. Installation & Authentication
1. **Install CLI**:
   ```bash
   curl -fsSL https://composio.dev/install | sh
   ```
2. **Login**:
   - Run `composio login`.
   - Open the provided URL in a browser to authenticate.
   - **Critical**: Run `composio login --poll` to wait for the authentication to complete and save credentials locally.

## 2. Account Management
To manage or verify connected accounts, a developer project must be initialized in the current working directory.

1. **Initialize Project** (Required for `dev` commands):
   ```bash
   composio dev init
   ```
2. **Link an Application**:
   ```bash
   composio link <toolkit-slug>
   ```
   *Example: `composio link github`*
3. **Verify Connection**:
   ```bash
   composio dev connected-accounts list --toolkits <toolkit-slug>
   ```

## 3. Tool Discovery & Execution
1. **Search for Tools**:
   Use semantic queries to find the right tool slug for a use case.
   ```bash
   composio search "send an email" "create github issue"
   ```
2. **Inspect Tool Schema**:
   Find exactly what arguments a tool requires.
   ```bash
   composio tools info <TOOL_SLUG>
   ```
3. **Execute Action**:
   Pass arguments as a JSON object via the `-d` flag.
   ```bash
   composio execute <TOOL_SLUG> -d '{ "arg1": "value1", "arg2": "value2" }'
   ```

## 4. Advanced Usage
- **Parallel Execution**: Use `-p` to run multiple tool calls concurrently.
  ```bash
  composio execute -p SLUG1 -d '{...}' SLUG2 -d '{...}'
  ```
- **Scripting with `run`**: Use `composio run '<code>'` to execute Bun-based JS/TS code with injected `execute()` and `search()` helpers.
- **API Proxy**: Access app APIs directly using the connected account's auth.
  ```bash
  composio proxy <URL> --toolkit <toolkit-slug>
  ```

## Pitfalls & Rules
- **The `dev init` Wall**: Commands under `composio dev` (like listing connected accounts) will fail with "No developer project configured" unless `composio dev init` has been run in the directory. If running in a transient session (like Hermes terminal), this means account verification via `dev connected-accounts list` may be unavailable without project setup.
- **Login Polling**: `composio login` only starts the process; always follow up with `--poll` to finalize the session.
- **Input Validation**: Use `composio execute --dry-run` to validate JSON inputs against the tool schema without triggering the remote action.

## 5. MCP Tool Execution (Hermes)
When using Composio via MCP in Hermes, use `mcp__composio__COMPOSIO_MULTI_EXECUTE_TOOL`.
- **Required args**: `tools` (array of `{tool_slug, arguments}`), `sync_response_to_workbench` (boolean).
- **Recommended**: Set `current_step` to track progress (e.g., `CREATING_CONTAINER`).

## Recipes
- [Instagram Reels Publication](references/instagram-reels.md)
