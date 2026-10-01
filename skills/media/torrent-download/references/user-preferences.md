# User Preferences — Torrent Downloads

## Language

- **Default:** Spanish Latino (Dual-Lat / Dual). English audio only as explicit fallback.

## Stalled Torrents

- **Do NOT remove** stalled/no-seeder torrents automatically. The user prefers to leave them in the queue in case seeders appear later (`"dejala ahi a lo mejor pega alguno mas tarde"`).
- Only remove a stalled torrent if the user explicitly asks to, or if it's blocking the queue and the user agrees.
- Check the tracker status first (`-it`) — if trackers report leechers (even 0 seeders), the torrent may eventually connect.

## English vs Dual Conflicts

- If a Dual-Lat version is queued for a movie that already has an English-only version downloaded:
  - **Remove the English version** (with files) and keep the Dual-Lat version.
  - The user prefers Dual audio even if it means waiting for seeders on the Dual version.

## Adding Trackers

- When a torrent has name resolved but no peers (Piece Size: None), add well-known public trackers and reannounce before giving up.
- If the torrent still fails to connect after tracker injection, leave it in the queue — do not remove.

## Download Queue

- The user does NOT manually monitor the queue. Dead torrents that can't resolve metadata should be left alone unless they explicitly interfere with active downloads.
