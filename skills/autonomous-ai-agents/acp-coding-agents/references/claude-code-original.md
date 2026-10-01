# claude-code (original content — absorbed into acp-coding-agents)

Claude Code CLI skill for ACP transport delegation. Covers: installation (`npm install -g @anthropic-ai/claude-code`), delegate_task pattern with `acp_command="claude"`, best practices for context/gpal/acceptance-criteria, and CLI script approaches. The full original 36KB SKILL.md included exhaustive command reference, environment setup, and troubleshooting guides — all now canonical under `acp-coding-agents` with the Claude Code section preserving the key workflows.

## Key preserved patterns

- `delegate_task(goal=..., acp_command="claude", acp_args=["--acp", "--stdio"])`
- `claude --acp --stdio` direct invocation
- Best practices: provide project context, set acceptance criteria, request verification steps
