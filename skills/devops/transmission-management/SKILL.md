---
name: transmission-management
description: Manage torrents using transmission-remote CLI, including magnet additions, directory management, tracker optimization, and remote host control via SSH.
---

# Transmission Management

## Media center: KODI (NOT Jellyfin)
As of 2026-08 the user's media center is **KODI**. Jellyfin is retired — do not assume Jellyfin features/scanning. Naming must follow Kodi conventions:
- Movies: one folder per movie named `Title (Year)/` containing `Title (Year).mkv` (kodi.wiki/view/Naming_video_files/Movies).
- Series: one folder per show `Title (Year)/`, episodes named `Title S01E01.mkv` (kodi.wiki/view/Naming_video_files/Episodes).
- Root-owned Jellyfin metadata files (`*.backdrop.jpg`, `folder.jpg`, `.trickplay/`, etc.) may still exist from the Jellyfin era; they are leftovers to clean, not to protect.

## Remote control via SSH
When transmission runs on another machine, do not depend on the remote web UI being open. Preferred pattern is local wrappers around SSH + transmission-remote.

### Recommended wrapper scripts
- `/home/migbert/.local/bin/remote_add_torrent.sh`: laptop-side wrapper that adds magnets/.torrent files to a remote host. NOTE: lives in `~/.local/bin`, NOT under this skill's `scripts/` (that dir does not exist here). Canonical usage docs live in the `media/torrent-download` skill (section "Remote laptop wrapper script").
- `references/laptop-remote-wrapper.md`: usage details and Hermes integration notes
- `references/laptop-ssh-usage.md` does NOT exist in this skill — the one-liners are in `media/torrent-download` (section "Laptop/remote usage via SSH"). Do not reference it from here.

Wrappers should:
- validate `movies|series|music`
- resolve remote `.torrent` URLs by `curl` on the server to `/tmp/<filename>` before adding
- quote remote arguments to avoid local shell expansion leaking through SSH
- print destination path, remote command, add result, and a short tail of `transmission-remote -l`

## Content routing and user preferences
Default target directories:
- movies -> `/home/piro/multimedia/movies`
- series -> `/home/piro/multimedia/series`
- music -> `/home/piro/multimedia/music`

User default audio preference: Spanish Latino dual audio, under release naming patterns such as `Dual-Lat`, `Dual`, `Lat`, `Latino`, `Esp`, `Español`, `Cast`, `Castellano`. Only propose English + subtitles or English-only downloads when Spanish options have 0 seeders and the user confirms.

## Workflow for Adding Torrents
1. **Structure First**: Always create the target directory structure (`mkdir -p`) before adding torrents to avoid default download folders.
2. **Adding Magnets**: Use `transmission-remote -a "magnet_link" -w "/absolute/path"`.
3. **Verification**: Run `transmission-remote -l` to verify the torrent is added and metadata is being retrieved.

### Remote add pattern
```bash
ssh host "transmission-remote -a '<magnet_or_local_path>' -w '/home/piro/multimedia/movies'"
```
Prefer a wrapper script so the local Hermes agent can invoke it deterministically.

## Workflow for Media Migration (Local -> Server)
When copying media files from local storage to the server:
1. **Transport**: Use `rsync -av` to move files.
2. **KODI Naming**: Ensure the target path follows the `Title (Year)/Title (Year).ext` convention.
3. **Cleaning**: Delete the original temporary download folders or source files only after verifying the final destination contains the correct file.
4. **Verification**: List the target directory to confirm the file exists and is named correctly.

### Remote migration pattern
```bash
rsync -av "/local/path/to/file.mkv" serverhogar:"/home/piro/multimedia/movies/Title (Year)/Title (Year).mkv"
```


## Reporting Status
When providing status updates on torrents:
- Use `transmission-remote -l` to get the list.
- Present the output in a clean Markdown table (ID, Name, Progress, Status) for readability.

## Optimizing Slow/Idle Torrents
If a torrent remains at 0% or "Idle" for too long (metadata not resolving):
- **Inyect Tracker List**: Add high-quality public trackers to the torrent ID.
- **Force Reannounce**: Use `--reannounce` to trigger a new search for peers.
- **Commands**:
  - Add tracker: `transmission-remote -t <ID> --tracker-add "udp://tracker.url:port/announce"`
  - Trigger: `transmission-remote -t <ID> --reannounce`
