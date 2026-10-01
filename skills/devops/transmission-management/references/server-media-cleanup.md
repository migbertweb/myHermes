# Server Media Cleanup Workflow

When replacing media files on serverhogar (e.g., swapping English-only for Dual-Lat versions), follow this sequence.

## Context
- Server SSH alias: `serverhogar` (Host: 192.168.1.8, User: piro)
- Media root: `~/multimedia/movies` (all lowercase — not `Multimedia`)
- User preference: Spanish Latino dual audio (`Dual-Lat`) as default. English-only versions get replaced.

## Transfer new files
Use **rsync** (not scp — see pitfalls). Run in background for >1G:

```bash
# Syntax: rsync -av --progress "local/dir/" serverhogar:"~/multimedia/movies/<target_dir>/"
# Note trailing slash on source = copy contents, not the dir itself
rsync -av --progress "/home/migbert/Escritorio/El Justiciero Saga/" \
  serverhogar:"~/multimedia/movies/El Justiciero Saga/"
```

For background transfer:
```
terminal(background=true, notify_on_complete=true, timeout=600)
```

## Identify old versions to delete
Search case-insensitive — titles may use English or Spanish names (Equalizer / El Justiciero / El Protector):

```bash
ssh serverhogar 'cd ~/multimedia/movies && ls -la | grep -i equalizer'
```

Check subfolders — some YTS/GIRAYS releases are empty dirs with only Jellyfin images (no video).

## Verify audio tracks before deciding
Use ffprobe to confirm the language of existing files:

```bash
ssh serverhogar "ffprobe -v error -show_entries stream=index,codec_type:stream_tags=language,title \
  -of csv=p=0 '~/multimedia/movies/<filename>'"
```

Output format: `index,codec_type,language` per stream. Look for `spa` or `eng` in audio streams.

## Delete old versions
Jellyfin-created metadata files are owned by `root`. User `piro` has sudo but not NOPASSWD:

```bash
ssh serverhogar 'echo "123456" | sudo -S rm -rf \
  ~/multimedia/movies/"old_file_or_folder1" \
  ~/multimedia/movies/"old_file_or_folder2"'
```

Jellyfin metadata patterns to clean up (owned by root):
- `.trickplay/` directories (BIF thumbnails)
- `*-backdrop.jpg`
- `*-landscape.jpg`
- `*-logo.png`
- `*-poster.jpg`
- `folder.jpg`

## Media naming convention (KODI/Jellyfin)
User organizes media per KODI/Jellyfin scraping rules. One folder per series with video files inside, named `Title - S01E0X - quality.mkv` (the `S01E0X` marker is what scrapers parse). Dotted release-style names (`Serie.S01E02.2026.WEB-DL...`) and nested release root folders (EliteTorrent etc.) break episode recognition — consolidate and rename after download. Example target:
```
/home/piro/multimedia/series/Stuart no logra salvar el universo/
  Stuart no logra salvar el universo - S01E01 - 1080p WEB-DL Dual-Lat.mkv
```
After moving/renaming files, stop and remove the torrents from Transmission (`transmission-remote -t <id> --stop` then `--remove`) so they don't report missing files.

## Verify
```bash
ssh serverhogar 'ls -lh ~/multimedia/movies/<target_dir>/'
ssh serverhogar 'ls ~/multimedia/movies/ | grep -i <title>'
```

Confirm only the new files remain.
