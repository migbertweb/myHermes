---
name: obsidian
description: Read, search, create, and edit notes in the Obsidian vault.
platforms: [linux, macos, windows]
---

# Obsidian Vault

Use this skill for filesystem-first Obsidian vault work: reading notes, listing notes, searching note files, creating notes, appending content, adding wikilinks, and setting up vaults from scratch.

A vault is just a directory of markdown files with a `.obsidian/` config folder. The Obsidian GUI app is NOT required — the agent can read and write vault content on any machine with file access. Install the GUI only when the user wants visual editing on a specific device.

## Vault path

Use a known or resolved vault path before calling file tools.

The documented vault-path convention is the `OBSIDIAN_VAULT_PATH` environment variable, for example from `~/.hermes/.env`. If it is unset, use `~/Documents/Obsidian Vault`.

File tools do not expand shell variables. Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to `read_file`, `write_file`, `patch`, or `search_files`; resolve the vault path first and pass a concrete absolute path. Vault paths may contain spaces, which is another reason to prefer file tools over shell commands.

If the vault path is unknown, `terminal` is acceptable for resolving `OBSIDIAN_VAULT_PATH` or checking whether the fallback path exists. Once the path is known, switch back to file tools.

## Vault setup from scratch

Creating a new vault requires only a directory with `.obsidian/` config files and a `NOTES.md` or `index.md`. The Obsidian app is NOT needed — the vault works as plain markdown.

### Required files in `.obsidian/`

- **`obsidian.json`** — vault identity (name, path)
- **`app.json`** — editor preferences (attachment path, link mode)
- **`core-plugins.json`** — enabled built-in plugins (file-explorer, graph, backlink, daily-notes, etc.)

### Recommended folder structure

```
vaults/principal/
├── index.md              ← landing page / bienvenida
├── Diario/               ← daily notes
├── Proyectos/            ← project notes
├── Notas/                ← general reference notes
├── assets/               ← images and attachments
└── .obsidian/            ← Obsidian config (hidden)
    ├── obsidian.json
    ├── app.json
    └── core-plugins.json
```

### Creating vault config files

Use `write_file` (not heredocs) to create `.obsidian/` configs — these are JSON files and the agent's syntax checker validates them.

Example `obsidian.json`:
```json
{ "vault": { "name": "Bóveda Principal", "path": "/home/user/vaults/principal" } }
```

Example `core-plugins.json`:
```json
["file-explorer", "global-search", "switcher", "graph", "backlink", "canvas", "outgoing-link", "tag-pane", "page-preview", "daily-notes", "templates", "note-composer", "command-palette", "editor-status", "bookmarks", "outline", "word-count", "file-recovery"]
```

Example `app.json`:
```json
{ "promptDelete": false, "alwaysUpdateLinks": true, "newFileLocation": "folder", "attachmentFolderPath": "assets", "useMarkdownLinks": true, "spellcheck": true }
```

## Multi-device setup (server ↔ laptop)

> **Reference:** `references/syncthing-cli-versions.md` has the full v1.x vs v2.x CLI differences.

### Architecture pattern
- **Server** hosts the canonical vault directory (Ubuntu, headless)
- **Laptop** accesses the same files via sync (Syncthing) and optional Obsidian GUI
- **Agent** writes/reads directly to the server's vault via file tools or SSH

### Syncthing integration
1. Create the vault directory on the server first
2. Add a folder in Syncthing (`sendreceive` type) pointing to the vault
3. Add both devices (server + laptop) to the folder
4. On the laptop, Syncthing auto-creates the folder entry — set the local path to match (e.g. `~/vaults/principal`)
5. Syncthing requires a `.stfolder` marker; the first device creates it automatically

### Syncthing CLI commands (v1.x — server)
```bash
syncthing cli config folders add --id my-vault --label "My Vault" --path /home/user/vaults/principal
syncthing cli config folders my-vault devices add --device-id=LAPTOP_DEVICE_ID
```

### Syncthing CLI commands (v2.x — laptop)
```bash
syncthing cli config folders my-vault path set "/home/laptop-user/vaults/principal"
```

### REST API (both versions, for rescan/override)

Find the API key first — the config directory differs by Syncthing version:
- **v1.x** (Ubuntu): `~/.config/syncthing/config.xml`
- **v2.x** (Arch): `~/.local/state/syncthing/config.xml`

```bash
# Get API key (adjust path for version)
APIKEY=*** -oP 'apikey="\K[^"]+' ~/.config/syncthing/config.xml)

# Rescan a folder
curl -s -X POST -H "X-API-Key: $APIKEY" "http://127.0.0.1:8384/rest/db/scan?folder=FOLDER_ID"

# Check folder status
curl -s -H "X-API-Key: $APIKEY" "http://127.0.0.1:8384/rest/db/status?folder=FOLDER_ID"

# Override — force local to match remote (use when sync conflict wiped files)
curl -s -X POST -H "X-API-Key: $APIKEY" "http://127.0.0.1:8384/rest/db/override?folder=FOLDER_ID"
```