- **Sustained Low Peers**: If a torrent is stuck at 0% despite reannouncing, perform a sequence of `reannounce` followed by a 15-30s sleep to allow for peer discovery before verifying status.
- **Network Connectivity Check**: If reannouncing doesn't work, check if the Listenport is open and reachable.
  - Check if daemon is listening: `ss -tlnp | grep <port>` (default 51413).
  - Verify external reachability: `transmission-remote -pt` (will return "Port is open: No" if closed).
  - Check firewall: `sudo iptables -L -n` (look for DROP rules or missing ACCEPT for the port).
  - Common cause: Lack of Port Forwarding on the router.

## Directory Management
- To move an existing torrent to a new path: `transmission-remote -t <ID> --move "/new/absolute/path"`.
- Always verify the new path exists before moving.

## Replacing Media Files on the Server
When the user replaces a movie/series with a better version (different language, quality), old versions must be deleted. See `references/server-media-cleanup.md` for the full workflow including Jellyfin metadata handling and sudo over SSH.

## Organizing Media Library Folders (KODI naming — verified convention)
When the user asks to "ordenar"/organize a series or movie folder — one clean folder per
title, files renamed so KODI scrapes correctly — see `references/media-library-reorganization.md`.
Convention: movies `Título (Año)/Título (Año).ext`; series one folder `Título (Año)/` with
episodes `Título (Año) - S01E0X - 1080p WEB-DL Dual-Lat.mkv` (multi-season: `Temporada N/`).
CRITICAL safe-delete rule (data loss 2026-08-16): move → verify dest exists → only then
delete source; never `rm -rf` sources before every move is confirmed; absolute paths only
in SSH reorg scripts; print progress per item; verify with ffprobe at the end.

## Pitfalls
- **Separador decimal con coma (locale es_PT-BR)**: `transmission-remote -i` muestra `Percent Done: 88,1%` (coma). El grep `-oE '[0-9.]+%'` captura solo el último tramo (`1%` de `88,1%`), distorsionando el log del watcher (parece que no avanza). Fix ya aplicado en scripts: `grep -oE '[0-9.,]+%' | tr ',' '.'`. No es fatal para la detección de fin: `100%` exacto no lleva coma y el watcher lo detecta igual.
- **Case Sensitivity**: Be cautious with folder naming (e.g., `Multimedia` vs `multimedia`). Linux is case-sensitive. Always verify the user's preferred case. The server's directory is `~/multimedia/movies` (all lowercase).
- **scp Fails on serverhogar**: The remote zsh config (powerlevel10k/gitstatus) emits `can't change option: zle` errors that break scp's shell initialization. Use `rsync -av --progress` instead for all file transfers TO the server. Run in background with `notify_on_complete=true` for files over 1G.
- **Jellyfin Root-Owned Files**: Jellyfin (running as root) creates metadata files alongside media: `.trickplay/` dirs, `*-backdrop.jpg`, `*-landscape.jpg`, `*-logo.png`, `*-poster.jpg`, `folder.jpg`. These are owned by `root` and cannot be deleted by user `piro`. Use `echo "<password>" | sudo -S rm -rf <path>` over SSH to remove them.
- **Partial scp Transfers**: If scp was killed mid-transfer, it leaves partial files on the remote. rsync resumes by default, but verify and clean up partials first.
- **Metadata Retrieval Cycle**: When adding a new magnet, it may show as "Idle" with "n/a" progress. Do not assume it's broken immediately. Wait 15-30s, verify with `transmission-remote -t <ID> -i`, and if still stuck, try a different magnet hash for the same content before escalating to tracker injection.
- **Active Monitoring**: When the user asks for progress updates shortly after adding a torrent, use a `sleep` delay (e.g., 20s) before checking status to allow peers to connect and metadata to resolve.
- **Concurrent Downloading**: When adding multiple episodes of a series in rapid succession, verify each ID's state individually to ensure they aren't all competing for the same limited peer set.
- **Test magnet behavior**: Adding an obviously invalid magnet such as all-zero hash may trigger transmission help output rather than success text; do not treat full help output as a script failure until you inspect the resulting torrent list.\n- **Release Folder Gap**: Adding a torrent to `/home/piro/multimedia/series` creates a subfolder named after the release (e.g., `Show.S01E01.1080p.../`). This is NOT KODI-organized. Explicitly move the file to `Show (Year)/` and rename it to `Show (Year) - S01E01...` before reporting completion.
