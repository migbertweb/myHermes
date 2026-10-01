# Post-download reorg + tracker injection pitfalls (verified 2026-08-16)

## Post-download auto-reorg (rename to KODI convention)

Releases download with dot-separated names and junk files. Verified flow
(Stuart S01E04, 2026-08-16):

1. After adding the magnet, inspect internal filenames early:
   `transmission-remote -t <ID> -f`
   Expect: the real `.mkv` plus junk — `.pad/` dirs, `*.url` (e.g.
   `Descargar Películas, Series y Animes...url`), and `*.vbs` (e.g.
   `Importante Leeme!.vbs`).
2. Deploy `scripts/post_download_reorg.sh` to the server (rsync — scp breaks
   on serverhogar's zsh) and launch detached so it survives the SSH session:
   ```bash
   rsync -av post_download_reorg.sh serverhogar:/tmp/
   ssh serverhogar 'setsid nohup bash /tmp/post_download_reorg.sh \
     <ID> <SRC_DIR> "<FINAL_DIR>" "<FINAL_FILE>" > /tmp/reorg.log 2>&1 < /dev/null &'
   ```
   Poll with `ssh serverhogar 'tail /tmp/reorg.log'`.
3. Script behavior: waits (polls Percent Done/State every 30s) until 100%,
   finds the `.mkv`, moves+renames into KODI convention, cleans `.pad/`,
   `*.url`, `*.vbs`, `rmdir`s the release folder, removes the torrent from
   the list (`transmission-remote -t <ID> --remove`, data kept), and verifies
   with ffprobe (filename/duration/size).

KODI naming actually used (matches "Organizing Media Library Folders"):
- Series: `series/Title (Año)/Title (Año) - S0xE0y - 1080p WEB-DL Dual-Lat.mkv`
- Movies: `movies/Title (Año)/Title (Año).ext`

## Tracker injection pitfalls

Stuck metadata (Idle, Piece Count 0, 0 peers) was fixed by adding 8 public
trackers + `--reannounce`; metadata resolved within ~20s.

- `--tracker-add` fails with `Error: error setting announce list` when the
  tracker is ALREADY in the magnet's `&tr=` params (e.g. the magnet already
  had `tracker.openbittorrent.com` and `tracker.opentrackr.org`). This is
  NOT a failure of the tracker itself.
- Chaining with `&&` is fatal here: the first duplicate error aborts the
  whole chain, so subsequent NEW trackers never get added. Chain with `;`
  or add them one per line.
- Check the magnet's `tr=` params before choosing trackers to inject; skip
  ones already present. Good public additions: open.demonii.com, exodus
  .desync.com, explodie.org, tracker.torrent.eu.org,
  tracker.internetwarriors.net, tracker.cyberia.is, leechers-paradise.org
  (udp://...:6969 or :1337/announce variants).
- Slow-but-working downloads: 2 peers at ~180 kB/s is normal for a fresh
  magnet; ETA can be hours. Don't treat slow speed as failure.

## Type routing reminder

`S0xE0y` in the release name = SERIES, not movie, regardless of what the
user calls it. Route to `/home/piro/multimedia/series`, not movies.
