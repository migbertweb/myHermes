---
name: freelance-proposal-archive
description: Archive freelance proposals into Obsidian vault.
---

# Freelance Proposal Archive (Obsidian)

Layer that persists a freelance job post + analysis + proposal into the Obsidian vault following the user's 99frelas structure. Complements the (immutable, hub) `freelance-proposal-engine` skill, which handles proposal *writing*; this one handles *archiving*.

## Trigger

- "crea en obsidian una carpeta ... y agrega allí los recursos, el proyecto y la propuesta"
- Any request to save a job post / proposal analysis into the vault

## Environment facts

- Vault: `/home/migbert/vaults/principal` (from `OBSIDIAN_VAULT_PATH` in `~/.hermes/.env`)
- Source of job posts + attachments: `~/proyectos/Freelancer/99frelas/propostas/<post title>/`
- Chat attachments referenced as `file_0000...` are often NOT readable from chat — copy them from the source dir above (matched by original name, e.g. `img-20260619-wa0007.jpg`)

## Workflow

### 1. Locate source files

- If attachments are referenced but not found locally, search `~/proyectos/Freelancer/99frelas/propostas/` for the post folder (`search_files` target=files).
- Inspect **every** image with `vision_analyze`. Common split: one image is just the logo, another holds the real UI template/mockup. Embed the template description (layout, KPIs, palette) into the Proyecto note — it anchors the dashboard design for the proposal.

### 2. Create the vault folder

`<vault>/Freelancer/99frelas/propostas/<post title>/` — keep the exact post title, accents included (UTF-8 fine on Linux).

### 3. Copy resources

- `Recursos/` subfolder.
- Rename hash filenames (`file_0000004b...png`, `img-...jpg`) to descriptive names (`logo-ds.jpg`, `benchia-template-dashboard.png`).
- `terminal cp` is fine for binaries (paths contain spaces/accents — quote them).

### 4. Write the notes (3 files, cross-linked with wikilinks)

**Index** `<post title>.md`
- frontmatter: `tags: [freelance, propuesta, <platform>, ...]`, `estado`, `cliente`, `fecha`, `fuente` (source dir path)
- wikilinks to `[[<Short>-Proyecto]]` and `[[<Short>-Propuesta]]`
- Recursos section with `[[Recursos/<file>]]` links
- Estado checklist (análise/proposta/enviar/call) + Pendências con el cliente

**`<Short>-Proyecto.md`**
- frontmatter + backlink to index
- Descripción del post original
- Template/dashboard description (from image analysis)
- Análisis de ejecución: veredicto, alcance por módulo (tabla), arquitectura (ASCII), stack opinado (tabla con "por qué"), decisiones clave, fases + precio (tablas), riesgos (tabla), preguntas abiertas

**`<Short>-Propuesta.md`**
- frontmatter + backlink; note character count
- Proposal ready to paste (PT-BR for Brazilian clients) + follow-up message template (48h)

Skeletons: `templates/obsidian-proposal-structure.md`.

### 5. Naming convention

Short prefix = project short name (`BenchIA` → `BenchIA-Proyecto.md`, `BenchIA-Propuesta.md`). Wikilinks by short name stay unique vault-wide; avoid generic names like `Proyecto.md` (collision risk).

## Proposal conventions (Brazilian market)

- PT-BR, gíria paulistana moderada (sutake, trampo, de boa, fechou) — details in memory
- Body ≤3000 chars; structure: hook + entregables + cronograma + proceso + CTA + precio R$
- Milestone payments: 20% entrada / 40% meio / 40% entrega
- Close with 3 clarifying questions + offer a 20-min call
- Follow-up template lives inside the Propuesta note

## Pitfalls

- Don't trust chat attachment paths; resolve from the 99frelas source dir first.
- First image may be logo-only — do not conclude "no template" until every attachment has been checked.
- Keep post-title accents in folder names; quote paths in shell commands.
- `freelance-proposal-engine` is a hub skill and immutable — never edit it; add user-specific layers as separate skills (this one).

## Support files

- `templates/obsidian-proposal-structure.md` — note skeletons for index / proyecto / propuesta
