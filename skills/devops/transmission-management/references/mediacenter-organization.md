# Mediacenter Organization & Renaming (KODI/Jellyfin)

When the user asks to reorganize downloaded series/movies into a clean mediacenter structure — "una sola carpeta, nombres según normativa KODI".

## Target structure

- Series: ONE folder per series at `/home/piro/multimedia/series/<Nombre Serie>/`, all episodes flat inside
- Files: `<Nombre Serie> - S01E0X - <calidad>.mkv` — the `SxxExx` marker is the only thing scrapers parse; the rest is free-form
- Spanish title with spaces beats release-style dots: `Stuart no logra salvar el universo - S01E01 - 1080p WEB-DL Dual-Lat.mkv`, NOT `Stuart.no.logra.salvar.el.universo.S01E01...`
- Movies: clean name in `/home/piro/multimedia/movies/`

## Known mess patterns (Spanish releases, EliteTorrent etc.)

- Each episode in its own folder named after the release, with INCONSISTENT case (`universo` vs `Universo`)
- The torrent's embedded root directory can have the WRONG name — observed: S01E02 content nested inside a folder named after S01E01 (release packaging bug). `find` is the only reliable way to locate all video files
- Junk files in every release folder: `Descargar Películas, Series y Animes...url`, `Importante Leeme!.vbs`, `.pad/`
- Jellyfin root-owned metadata (owner `root`, can't delete as piro without sudo): `backdrop.jpg`, `folder.jpg`, `landscape.jpg`, `logo.png`, `season01-poster.jpg`, `*-thumb.jpg`, `.trickplay/`

## Workflow

1. **Map everything first** — never trust folder names:
   ```bash
   ssh serverhogar 'find /home/piro/multimedia/series/ -maxdepth 3 -iname "*<title>*" -exec ls -lh {} \;'
   ssh serverhogar 'find /home/piro/multimedia/series/ -iname "*.mkv" -path "*<title>*" -exec ls -lh {} \;'
   ```
2. Stop the affected torrents BEFORE moving files (`transmission-remote -t <ids> --stop`) so they don't error mid-move.
3. Create the target folder and move+rename each MKV. Same filesystem = instant rename, even 2GB files:
   ```bash
   ssh serverhogar 'mkdir -p "/home/piro/multimedia/series/<Nombre Serie>" && mv "<old path>/<file>.mkv" "/home/piro/multimedia/series/<Nombre Serie>/<Nombre Serie> - S01E01 - 1080p WEB-DL Dual-Lat.mkv"'
   ```
4. Delete the old folders (includes root-owned Jellyfin metadata) — piro has sudo but not NOPASSWD:
   ```bash
   ssh serverhogar 'echo "<pass>" | sudo -S rm -rf "<old folder 1>" "<old folder 2>"'
   ```
5. Remove the torrents from the queue (`--remove`, NOT `--remove-and-delete` — files are already moved) so Transmission stops reporting missing files.
6. Verify integrity per file before/after:
   ```bash
   ssh serverhogar 'ffprobe -v error -show_entries format=duration,size -of csv=p=0 "<file>"'
   ```
7. Jellyfin picks up the new folder on its next library scan; no manual step needed.

## Pitfalls

- Do NOT delete old folders until every MKV is confirmed moved (ffprobe each).
- After moving files, the torrents WILL show "missing files" if left in the queue — remove them.
- The reorganized series folder may have a different name than Jellyfin's old entry; a fresh scan creates a new entry (old metadata jpgs die with the old folders).
- KODI naming standard: folder name = series title; file pattern `Title - S01E01 - quality.mkv`. Never split episodes across folders.
