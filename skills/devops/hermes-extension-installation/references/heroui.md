# Worked example: HeroUI react MCP + skill (2026-08-09)

Session-proven install of HeroUI v3 tooling across 3 Hermes profiles (default, devops-chief, coder-front) on laptop CachyOS.

## MCP server (@heroui/react-mcp)

Source: https://heroui.com/en/docs/react/getting-started/mcp-server
Package: `@heroui/react-mcp@latest` (npm), stdio via npx. Requires Node ≥22 (machine had v26.4.0).

```bash
# default profile (prompt auto-answers; pty ALONE cancels — must pipe Y)
printf 'Y\n' | hermes mcp add heroui-react --command npx --args -y @heroui/react-mcp@latest

# per-profile: flag BEFORE subcommand
printf 'Y\n' | hermes -p devops-chief mcp add heroui-react --command npx --args -y @heroui/react-mcp@latest
printf 'Y\n' | hermes -p coder-front  mcp add heroui-react --command npx --args -y @heroui/react-mcp@latest
```

Result: 6 tools discovered (`list_components`, `get_component_docs`, `get_component_source_code`, `get_component_source_styles`, `get_theme_variables`, `get_docs`), all enabled. Config key: `mcp_servers.heroui-react` with `command: npx`, `args: [-y, '@heroui/react-mcp@latest']`, `enabled: true`.

Verify: `hermes mcp list`, `hermes mcp test heroui-react` (first connect ~11s while npx downloads; then cached).

## Agent Skill (heroui-react v3.0.1)

Source: https://heroui.com/en/docs/react/getting-started/agent-skills
Official installer `curl -fsSL https://heroui.com/install | bash -s heroui-react` targets ONLY Claude Code / Cursor / OpenCode / Codex / Antigravity (checks `~/.claude`, `~/.cursor`, `~/.config/opencode`, `$HOME/.codex`, `$HOME/.gemini`) → "No supported tools detected" on Hermes.

Reading the installer script reveals the real payload URL: `https://heroui.com/skills/heroui-react.tar.gz`.

```bash
cd /tmp && curl -fsSL -o heroui-react.tar.gz https://heroui.com/skills/heroui-react.tar.gz
tar tzf heroui-react.tar.gz   # SKILL.md, LICENSE.txt (Apache-2.0), scripts/*.mjs (6 scripts)
# NOTE: bare extract in /tmp errors with "utime: Operación no permitida" — extract into a subdir:
mkdir -p heroui-skill && tar xzf heroui-react.tar.gz -C heroui-skill
```

Layout: `SKILL.md` (frontmatter: name `heroui-react`, description, metadata.author `heroui`, metadata.version `3.0.1`), `LICENSE.txt`, `scripts/{list_components,get_component_docs,get_docs,get_source,get_styles,get_theme}.mjs`.

Install (copy tree, don't extract directly into the skills dir):

```bash
mkdir -p ~/.hermes/skills/heroui-react
cp -r /tmp/heroui-skill/SKILL.md /tmp/heroui-skill/LICENSE.txt /tmp/heroui-skill/scripts ~/.hermes/skills/heroui-react/

# per-profile
for P in devops-chief coder-front; do
  mkdir -p ~/.hermes/profiles/$P/skills/heroui-react
  cp -r ~/.hermes/skills/heroui-react/SKILL.md ~/.hermes/skills/heroui-react/LICENSE.txt \
        ~/.hermes/skills/heroui-react/scripts ~/.hermes/profiles/$P/skills/heroui-react/
done
```

Verify: `hermes skills list | grep -i heroui` (or `hermes -p PROFILE skills list`) → `enabled`.

## Notes

- Skill is auto-discovered (no /reload-skills needed for future sessions; current session needs reload).
- MCP tools only load on new session / gateway restart — user deferred the gateway restarts; config was verified live via `hermes mcp test` instead.
- Backup before touching per-profile config.yaml: `cp ~/.hermes/profiles/<P>/config.yaml ~/.hermes/profiles/<P>/config.yaml.bak.$(date +%Y%m%d_%H%M%S)`.
