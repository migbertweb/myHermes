# codex (original content — absorbed into acp-coding-agents)

OpenAI Codex CLI skill for ACP transport delegation. Covers: installation (`npm install -g @openai/codex`), delegate_task pattern with `acp_command="codex"`, configuration via CODEX_API_KEY/CODEX_MODEL/CODEX_MAX_TOKENS environment variables.

## Key preserved patterns

- `delegate_task(goal=..., acp_command="codex", acp_args=["--acp", "--stdio"])`
- `codex --acp --stdio` direct invocation
- Config: CODEX_API_KEY, CODEX_MODEL, CODEX_MAX_TOKENS
