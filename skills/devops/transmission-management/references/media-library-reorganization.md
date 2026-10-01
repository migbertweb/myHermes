# Media Library Reorganization (KODI/Jellyfin naming)

When the user asks to "ordenar" a series/movie folder — one clean folder per title,
video files directly inside, names a mediacenter can scrape — follow this sequence.
Verified 2026-08-09 (Stuart no logra salvar el universo, S01E01-E03).

## Why (user context)

Release-style names (`Stuart.no.logra.salvar.el.Universo.S01E02.2026.WEB-DL.1080p-Dual-Lat`)
break KODI/Jellyfin scraping: inconsistent case (`universo` vs `Universo`), per-episode
folders, and nested release root folders make episodes unrecognized. User's real complaint:
"a veces no logra reconocer los capitulos o los nombres de peliculas porque estan mal escrito".

## Target convention (KODI) — VERIFIED 2026-08-16 (57 movies + 3 series reorg)

### Movies
- One folder per movie: `/home/piro/multimedia/movies/<Título (Año)>/<Título (Año)>.ext`
  e.g. `Nunca debimos entrar (2026)/Nunca debimos entrar (2026).mkv`
- Year in parentheses is MANDATORY (disambiguates remakes/series vs movies).
- Keep the video extension (`.mkv`/`.mp4`), rename subs to `<Título (Año)>.srt` or
  `<Título (Año)>.es.srt` (extracted `_Track03.srt` junk → clean base name).
- 2-CD movies: Kodi file stacking → `Título (Año)CD1.avi` + `Título (Año)CD2.avi`.
- Duplicates of the same film: keep Dual-Lat release, delete English/flat copies.

### Series
- One folder per series: `/home/piro/multimedia/series/<Título (Año)>/` — year disambiguates
  generic titles (e.g. `Elle (2026)`, `X-Men '97 (2024)`, `Ghost in the Shell (2026)`).
- Episodes inside (flat): `<Título (Año)> - S0xE0y - <calidad> <contenedor> <audio>.mkv`
  e.g. `Ghost in the Shell (2026) - S01E01 - 1080p WEB-DL Dual-Lat.mkv`
- Multi-season shows use `Temporada N/` subfolders (existing `La Casa del Dragon/Temporada 3/`
  pattern) with the same episode naming inside.
- Never one folder per episode (breaks scraping); never nested release folders.

### Artwork (KEEP, move into new folder)
Kodi reads local art: `folder.jpg` (poster), `backdrop.jpg`, `landscape.jpg`, `logo.png`,
`seasonXX-poster.jpg`, `poster.jpg`. Jellyfin-era long formats (`Name-poster.jpg`,
`Name-backdrop.jpg`) → rename to Kodi short names when folding flat files.

### Junk (DELETE)
`.pad/` dirs, `Importante Leeme!.vbs`, `Descargar Películas...url` / `Hackstore*.url`,
`*.trickplay/` dirs, `*-thumb.jpg` (Jellyfin episode thumbs). Dead shells = folders with
only artwork/trickplay and NO video → delete with sudo (root-owned).

## Safe verify-rename procedure (use this exact order)

1. **Map first — never guess**: `find <dir> -mindepth 1 -maxdepth 3 -printf '%y %u %s %p\n'`.
   Get both dir tree AND video file list; nested release folders hide episodes.
2. **Verify titles on TMDB** (web_search es titles) before renaming; resolve duplicates and
   dead shells, present the plan, get user OK (user rule: no fixes without approval).
3. **Move → verify → cleanup**, per item:
   ```python
   # absolute paths ONLY — ssh 'python3 -' starts in /home/piro, not the media dir
   src = os.path.join(MOVIES, old_dir, file); dst = os.path.join(MOVIES, new_dir, name)
   run(["mv", src, dst])                     # same filesystem = instant
   assert os.path.exists(dst)                 # VERIFY BEFORE ANY DELETE
   # only now: rm junk inside old dir, then rmdir old dir
   ```
4. **NEVER `rm -rf` a source dir before its video is verified in the destination.**
   Verified data loss (Equalizer trilogy, ~4.5 GB) from a move-loop bug + unconditional
   shell cleanup. Print progress per item with flush=True — a crash mid-run must not hide
   what already succeeded.
5. **Root-owned leftovers**: `echo 123456 | sudo -S rm -rf <path>`. Note: mv of
   root-owned FILES works as piro when both parent dirs are piro-writable; only deletions
   of root-owned content need sudo.
