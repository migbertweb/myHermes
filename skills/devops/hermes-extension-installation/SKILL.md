---
name: hermes-extension-installation
description: "Install third-party MCP servers and Agent Skills in Hermes."
category: devops
---

# Installing MCP Servers & Agent Skills into Hermes

Two ways to extend Hermes with third-party packages: **MCP servers** (tools, config-driven) and **Agent Skills** (filesystem SKILL.md folders). Covers both, including per-profile propagation.

## MCP Servers (`hermes mcp add`)

```bash
hermes mcp add NAME --command npx --args -y @scope/pkg@latest
```

- **Interactive "Enable all N tools?" prompt: pipe the answer.** `printf 'Y\n' | hermes mcp add ...` — PTY mode alone still cancels; the prompt needs stdin. `select` lets you pick a subset.
- Verify: `hermes mcp list`, then `hermes mcp test NAME` (first run is slow, ~11s — npx downloads the package; cached afterwards).
- Requires Node for npx servers; check `node --version` first — some servers mandate a minimum (e.g. HeroUI needs ≥22).
- New session needed to use tools (no hot-reload).

### Per-profile MCP

- Each profile has its own config.yaml: `~/.hermes/profiles/<name>/config.yaml`.
- Flag goes BEFORE the subcommand: `hermes -p PROFILE mcp add NAME --command ...`.
- Verify per-profile: `hermes -p PROFILE mcp list` / `hermes -p PROFILE mcp test NAME`.
- **Back up the profile config first** (cp to `config.yaml.bak.<ts>` — see config-backup-rotation for the default config; same rule applies per profile).
- Gateway restart required to load the MCP — the user may want to defer restarts; ask before restarting.

## Agent Skill packages (vendor installers that skip Hermes)

Many vendors ship `curl -fsSL https://site/install | bash -s skill-name` installers that only target Claude Code / Cursor / OpenCode / Codex / Antigravity (they check for `~/.claude`, `~/.cursor`, etc.) and bail with "No supported tools detected" on Hermes.

**Workaround — fetch the tarball directly:**

1. Read the installer script (`curl -fsSL https://site/install`) to find the tarball URL — pattern is usually `https://site/skills/<name>.tar.gz`.
2. Inspect: `curl -fsSL -o /tmp/<name>.tar.gz <url> && tar tzf /tmp/<name>.tar.gz`.
3. Extract into a scratch SUBDIR: `mkdir -p /tmp/scratch && tar xzf ... -C /tmp/scratch` — extracting bare into /tmp fails with utime errors on the `./` entry.
4. Validate SKILL.md frontmatter parses and has `name` + `description` (yaml.safe_load on the `---` block).
5. Install default profile: copy `SKILL.md`, `LICENSE.txt`, `scripts/` → `~/.hermes/skills/<name>/`.
6. Per-profile: copy the same tree → `~/.hermes/profiles/<name>/skills/<name>/`.
7. Verify: `hermes skills list | grep <name>` (or `hermes -p PROFILE skills list`).

Typical layout: `SKILL.md` + `LICENSE.txt` + `scripts/*.mjs`. Scripts may need Node — check `node --version` if the skill ships .mjs/.js scripts.

### Skill BUNDLES (repo con N skills interdependientes)

Algunos repos (ej. nextlevelbuilder/ui-ux-pro-max-skill) son bundles: `.claude/skills/<name>/SKILL.md` × N. Los skills se referencian entre sí (p.ej. `banner-design` usa `ui-ux-pro-max`), así que instalar solo el "principal" deja dependencias rotas → copiar TODOS los `SKILL.md` del bundle.

1. `tar tzf <tarball> | grep -E '\.claude/skills/[^/]+/SKILL\.md$'` → lista los N skills.
2. Validar frontmatter (`name` + `description`) de cada uno.
3. Bucle: `for d in ~/.hermes/skills ~/.hermes/profiles/*/skills; do cp -r "$SRC/$s" "$d/$s"; done` — chequear colisiones de nombre antes (`[ -d "$d/$s" ]`).
4. Verificar: `hermes skills list | grep <name>` por perfil. OJO: grep con regex de anclas falla en la tabla con nombres cortos — usar `grep -E '(^|\s)(name)(\s|│)'` o `grep name` simple.

### agentskills CLI (`npx skills add <owner>/<repo>`) — installs to CWD, symlinks only Claude Code

The agentskills ecosystem (remotion-dev/skills, coreyhaines31/marketingskills, etc.) installs via `npx skills add owner/repo [--skill name1 name2]`. Two gotchas:

