# opencode (original content — absorbed into acp-coding-agents)

OpenCode CLI skill for ACP transport delegation. Covers: installation (`npm install -g opencode`, or from source), delegate_task pattern with `acp_command="opencode"`, configuration (OPENCODE_API_KEY, OPENCODE_MODEL, opencode.config.json), and file-level permission prompting.

## Key preserved patterns

- `delegate_task(goal=..., acp_command="opencode", acp_args=["--acp", "--stdio"])`
- `opencode --acp --stdio` direct invocation
- Config: OPENCODE_API_KEY, OPENCODE_MODEL, opencode.config.json
- Custom provider config for non-OpenAI backends
