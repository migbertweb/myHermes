# Nested KODI-folder downloads + SSH launch pitfalls (verified 2026-08-24)

Companion to `references/post-download-reorg-and-trackers.md`. This file holds
variants and pitfalls verified in the 2026-08-24 batch (Linternas S01E02 + 2 movies).

## Pattern: `-w` straight into the final KODI folder

Structure-first works per-KODI-folder, not just per-library-root: `mkdir -p` the final
`movies/Title (Year)/` folder, then add the magnet with `-w` pointed at it. Folder-type
releases (the norm: mkv + `Importante Leeme!.vbs` + `Descargar ... .url`) create their
release-named subfolder INSIDE the KODI folder, so the reorg args become:

- SRC_DIR   = `/home/piro/multimedia/movies/Toy Story 5 (2026)/Toy.Story.5.2026.1080p-Dual-Lat`
- FINAL_DIR = `/home/piro/multimedia/movies/Toy Story 5 (2026)`
- FINAL_FILE = `Toy Story 5 (2026).mkv`

Same pattern for an episode into an existing series folder (`series/Lanterns (2026)/` →
`Lanterns (2026) - S01E02 - 1080p WEB-DL Dual-Lat.mkv`). The reorg script's
`find "$SRC_DIR" -maxdepth 2 -name '*.mkv'` covers this nesting. All three torrents in
this batch (1 episode + 2 movies) were folder-type with the same junk files.

Sequence that worked (3 torrents, all in parallel, no conflicts):
1. `ssh serverhogar "mkdir -p '<final KODI dir>'"` per movie (structure first).
2. `ssh serverhogar "transmission-remote -a '<magnet>' -w '<final KODI dir>'"` per torrent
   (3 parallel SSH calls; each returned `responded: success`).
3. `sleep 20` → `transmission-remote -l` to map torrent IDs.
4. `transmission-remote -t <ID> -f` to confirm mkv + junk and get the release subfolder
   name (SRC_DIR).
5. rsync `post_download_reorg.sh` to server `/tmp/` once, then one detached watcher per ID.
6. Verify watchers with `pgrep -af post_download_reorg` + `tail /tmp/reorgNN.log`.

## Pitfall: SSH hang when chaining `-f` inspection with the setsid launch

```
ssh serverhogar "transmission-remote -t 86 -f | head -8 && setsid nohup bash /tmp/post_download_reorg.sh ... & echo ok"
```
returned exit 124 (timed out at 45s) even though the watcher DID launch remotely. The
launch-only batch (two `setsid nohup ... &` in one ssh call, no `-f` pipe) did not hang.
Rules:
- Keep inspection (`-f`) and watcher launch in SEPARATE ssh calls.
- After a timed-out launch, confirm with `pgrep -af post_download_reorg` and
  `tail /tmp/reorgNN.log` before assuming failure or double-launching.

## Metadata resolution after tracker injection can take >1 min

A magnet with only 2 trackers (openbittorrent + opentrackr) showed `Piece Count: 0` /
`Percent Done: -nan%` for over a minute. After injecting 5 extra trackers
(open.demonii.com:1337, explodie.org:6969, tracker.torrent.eu.org:451,
tracker.internetwarriors.net:1337, open.stealth.si:80) + `--reannounce`, it STILL showed
0 pieces; only after ~60-85s more and a SECOND `--reannounce` did it resolve
(5389 pieces, 1 peer, Downloading). Do not declare a torrent dead at the first
reannounce — repeat reannounce + sleep and re-check `-i`.
