---
name: acp-coding-agents
description: >-
  Umbrella skill for ACP-compatible coding agent CLIs: Claude Code, Codex,
  and OpenCode. Each agent uses the --acp --stdio transport protocol for
  Hermes subagent delegation. Absorbs the former claude-code, codex, and
  opencode skills.
version: 1.0.0
author: Hermes Agent (merged from 3 absorbed skills)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [acp, agents, claude-code, codex, opencode, coding-agent, delegation, ACP-CLI]
    supersedes:
      - claude-code
      - codex
      - opencode
---

# ACP Coding Agents (Umbrella)

Delegate coding tasks to ACP-compatible CLI agents via the `--acp --stdio`
transport protocol. This skill replaces three former narrow skills (claude-code,
codex, opencode). Each agent type is documented in a subsection below.

## When to Use

- User explicitly mentions "Claude Code", "Codex CLI", or "OpenCode"
- User wants to delegate a feature implementation or bug fix to an external
  coding agent
- The task benefits from a dedicated agent with its own context window

## Common Protocol

All three agents share the ACP (Agent Communication Protocol) transport:

```
--acp --stdio
```

Use via `delegate_task`:

```python
delegate_task(
    goal="Implement feature X",
    context="Relevant background...",
    acp_command="claude",
    acp_args=["--acp", "--stdio"],
)
```

---

## 1. Claude Code

> **Legacy reference:** `references/claude-code-original.md`

The Claude Code CLI (`claude`) accepts structured tasks and returns results
via ACP transport.

### Installation

```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Verify
claude --version
```

### Usage via delegate_task

```python
delegate_task(
    goal="Add user authentication module",
    context="Project at /path/to/project with Flask...",
    acp_command="claude",
    acp_args=["--acp", "--stdio"],
)
```

### CLI Script Approach

For direct invocation, save as a script:

```bash
#!/bin/bash
claude "$@" --acp --stdio
```

### Best Practices

- Provide full project context (file paths, error messages, constraints)
- Set explicit acceptance criteria so Claude knows when it's done
- Request verification steps (tests, linting) in the goal
- Claude Code can read/write files, run commands, and create PRs

---

## 2. Codex CLI

> **Legacy reference:** `references/codex-original.md`

OpenAI's Codex CLI (`codex`) is a terminal-based coding agent.

### Installation

```bash
# Install Codex CLI
npm install -g @openai/codex

# Verify
codex --version
```

### Usage via delegate_task

```python
delegate_task(
    goal="Refactor the API layer",
    context="FastAPI app at /path/to/project...",
    acp_command="codex",
    acp_args=["--acp", "--stdio"],
)
```

### Configuration

Codex CLI can be configured via environment variables or a config file:

- `CODEX_API_KEY` — OpenAI API key (required)
- `CODEX_MODEL` — Model override (default: gpt-4o)
- `CODEX_MAX_TOKENS` — Max tokens per response

---

## 3. OpenCode CLI

> **Legacy reference:** `references/opencode-original.md`

OpenCode (`opencode`) is an open-source coding agent CLI.

### Installation

```bash
# Install OpenCode
npm install -g opencode

# Or from source
git clone https://github.com/sst/opencode
cd opencode
npm install && npm run build
npm link

# Verify
opencode --version
```

### Usage via delegate_task

```python
delegate_task(
    goal="Create a REST API endpoint",
    context="Hono app at /path/to/project...",
    acp_command="opencode",
    acp_args=["--acp", "--stdio"],
)
```

### Configuration

OpenCode supports:

- `OPENCODE_API_KEY` — API key
- `OPENCODE_MODEL` — Model selection
- Custom provider config via `opencode.config.json`
- File-level permission prompts for safety

### Using Hermes API Server as LLM backend

OpenCode can use Hermes' OpenAI-compatible API server (`/v1/chat/completions`)
as its LLM provider, instead of delegating via ACP. Configure OpenCode to
point at the Hermes API server:

```json
{
  "provider": "openai",
  "apiBase": "http://192.168.1.8:8642/v1",
  "apiKey": "your-api-server-key"
}
```

Or via environment:
```bash
export OPENCODE_API_KEY="your-api-server-key"
export OPENCODE_API_BASE="http://192.168.1.8:8642/v1"
```

#### Known issue: custom SSE events break streaming

When `stream: true`, Hermes API server emits custom `hermes.tool.progress`
SSE events alongside standard OpenAI chunks. These contain tool metadata
(`tool`, `emoji`, `label`, `toolCallId`, `status`) that OpenAI-compatible
clients like OpenCode cannot parse — the client's schema validation fails
because the payload lacks the expected `choices` array:

```
Type validation failed: Value: {"tool":"browser_navigate","emoji":"🌐",
  "label":"https://opencode.ai","toolCallId":"call_...","status":"running"}
```

**Fix:** set `tool_progress` to `off` for the `api_server` platform in
`~/.hermes/config.yaml`. Two conditions must be met:

1. **Config entry** — merge into the existing `display.platforms` block
   (NOT a separate standalone `platforms:` — YAML overwrites duplicate
   keys, so a second top-level `platforms:` will wipe the first).

   ```yaml
   display:
     platforms:
       # ... existing platforms (telegram, discord, etc.)
       api_server:
         tool_progress: off
   ```

2. **Code support** — the streaming code in
   `gateway/platforms/api_server.py` must check `resolve_display_setting`
   before wiring up the tool-progress callbacks. Versions before the
   upstream fix need a manual patch (see
   `references/opencode-api-server.md` for the full patch).

Once both conditions are satisfied, Hermes stops emitting custom SSE
events on the `/v1/chat/completions` streaming endpoint. The standard
text delta stream continues working normally. Frontends that support the
custom events (e.g. Open WebUI) can opt in per-platform via
`tool_progress: all`.

See `references/opencode-api-server.md` for reproduction details and
debugging steps.

---

## Kanban Integration

The `kanban-codex-lane` skill (also archived and absorbed into the `kanban`
umbrella) provides patterns for running Codex CLI from Kanban worker tasks.
See the `kanban` skill for details.
