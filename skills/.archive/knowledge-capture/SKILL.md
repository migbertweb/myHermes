---
name: knowledge-capture
description: Interactive conversational knowledge capture — ask before saving vault-worthy content with type mapping.
platforms: [linux, macos, windows]
---

# Knowledge Capture

Use this skill when vault-worthy content surfaces in conversation: decisions, ideas, resources, project notes, workflows, technical discoveries, or anything the user might want to persist.

**Never save silently.** Always ask first.

## Protocol

1. **Detect** — identify content that has durable value (not transient chat, not tool output noise).
2. **Offer** — ask concisely:
   > ¿Guardo? Tipo: `recurso`
3. **Confirm** — the user replies:
   - `"si"` → save with the suggested type
   - `"si <type>"` → save with overridden type
   - anything else / no response → do not save
4. **Save** — write the note with frontmatter and [[wikilinks]] where relevant.

## Type-to-folder mapping

This mapping must be discovered per user by inspecting their vault structure (folders under the vault root). The reference file `references/type-folder-mapping.md` documents one user's actual mapping as a concrete example.

Common conventions:
- `recurso` → external references, bookmarks
- `nota` → standalone ideas, concepts
- `proyecto` → active project notes
- `diario` → daily entries
- Plus any domain-specific folders (linux, youtube, recipes, etc.)

## Note format

Use write_file (never heredocs/echo) to create notes with standard frontmatter:

```markdown
---
tags: [type-tag]
created: YYYY-MM-DD
---

# Title

Content...
```

Include `[[wikilinks]]` to related notes when relevant.

## Interaction with Obsidian skill

The `obsidian` skill handles raw vault operations (read, search, path resolution, syncthing, etc.). This skill provides the **interactive decision layer** on top — when to ask, what to ask, and where to save based on user confirmation.

Load this skill in conjunction with the obsidian skill when the user has a vault they want you to populate interactively.

## Pitfalls

### Do not save without asking
Silent writes erode trust. Users want control over what enters their vault. Always ask, even if the content seems obviously valuable.

### Suggest a specific type
Don't ask an open-ended "what type?" — propose one type based on content analysis. The user can override if wrong.

### No response = no save
If the user doesn't answer the question (topic shifts, they ignore it), do not save. Don't circle back later unless the same content resurfaces naturally.