6. **Transmission**: after data moves, remove dead torrents from the queue (loop
   `transmission-remote -l` → per-ID `-i` → check `Location/Name` exists → `--remove`).
   Seeding ratio is lost — offer re-adding magnets if the user cares.
7. **Verify integrity**: `ffprobe -v error -show_entries format=duration,size -of csv=p=0 <f>`
   on every moved file; confirm queue is clean and zero junk left (`.vbs|.url|.pad|trickplay`).
8. **Idempotent re-runs**: check both src AND dst before acting (a crashed run leaves
   partial state; re-running must not fail on already-done items).

## Sequence

1. **Map the mess first — never guess.** The find tree can lie: this session's first pass
   hid E02's .mkv (it was nested INSIDE E01's folder because the release had a wrong root
   folder). Get both views:
   ```bash
   ssh serverhogar 'find /home/piro/multimedia/series/ -maxdepth 3 -iname "*<title>*" -exec ls -lh {} \;'
   ssh serverhogar 'transmission-remote -t <id> -i | grep -E "Name:|Location:|Percent"'
   ```
   And list every video file independently (`find ... -iname "*.mkv" -path "*<title>*"`).

2. **Stop the torrents** for the files being moved (else they error or resume):
   ```bash
   ssh serverhogar 'transmission-remote -t <id1>,<id2> --stop'
   ```

3. **Create target + move + rename** (same filesystem → instant mv, no copy):
   ```bash
   ssh serverhogar 'mkdir -p "/home/piro/multimedia/series/Stuart no logra salvar el universo" && \
     mv "<old path>/file.mkv" "/home/piro/multimedia/series/<Titulo>/<Titulo> - S01E0X - 1080p WEB-DL Dual-Lat.mkv"'
   ```

4. **Delete old folders** — Jellyfin metadata inside is root-owned; sudo needed:
   ```bash
   ssh serverhogar 'echo 123456 | sudo -S rm -rf "<old folder 1>" "<old folder 2>"'
   ```
   Jellyfin root-owned patterns to remove: `backdrop.jpg`, `folder.jpg`, `landscape.jpg`,
   `logo.png`, `season01-poster.jpg`, `*-thumb.jpg`, `.trickplay/`. Release junk (piro-owned):
   `Descargar Películas, Series y Animes...url`, `Importante Leeme!.vbs`, `.pad/`.

5. **Remove torrents from queue** — files moved/renamed → transmission can't seed them;
   dead paths just clog the queue:
   ```bash
   ssh serverhogar 'transmission-remote -t <id1>,<id2> --remove'
   ```
   Keeps data on disk; only the queue entry goes. NOTE: seeding ratio is lost — re-add the
   magnets if the user wants to keep seeding (offer this, don't assume).

6. **Verify integrity** with ffprobe (duration + size prove the file is the right episode):
   ```bash
   ssh serverhogar 'for f in "/home/piro/multimedia/series/<Titulo>/"*.mkv; do ffprobe -v error -show_entries format=duration,size -of csv=p=0 "$f"; done'
   ```
   Then confirm queue is clean: `transmission-remote -l | grep -i <title>` → nothing.

## Pitfalls

- **NEVER delete source dirs (`rm -rf`) before verifying every move succeeded.** A bug in
  the move loop (e.g. wrong path) silently leaves files behind, then the shell cleanup
  deletes them permanently. Verified 2026-08-16: lost The Equalizer trilogy (~4.5 GB) this
  way. Pattern: run moves, re-scan `find` for videos, and only then delete leftovers.
- **Use ABSOLUTE paths in reorg scripts run over SSH.** `ssh serverhogar 'python3 -'` starts
  in the SSH user's home (`/home/piro`), NOT the media dir. `os.path.relpath` + relative
  joins silently fail. Build paths with `os.path.join(MOVIES, ...)` everywhere.
- **Print progress per movie as you go** (flush per item). A crash mid-run loses visibility
  of what already succeeded; an "OK" summary only at the end hides partial work.
- **Idempotency**: if a run crashes and you re-run, the script must skip/verify already-done
  items instead of failing on them. Check `os.path.exists` on both source AND target first.
- Never delete old folders with plain `rm` — Jellyfin files are root-owned (see step 4).
- Map first, always: nested release folders are common with Spanish trackers (EliteTorrent
  releases ship a wrong root folder name, which transmission materializes as a nested dir).
- Jellyfin picks up the new folder on its next scan; force a library scan from the dashboard
  if the user wants it immediate.
