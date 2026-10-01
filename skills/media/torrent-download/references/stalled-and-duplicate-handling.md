# Stalled & Duplicate Torrent Handling (pitfalls detail)

Session-verified additions to the main SKILL.md pitfalls (2026-08-09, Maridos.en.accion).

## Duplicate magnet (same infohash)

When the user passes a magnet claiming to be an alternative for a stalled torrent,
VERIFY it's actually different before adding:

```bash
ssh serverhogar 'transmission-remote -t <id> -i | grep Hash:'
# compare with the new magnet's urn:btih: value
```

Users may paste the same link twice (same name, same size). If the hash matches,
do NOT re-add — tell them a real alternative must have a different infohash
(different release group, resolution, or tracker set). Observed: user re-sent the
identical Maridos.en.accion 1080p magnet; hash check caught it before a duplicate
was queued. Transmission dedupes by hash, so an identical magnet would just clone
the stalled torrent to no effect.

## Leechers reported but 0 peers connected

Tracker shows `N leechers` (e.g. torrent.eu.org reporting 6 leechers) but
`Peers: connected to 0` means other people are trying the same release but nobody
with complete metadata has connected yet — common for brand-new releases. The
torrent has a real chance of starting later. Leave it in queue per user preference
(stalled/no-seeder torrents are kept, never auto-removed). Do NOT declare it dead
based on tracker leecher counts alone; do NOT `--remove` it while leechers are
visible.

## Trackers "Connection failed" vs dead torrent

`tracker.openbittorrent.com` and `tracker.opentrackr.org` both returned
"Connection failed" persistently in this session (hours) while the same trackers
worked for other torrents. When the 2 default magnet trackers are down but
`tracker.torrent.eu.org` answers with leechers, the torrent is NOT dead — it is
waiting on a peer with complete metadata. The metadata-fetch window (`-nan%` +
peers downloading at 0 kB/s, resolves in ~25s) is documented in SKILL.md; this
reference adds the later stage: metadata resolved, 0 peers, leechers on tracker.
