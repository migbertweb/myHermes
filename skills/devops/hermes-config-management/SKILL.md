---
name: hermes-config-management
description: Procedures for auditing, restoring, and modifying Hermes Agent configuration files.
---

# Hermes Config Management

Guidelines for safely managing the `config.yaml` and related settings to prevent data loss and maintain structural integrity.

## Workflow

1. **Audit**: Use `read_file` and `terminal` checks to verify current state before modification.
2. **Backup**: While Hermes performs automatic backups, manually noting critical blocks before a `yaml.dump` is recommended.
3. **Modification**: 
   - For targeted changes, use `patch`.
   - For complex structural changes (like MoA presets), use a Python script with `yaml.safe_load` and `yaml.dump` to ensure valid syntax.
4. **Verification**: Always run a syntax check (`python3 -c "import yaml; yaml.safe_load(open('...'))"`) after writing to the config.

## Linked reference files

- `references/python-deps.md` — Installing Python dependencies for Hermes skills on Arch/CachyOS (system pip is externally managed; use the Hermes venv pip instead).

## Pitfalls & Lessons

- **custom_providers catalog is informational**: `custom_providers[0].models` is a dump of everything the provider (e.g. OmniRoute) exposes, used only by the model picker. It is NOT validation — model names NOT in the list (`combo-coding`, `deepseek-v4-*`, MoA refs without prefix) still resolve fine because the router maps them internally. Safe to prune to only referenced models. To find what's actually referenced, strip the `custom_providers:` block from the raw text and grep for model-ish tokens. Surgical edit: replace only the `    models:` block lines (between `    models:` and `    name: <provider>`), keeping everything else byte-identical — avoids `yaml.dump` reformatting the whole 1700+ line file. Verify afterwards with `yaml.safe_load` and by checking every `provider/model` reference in the remaining text is covered.
- **YAML Comment Loss**: `yaml.dump` (and most YAML libraries) does not preserve comments. If the config contains important documentation comments, avoid full-file rewrites; use targeted `patch` calls or preserve the comments in a separate reference file.
- **Formatting Shifts**: `yaml.dump` may change the style of lists (e.g., from block to flow style) or indentation. This is semantically correct but may look different to the user.
- **Sync Conflicts**: In synced environments, `.sync-conflict-*.json` files can accumulate in `~/.hermes/` and `~/.hermes/cron/`. These should be cleaned up to avoid confusion.

## Verification Steps
- [ ] Run `python3 -c "import yaml; yaml.safe_load(open('path/to/config.yaml'))"` to ensure the file is not corrupted.
- [ ] Verify specific keys (e.g., `moa.presets.default`) via `read_file` or a Python probe.
