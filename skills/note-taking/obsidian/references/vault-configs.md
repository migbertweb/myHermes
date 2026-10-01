# Obsidian Vault Configuration Files

Reference configs for initializing a new Obsidian vault from scratch.
Copy these when creating a vault on a remote server or new device.

## Directory structure

```
vaults/<vault-name>/
├── index.md
├── Diario/
├── Proyectos/
├── Notas/
├── assets/
└── .obsidian/
    ├── obsidian.json
    ├── app.json
    └── core-plugins.json
```

## obsidian.json

```json
{
  "vault": {
    "name": "Bóveda Principal",
    "path": "/home/user/vaults/principal"
  }
}
```

## app.json

```json
{
  "promptDelete": false,
  "alwaysUpdateLinks": true,
  "newFileLocation": "folder",
  "newFileFolderPath": "",
  "attachmentFolderPath": "assets",
  "useMarkdownLinks": true,
  "showUnsupportedFiles": true,
  "spellcheck": true
}
```

## core-plugins.json

```json
[
  "file-explorer",
  "global-search",
  "switcher",
  "graph",
  "backlink",
  "canvas",
  "outgoing-link",
  "tag-pane",
  "page-preview",
  "daily-notes",
  "templates",
  "note-composer",
  "command-palette",
  "editor-status",
  "bookmarks",
  "outline",
  "word-count",
  "file-recovery"
]
```

## index.md template

```markdown
---
created: YYYY-MM-DD
tags: [meta, bienvenida]
---

# 🏠 Bóveda Principal

## 📂 Estructura

- **Diario/** — Notas diarias
- **Proyectos/** — Notas de proyectos
- **Notas/** — Notas generales
- **assets/** — Adjuntos

---

*Sincronizada vía Syncthing*
```
