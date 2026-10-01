# Mediacenter naming & folder normalization (KODI/Jellyfin)

Trigger: user asks to organize a series/movie folder so KODI/Jellyfin recognize
episodes correctly — messy dotted release names
(`Stuart.no.logra.salvar.el.Universo.S01E02.2026.WEB-DL.1080p-Dual-Lat`),
episodes split across several folders, or episodes nested inside each other's
folders (EliteTorrent packs).

## Target convention (normativa mediacenter)

- One folder per series: `/home/piro/multimedia/series/<Nombre limpio de la serie>/`
- Files inside, renamed to: `<Serie> - S01E0X - <calidad>.mkv`
  e.g. `Stuart no logra salvar el universo (2026) - S01E05 - 720p WEB-DL Dual-Lat.mp4`
- The `SxxExx` marker is what scrapers (TMDB/IMDB) parse — keep it intact.
  Spaces + dashes are safer than dotted release names for matching.
- Movies: single folder per clean-titled movie `/home/piro/multimedia/movies/Título (Año)/` and clean file inside `Título (Año).ext` (e.g. `Pistolero (1995)/Pistolero (1995).mkv`).

## Movie Post-Completion Workflow

When a movie download finishes:
1. Verify download state is `100%` and check playability/tracks with `ffprobe`.
2. Remove the torrent entry from Transmission without deleting files:
   `ssh serverhogar 'transmission-remote -t <id> --remove'`
3. Rename release folder to `Título (Año)`:
   `ssh serverhogar 'mv "/home/piro/multimedia/movies/Pistolero.1995.1080p-dual-lat" "/home/piro/multimedia/movies/Pistolero (1995)"'`
4. Remove garbage files (`.url`, `.vbs`, etc.):
   `ssh serverhogar 'cd "/home/piro/multimedia/movies/Pistolero (1995)" && rm -f *.url *.vbs'`
5. Rename video file to `Título (Año).ext`:
   `ssh serverhogar 'mv "Pistolero.1995.1080p-dual-lat.mkv" "Pistolero (1995).mkv"'`

## Steps

1. **Map the real structure first** — releases often carry a wrong internal
   root folder (E02 folder can live INSIDE the E01 folder). Torrent names lie;
   file paths are the source of truth:
   ```bash
   ssh serverhogar 'find /home/piro/multimedia/series/ -maxdepth 3 -iname "*<serie>*" -exec ls -lh {} \;'
   # plus per-torrent: transmission-remote -t <id> -i | grep -E "Name:|Location:|Percent"
   ```
2. **Stop the involved torrents** before moving:
   `ssh serverhogar 'transmission-remote -t <id1>,<id2>,... --stop'`
3. **Create the clean folder and mv + rename** (same filesystem → instant):
   ```bash
   ssh serverhogar 'mkdir -p "/home/piro/multimedia/series/<Serie limpia>" && mv "<old path>" "<new path>" && ...'
   ```
4. **Remove those torrents from the queue** — after rename/move Transmission
   can't seed them; `--remove` (NOT `--remove-and-delete`) keeps files on disk.
5. **Delete old folders incl. root-owned Jellyfin metadata** (sudo, see
   transmission-management `references/server-media-cleanup.md`):
   ```bash
   ssh serverhogar 'echo PASSWORD | sudo -S rm -rf "<old folder1>" "<old folder2>"'
   ```
   Jellyfin artifacts owned by root: `*-backdrop.jpg`, `folder.jpg`,
   `*-landscape.jpg`, `*-logo.png`, `*-poster.jpg`, `*-thumb.jpg`.
   Release junk to delete too: `Descargar Películas...url`, `Importante Leeme!.vbs`, `.pad/`.
6. **Verify integrity** of each renamed file with ffprobe:
   `ffprobe -v error -show_entries format=duration,size -of csv=p=0 "<file>"`
7. Jellyfin picks the new folder up on its next scan (or manual dashboard refresh).

## Pitfalls

- The sudo prompt appears inline in SSH output (`Password pls:`); the
  `echo PASSWORD | sudo -S` pattern handles it non-interactively.
- Nested episode folders: a torrent may report `Location: series/` while its
  file actually sits inside another episode's folder. Trust `find`, not `-i`.
- Mixed casing between episodes (`universo` vs `Universo`) is normal across
  releases — the cleanup normalizes it all to the clean title.
