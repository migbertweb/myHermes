# Installing Hermes Plugins (`hermes plugins install`) — worked example: superpowers

Session detail (2026-08-18): installing `obra/superpowers` as a Hermes plugin.

## The scanner wall

`hermes plugins install obra/superpowers --enable` was blocked at clone time:

```
Blocked: Security scan blocked plugin install: Blocked (dangerous verdict, 213 findings).
--force does not override a dangerous verdict.
```

The 213 findings were false positives on a big skill-framework repo (274k stars, docs+tests heavy):

- `CRITICAL persistence` — any mention of `CLAUDE.md` / `AGENTS.md` in docs and design plans (the framework's own concept)
- `CRITICAL credential_exposure` — fake test tokens (`testtoken-0123…`, `abababab…`) in `tests/brainstorm-server/*.test.js`
- `CRITICAL destructive` — one `rm -rf /tmp/brainstorm-smoke` inside a design doc
- `CRITICAL exfiltration` / `HIGH` — `os.environ` reads in spec docs, "output never enters your own context" phrases
- `MEDIUM supply_chain` / `traversal` — `uv run pytest`, `npm install` mentions, `path.join(__dirname, …)` in tests

Pattern: heuristics fire on *any* repo that mentions agent-instruction files, holds test fixtures, or documents shell commands. Large multi-harness plugin repos will almost always trip this.

## The only way through (user-approved)

```bash
hermes config set plugins.scan_on_install false
hermes plugins install obra/superpowers --enable
hermes config set plugins.scan_on_install true
```

`--force` (reinstall) does NOT bypass a DANGEROUS verdict. Present the findings summary to the user and get explicit approval before toggling.

## Per-profile propagation

Each profile has its own config (`plugins.enabled`) AND its own plugin code dir
(`~/.hermes/profiles/<p>/plugins/<name>/`). Installing without `-p` only touches default.

```bash
for p in coder-back coder-front devops-chief; do
  hermes -p $p config set plugins.scan_on_install false && \
  hermes -p $p plugins install obra/superpowers --enable && \
  hermes -p $p config set plugins.scan_on_install true
done
```

Verify per profile: `hermes -p $p plugins list | grep superpowers` → source column shows `user` when enabled.

## Warning that is NOT a failure

```
Warning: superpowers doesn't contain plugin.yaml, plugin.json, or __init__.py.
It may not be a valid Hermes plugin.
```

The manifest lives under `.hermes-plugin/plugin.yaml` (superpowers layout):

```
.hermes-plugin/plugin.yaml   # name, version, provides_hooks: [pre_llm_call]
.hermes-plugin/__init__.py   # resolves ../skills, injects using-superpowers bootstrap
skills/<14 skills>/SKILL.md  # the actual payload
```

Install succeeded and `hermes plugins list` showed `superpowers | enabled | 6.3.0 | user`.

## Activation caveats

- Plugin hooks (pre_llm_call) load at session/gateway start — active sessions/gateways need restart.
- Superpowers README: Hermes has no post-compaction hook; a very long session that compacts over its first turn loses the bootstrap → start a fresh session if skills stop triggering.
- Bootstrap test: "Let's make a react todo list" should auto-trigger `brainstorming` before any code.