1. **It writes to `./.agents/skills/` relative to the CURRENT working directory** — run it from the project dir and the skills land in `<project>/.agents/skills/`, NOT `~/.agents/skills/`. After install, move them: `mv .agents/skills/<name> ~/.agents/skills/`.
2. **It only symlinks to Claude Code** (`symlinked: Claude Code` in the output), never to Hermes. Create the Hermes symlink manually: `ln -sfn ../../.agents/skills/<name> ~/.hermes/skills/<name>` (same pattern the remotion install uses).
3. `--list` shows available skill names; `--skill a b c` installs a subset (installing all 50+ of a big repo pollutes the agent's skill index — prefer subsets).
4. The installer writes a `skills-lock.json` + `.agents/`/`.claude/` artifacts into the CWD — clean them up after moving.
5. Verify with `hermes skills list | grep <name>`; the skill becomes visible to the agent on the NEXT session (skill list loads at startup) but can be loaded on demand via `skill_view`.

## Pitfalls

- `hermes mcp add` in pty mode still cancels the enable prompt → always `printf 'Y\n' |`.
- `hermes skills install` also has an interactive confirmation prompt (`Confirm [y/N]:`) → pipe with `printf 'y\n' | hermes skills install ...` (lowercase y).
- Vendor `curl|bash` installers never detect Hermes → skip them entirely; go straight for the tarball URL revealed by reading the installer script.
- `hermes config set` cannot write nested `mcp_servers` structures → use `hermes mcp add` (it handles the YAML correctly).
- After editing profile configs, gateways keep running with the old config until restarted — tools stay registered but inactive.
- **Not every URL is a skill.** See `references/skill-evaluation.md` for the pre-install checklist — some repos are JS libs (e.g. defuddle) that Hermes already covers via a different backend, and installing them as skills adds nothing.
- **Skill bundles with many skills:** extract all SKILL.md folders from the tarball, loop copy to `~/.hermes/skills/` and all `~/.hermes/profiles/*/skills/`. Check collisions with `[ -d "$d/$s" ]` before copy.
- **Python CLI tools with bundled skills** (e.g. agent-reach): install CLI via `uv tool install <git-url>` first, then copy skills from extracted source. The CLI provides `doctor` command to verify platform readiness.
- **Collision handling:** if skill already exists in default profile, skip default but still copy to all profiles — the user's local overrides persist while profiles get the update.
- **Verify count after bulk install:** `ls ~/.hermes/skills/ | wc -l` and `hermes skills list | wc -l` to confirm all skills registered.

## Concrete Repo Examples

### karpathy-guidelines (multica-ai/andrej-karpathy-skills)

Repo con `skills/karpathy-guidelines/SKILL.md`. Skill real, 4 principios. Instalado: copiar a `~/.hermes/skills/` y perfiles. Verificar con `hermes skills list`.

### defuddle (kepano/defuddle)

Librería JS para extraer contenido principal como Markdown. NO es skill. Hermes ya usa `extract_backend=firecrawl` que hace lo mismo. No instalar. Si firecrawl falla, considerar MCP server de defuddle (requiere JS runtime + DOM).

### caveman-compress-mode

Ya está en `~/.hermes/skills/caveman-compress-mode`. Activar con `/ponytail lite` o `/caveman`. Para hacerlo permanente, agregar sección en `~/.hermes/SOUL.md` (backup primero).

### agent-skills (addyosmani/agent-skills)

Bundle de 25 skills de engineering en `skills/*/SKILL.md`. Instalado completo copiando todos los subdirectorios a `~/.hermes/skills/` y 6 perfiles. Incluye: `code-review-and-quality`, `test-driven-development`, `planning-and-task-breakdown`, `spec-driven-development`, `ci-cd-and-automation`, `security-and-hardening`, etc.

### marketingskills (coreyhaines31/marketingskills)

Bundle de 50 skills de marketing en `skills/*/SKILL.md`. Instalado completo. 8 skills ya existían localmente (`cold-email`, `content-strategy`, `copywriting`, `marketing-loops`, `marketing-psychology`, `prospecting`, `social`, `video`) — se actualizaron en perfiles, local mantuvo override del usuario.

### awesome-design-md (VoltAgent/awesome-design-md)

NO es skill — colección de archivos `DESIGN.md` de referencia para diseño de UI. No hay `SKILL.md` en el repo. No instalar como skill; usar copiando `DESIGN.md` al root del proyecto cuando se necesite.

## References

- `references/heroui.md` — worked example: HeroUI react MCP + skill installed across 3 profiles (exact commands).
- `references/skill-evaluation.md` — pre-install checklist: is it a skill, an MCP, or a lib Hermes already covers?