**v2.x CLI path set** — use positional arg, not flag:
```bash
syncthing cli config folders my-vault path set "/home/laptop-user/vaults/principal"
```

## Read a note

Use `read_file` with the resolved absolute path to the note. Prefer this over `cat` because it provides line numbers and pagination.

## List notes

Use `search_files` with `target: "files"` and the resolved vault path. Prefer this over `find` or `ls`.

- To list all markdown notes, use `pattern: "*.md"` under the vault path.
- To list a subfolder, search under that subfolder's absolute path.

## Search

Use `search_files` for both filename and content searches. Prefer this over `grep`, `find`, or `ls`.

- For filenames, use `search_files` with `target: "files"` and a filename `pattern`.
- For note contents, use `search_files` with `target: "content"`, the content regex as `pattern`, and `file_glob: "*.md"` when you want to restrict matches to markdown notes.

## Create a note

Use `write_file` with the resolved absolute path and the full markdown content. Prefer this over shell heredocs or `echo` because it avoids shell quoting issues and returns structured results.

### Creating bookmarks / web references

When the user shares a URL (Reddit, article, tweet, etc.) and asks to save it to the vault:

1. **Attempt to fetch the content** — use `terminal` with `curl` or `browser_navigate` to retrieve the page. Try multiple endpoints if the primary one is blocked (JSON API, older subdomains, text-only proxies, Wayback Machine, Google cache).

2. **If content is accessible:** extract a meaningful summary, the title, and key metadata. Save as a note with frontmatter:
   ```markdown
   ---
   tags: [source-tag, bookmark]
   source: <original-url>
   ---
   
   # <Title>
   
   - **Source:** <link>
   - **Date saved:** YYYY-MM-DD
   
   <extracted summary or content>
   ```

3. **If content is blocked/inaccessible** (Reddit JS challenge, Cloudflare, login wall, etc.): save a **bookmark note** with whatever metadata is extractable from the URL itself:
   ```markdown
   ---
   tags: [source-tag, bookmark, pendiente]
   source: <original-url>
   ---
   
   # <Source> — <Context>
   
   - **URL:** <original-url>
   - **Date saved:** YYYY-MM-DD
   
   > ⚠️ **Nota:** El contenido no pudo ser recuperado automáticamente (<brief reason, e.g. "Reddit bloqueó las solicitudes desde el servidor">). Abrir manualmente en el navegador para ver el contenido.
   ```

   Extract what metadata you can from the URL (subreddit, post ID, comment ID, domain, path). Save in the `Recursos/` or `Notas/` subfolder.

4. **Frontmatter conventions:**
   - `tags`: always include `bookmark` plus a source-specific tag (e.g. `reddit`, `youtube`, `article`). Add `pendiente` when content couldn't be fetched.
   - `source`: the original URL as a string — this lets Obsidian's search and Dataview plugins use it.
   - `created`: optional YYYY-MM-DD date (file mtime is an alternative).

5. **Placement:** save bookmarks under `Recursos/` or a dedicated `Bookmarks/` folder, named `Source-topic.md` (e.g. `Reddit-niri-comentario.md`).

## Append to a note

Prefer a native file-tool workflow when it is not awkward:

- Read the target note with `read_file`.
- Use `patch` for an anchored append when there is stable context, such as adding a section after an existing heading or appending before a known trailing block.
- Use `write_file` when rewriting the whole note is clearer than constructing a fragile patch.

For an anchored append with `patch`, replace the anchor with the anchor plus the new content.

For a simple append with no stable context, `terminal` is acceptable if it is the clearest safe option.

## Targeted edits

Use `patch` for focused note changes when the current content gives you stable context. Prefer this over shell text rewriting.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.

## Pitfalls

### Sync conflicts wipe files
When a folder is added to Syncthing on both sides with different content (e.g. empty dir on laptop, populated dir on server), Syncthing may decide the empty side "wins" and delete the server's files. The server shows `find ~/vaults/principal -type f` returning nothing, or `globalDeleted` matching the expected file count.

**Recovery:** Recreate the vault files on the server, then use the Syncthing REST API override on the laptop:
```bash
curl -s -X POST -H "X-API-Key: $(grep -oP 'apikey=\"\K[^\"]+' ~/.config/syncthing/config.xml)" "http://127.0.0.1:8384/rest/db/override?folder=obsidian-vault"
```
This forces the laptop to accept the server's state as truth. Alternatively, set the laptop folder to `receiveonly` temporarily.

### Don't assume user has Obsidian GUI
The vault is just markdown files — the Obsidian app is optional. Check before suggesting the user open it. If they want GUI access, offer to install it (AUR on Arch/CachyOS: `obsidian-bin`).

### Vault path may differ between devices
The server and laptop may have different paths for the same vault (e.g. server: `/home/piro/vaults/principal`, laptop: `/home/migbert/vaults/principal`). Set `OBSIDIAN_VAULT_PATH` separately on each machine's `~/.hermes/.env`.

### JSON quotes in SSH heredocs
When creating `.obsidian/*.json` files via SSH, be careful with quote escaping. Use `write_file` via file tools instead of SSH heredocs when possible — the agent's JSON validator catches mistakes.
