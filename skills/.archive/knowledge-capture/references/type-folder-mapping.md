# Type-to-folder mapping — Migbert's vault

Vault path: `/home/migbert/vaults/principal`

| Type | Folder | Content |
|------|--------|---------|
| `recurso` | `Recursos/` | Bookmarks, articles, tools, links, external references |
| `nota` | `Notas/` | Ideas, concepts, standalone learnings |
| `proyecto` | `Proyectos/` | Active project notes, decisions, specs |
| `diario` | `Diario/` | Daily entries, session summaries |
| `linux` | `Linux/` | Linux-specific technical notes |
| `youtube` | `YouTube/` | Video scripts, outlines, ideas |

## Other vault folders

- `assets/` — attachments/images (not a note target)
- `index.md` — landing page (not a note target)

## Vault path resolution

Set in `~/.hermes/.env` as `OBSIDIAN_VAULT_PATH`. If unreadable, fall back to the obsidian skill's default search.
