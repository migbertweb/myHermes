# Common MCP Server Patterns

Quick reference for frequently-used MCP servers and their Hermes config patterns.

## Hugging Face MCP Server

**Repository:** https://github.com/huggingface/hf-mcp-server
**Public endpoint:** https://huggingface.co/mcp

### Auth modes

| Mode | URL | Headers | Use case |
|------|-----|---------|----------|
| OAuth interactive | `https://huggingface.co/mcp?login` | none | One-time setup, user logs in via browser |
| Token (READ) | `https://huggingface.co/mcp` | `Authorization: "Bearer ${HF_TOKEN}"` | Automation, CI, headless |

### Hermes config (token mode)

```yaml
mcp_servers:
  huggingface:
    url: "https://huggingface.co/mcp"
    headers:
      Authorization: "Bearer ${HF_TOKEN}"
    timeout: 180
    connect_timeout: 60
```

**Notes:**
- `${HF_TOKEN}` resolves from environment (shell env or ~/.hermes/.env)
- Token must have READ scope (created at https://huggingface.co/settings/tokens)
- OAuth mode (`?login`) triggers interactive prompt — not suitable for `hermes mcp add` pipe flow
- For token mode, write directly to config.yaml (Python yaml) to avoid the dual-prompt trap

### Tools exposed

- Model/Dataset/Space search and metadata
- Repository filesystem operations
- Gradio Space tool proxy (dynamic Spaces)
- Inference endpoints

## Civitai Orchestration

Already documented in config.yaml pattern:
```yaml
mcp_servers:
  civitai-orchestration:
    url: "https://orchestration.civitai.com/mcp"
    headers:
      Authorization: "Bearer ${CIVITAI_API_KEY}"
```

## Composio

```yaml
mcp_servers:
  composio:
    url: "https://connect.composio.dev/mcp"
    headers:
      Authorization: "Bearer ${COMPOSIO_API_KEY}"
```

## Pattern: HTTP server with Bearer token

For any MCP server using `Authorization: Bearer <token>`:

1. Store token in `~/.hermes/.env` as `SERVICE_API_KEY=value`
2. Reference in config.yaml headers as `Authorization: "Bearer ${SERVICE_API_KEY}"`
3. Write via Python yaml (not `hermes mcp add`) to avoid interactive prompts
4. Verify with `hermes mcp test <name>`
5. Inform user of pending gateway restart
