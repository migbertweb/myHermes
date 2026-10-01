---
name: torrent-download
description: >-
  Download torrents (magnet links or .torrent files) via transmission-daemon
  on serverhogar. Environment-conditional commands: direct transmission-remote
  when on the server, SSH-wrapped when on the laptop or remote context.
  Supports routing downloads to different directories by content type
  (movies, series, music).
---

# Torrent Download

Set up and use a BitTorrent client to download media via magnet links or `.torrent` files. Supports routing downloads to different directories by content type (movies, series, music).

**⚠️ Los comandos son condicionales al entorno de ejecución.** Cuando trabajes desde el server (serverhogar) usa `transmission-remote` directamente; cuando trabajes desde la laptop CachyOS (o cualquier sesión remota) envuelve cada comando en `ssh serverhogar 'transmission-remote ...'`. El skill incluye autodetección vía `hostname` en los scripts.

## Environment Detection

**This skill runs from either environment: the server (serverhogar) or the laptop (CachyOS).** The command pattern depends on where you are:

| Where you are | How to call Transmission |
|---|---|
| **On serverhogar** (direct terminal / server Hermes session) | Run commands directly: `transmission-remote <args>` |
| **On laptop CachyOS** (laptop Hermes session / any remote context) | Wrap every command in SSH: `ssh serverhogar 'transmission-remote <args>'` |

### Quick detection pattern

When automating across both environments, use this pattern in scripts:

```bash
# Auto-detect environment
if hostname | grep -qi 'serverhogar\|\.8$'; then
  # Running on the server — direct commands
  TR='transmission-remote'
else
  # Running on the laptop (or anywhere else) — go through SSH
  TR='ssh serverhogar transmission-remote'
fi

# Usage: $TR -l  (works from either side)
```

### Golden rule for manual execution

- **Single quotes + single commands**: `ssh serverhogar 'transmission-remote -l'`
- **Magnet links with special chars**: use double quotes outside, escape inner quotes as needed: `ssh serverhogar "transmission-remote -a 'magnet:?xt=...'"`
- **Multi-command chains**: wrap everything in one pair of single quotes after SSH: `ssh serverhogar 'cmd1 && cmd2 && cmd3'`
- **Prefer direct commands via SSH in Hermes sessions**: although the `remote_add_torrent.sh` script exists for laptop terminal usage, Hermes sessions benefit from direct `ssh serverhogar 'transmission-remote ...'` calls to avoid extra script layers and ensure exact control over arguments.

## Trigger conditions

- User asks to install a torrent client
- User provides a magnet link or `.torrent` file
- User asks to download something they have a magnet/torrent for
- User asks about downloading torrents via the terminal/agent

## Setup (one-time)

### If transmission is not installed on serverhogar:

```bash
ssh serverhogar 'sudo pacman -Sy --noconfirm transmission-cli'
```

### Directory structure (on serverhogar):

```bash
ssh serverhogar 'mkdir -p /home/piro/multimedia/{movies,series,music}'
```

Verify it from your current location:

```bash
# From laptop CachyOS:
ssh serverhogar 'transmission-remote -l'

# From serverhogar directly:
transmission-remote -l
```

### Remote access (web UI from the laptop)

If `rpc-authentication-required` is `false` (default), no username/password
is needed — just the host and port.

The web UI is available at `http://192.168.1.8:9091/transmission/web/`.

See `references/remote-access.md` for the exact config of this user's server (192.168.1.8).

Copy the system config to the user's config directory so the daemon can
read/write it when running as the user:

```bash
# Run on serverhogar:
ssh serverhogar 'mkdir -p /home/piro/.config/transmission-daemon'
ssh serverhogar 'sudo cat /etc/transmission-daemon/settings.json > /home/piro/.config/transmission-daemon/settings.json'
ssh serverhogar 'chmod 644 /home/piro/.config/transmission-daemon/settings.json'
```

Edit `settings.json` to set the default download directory (optional;
`-w` flag on `transmission-remote` overrides this per-torrent).

### Starting the daemon

**Approach A — systemd (User Level - Recommended):**
Create a unit file at `~/.config/systemd/user/transmission-daemon.service` with `Type=simple` and `ExecStart` pointing to the daemon with the `-g /home/piro/.config/transmission-daemon` flag. 
**Crucial:** Disable the system-wide service (`sudo systemctl disable transmission-daemon`) to avoid conflicts and timeout issues caused by `Type=notify` in the default system unit.

**Approach B — Hermes-managed background process:**
```python
terminal(
  command="transmission-daemon -f --log-level=error -g /home/piro/.config/transmission-daemon",
  background=true
)
```

**A. Quick start (auto-daemonizes, on serverhogar):**
```bash
transmission-daemon
```
The daemon forks into the background on its own — fine for most CLI scenarios.
No `-f` flag needed.

⚠️ Uses `~/.config/transmission-daemon/` by default — the same dir as approach B.
Make sure `settings.json` exists there (copy from system config if needed).

**B. Hermes-managed background process (recommended if you want process tracking):**
```python
terminal(
  command="transmission-daemon -f --log-level=error -g /home/piro/.config/transmission-daemon",
  background=true
)
```

Verify it is running:

```bash
# From laptop CachyOS:
ssh serverhogar 'transmission-remote -l'

# From serverhogar directly:
transmission-remote -l
# Expected: "ID   Done       Have  ETA           Up    Down  Ratio  Status       Name"
```

## Searching for magnet links

When the user provides a URL to a torrent site (e.g. dontorrent, 1337x, TPB)
instead of a direct magnet link, the site may be blocked by anti-bot
protection (CAPTCHA, Proof-of-Work, Cloudflare, etc.). In that case, do NOT
try to brute-force the page — use the **TPB API** as a fallback search:

```bash
# Basic search
curl -sL "https://apibay.org/q.php?q=<search+terms>" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data[:10]:
    name = item.get('name','')
    info_hash = item.get('info_hash','')
    seeders = item.get('seeders','')
    leechers = item.get('leechers','')
    size = item.get('size','')
    if size:
        try: size_gb = round(int(size)/1073741824, 2)
        except: size_gb = size
    else: size_gb = '?'
    print(f'Name: {name}')
    print(f'Hash: {info_hash}')
    print(f'Seeders: {seeders} | Leechers: {leechers}')
    print(f'Size: {size_gb} GB')
    print('---')"
"
```

**⚠️ IMPORTANT: The TPB API field for seeders is called `seeders`, NOT `seeds`.** Use `item.get('seeders','')` in Python scripts (see pitfall below).

**Query tips for finding the right version:**
- **Lightweight/streaming (x265 HEVC):** append `x265`, `hevc`, or `x265.10bit` to the search
- **Very small (under 2 GB per movie):** add `BRRip` or `WEBRip` + `HEVC`
- **YTS releases** (e.g. `[YTS.MX]` or `[YTS.AM]`) are an excellent fallback when x265 versions have no seeders — they use optimized x264 at 1080p, typically 1.2-2 GB per movie, and are almost always well-seeded (50-150+ seeders). Search with `YTS` in the query if x265/HEVC results are dead.
- **Trilogy/collections:** search with `trilogy` or `collection` — but check total size (packs can be 44+ GB)
- **Dual audio (Spanish/English):** add `dual` or `dual-lat` to the query
- **720p for streaming:** add `720p` + `hevc` or `x265` for quality/space balance

**Always check seed/leecher counts** from the API output before picking a
torrent. Favor entries with visible leechers (>0) or high seeders (>20).
Entries with 0 seeders and 0 leechers may never connect. If in doubt, add
more specific terms (release group name, resolution, codec). The `seeders`
field is the authoritative field name in the TPB API — do NOT confuse it
with `seeds`.

See `references/tpb-api.md` for the full API documentation.

## Multi-Magnet Race (Fastest First)
When the user provides multiple magnet links for the same episode to find the fastest one:
1. Add all provided magnets to Transmission.
2. Wait 30-60 seconds for metadata resolution and peer connection.
3. Identify the torrent that has transitioned from `Idle`/`n/a` to `Downloading` with the highest `Download Speed` or `Peers` count.
4. Immediately remove the slower/stalled duplicates using `transmission-remote -t <ID> --remove-and-delete` to free up queue slots.

## Handling torrents that get no peers

When a magnet link is added to Transmission but stays at 0% with `Status: Idle`
and `Peers: connected to 0`, the torrent has no seeders available.

### Diagnosis

```bash
# Check peer count and status
ssh serverhogar 'transmission-remote -t <id> --info | grep -E "State|Percent|Peers|Download Speed|Error"'

# Full info dump
ssh serverhogar 'transmission-remote -t <id> --info'

# Check tracker status (which trackers are responding)
ssh serverhogar 'transmission-remote -t <id> -it'


### Handling Partially Downloaded Torrents (99.9% Stuck)
When a torrent is stuck at 99.9% and cannot find the last few pieces (common in low-seed torrents), the file remains in the `incomplete-dir` (if enabled) and is not moved to the final destination.
- **Symptom:** `Percent Done: 99,9%`, `State: Idle`, and availability is very close to 100% but not quite.
- **Assessment:** Check if the file is actually playable via SSH:
  ```bash
  ssh serverhogar 'ffprobe -v error -show_entries format=duration,size "/path/to/incomplete/file.mkv"'
  ```
- **Workaround (Forced Completion):** If the video is playable and only a tiny fraction is missing:
  1. Stop the torrent: `ssh serverhogar 'transmission-remote -t <id> --stop'`
  2. Move file: `ssh serverhogar 'mv /path/to/incomplete/file.mkv /final/path/'`
  3. Remove torrent: `ssh serverhogar 'transmission-remote -t <id> --remove-and-delete'`
```

Look for `Peers: connected to 0, downloading from 0` — this confirms the
torrent has no active sources.

### Metadata not resolving (Percent Done: -nan%)

If the torrent shows `Percent Done: -nan%` (not a number) and `Name:` still
shows the hash or a URL-encoded name, the **metadata hasn't resolved yet** —
the magnet link connected to no tracker that can serve the file list. This is
different from having metadata but no seeders.

**⚠️ `-nan%` + peers connected = HEALTHY metadata fetch — do NOT inject trackers.**
If `Percent Done: -nan%` but `Peers: connected to N, downloading from N` with
N > 0 and `State: Downloading`, metadata is being fetched over DHT/PEX (the
magnet has no working tracker, but peers are supplying the file list). Just
wait 20-25 seconds and recheck before touching anything. Observed 2026-08-09:
`-nan%` with 12 peers connected/downloading at 0 kB/s resolved on its own to
1.4% at ~3 MB/s with 23 peers after ~25s. The tracker-injection fix below
applies ONLY when peers = 0.

**Fix: add known-good public trackers to the existing torrent (via SSH)**

```bash
# Add well-known public trackers to a stalled magnet
ssh serverhogar 'transmission-remote -t <id> --tracker-add "udp://tracker.torrent.eu.org:451/announce"'
ssh serverhogar 'transmission-remote -t <id> --tracker-add "udp://tracker.opentrackr.org:1337/announce"'
ssh serverhogar 'transmission-remote -t <id> --tracker-add "https://tracker.fastdownload.xyz:443/announce"'
ssh serverhogar 'transmission-remote -t <id> --tracker-add "udp://tracker.coppersurfer.tk:6969/announce"'
ssh serverhogar 'transmission-remote -t <id> --tracker-add "udp://tracker.leechers-paradise.org:6969/announce"'
ssh serverhogar 'transmission-remote -t <id> --tracker-add "udp://tracker.justseed.it:1337/announce"'
ssh serverhogar 'transmission-remote -t <id> --tracker-add "udp://tracker.internetwarriors.net:1337/announce"'

# Force an immediate reannounce to contact the new trackers
ssh serverhogar 'transmission-remote -t <id> --reannounce'
```

Wait **10-20 seconds** after reannouncing, then check again:

```bash
ssh serverhogar 'transmission-remote -t <id> --info | grep -E "Name:|State:|Percent|Peers:"'
```

If the name resolves (e.g. changes from the hash to a proper filename), the
metadata download succeeded and the torrent should start downloading normally.

**Prevention:** When adding a magnet link that only has one tracker (especially
from obscure sources like EliteTorrent, DonTorrent), add the public trackers
upfront at creation time by appending them to the magnet link's tracker list.
Or use `--tracker-add` right after adding the torrent, before the metadata
fetch times out.

### No metadata AND no peers (seeders/leechers show 0 after metadata resolves)

After metadata resolves, if `Peers: connected to 0` and no seeders/leechers
are reported by the trackers, the torrent itself has no active sources. Proceed
to "Resolution" below.

### Resolution

1. **Remove the unresponsive torrent:**
   ```bash
   ssh serverhogar 'transmission-remote -t <id> --remove'
   ```

2. **Search for an alternative** using apibay.org (see "Searching for magnet
   links" above) with more specific terms or a different release group.

3. **Check the new alternative has leechers** before adding by looking at the
   `seeders` and `leechers` columns from the API output.

4. **Add the alternative via SSH to serverhogar:**
   ```bash
   ssh serverhogar "transmission-remote -a '<magnet_link>' -w /home/piro/multimedia/<type>/"
   ```

5. **Verify peers connect** after 5-10 seconds:
   ```bash
   ssh serverhogar 'transmission-remote -t <new_id> --info | grep Peers'
   ```

Look for `Peers: connected to N, downloading from N` where N > 0.

### Fallback strategy (full chain)

If the first choice has no peers, try alternatives in this order:

1. **Same search, different release group** — Search again with slightly different
   terms or add a release group name (e.g. `-GIRAYS`, `-PSA`, `[YTS.MX]`).

2. **YTS releases** — If x265/HEVC lightweight versions have zero peers, try YTS
   releases (search with `YTS` in the query). They use optimized x264 at 1080p
   with good size-to-quality ratio (1.2-2 GB per movie) and are almost always
   well-seeded (50-150+ seeders). ⚠️ YTS is English-only audio — no Dual/Spanish.

3. **720p HEVC** — If no 1080p x265 and no YTS has seeders, try 720p HEVC
  versions (typically 0.5-1 GB each). Search: `query=<movie>+720p+hevc` or
  `query=<movie>+720p+x265`.

## Troubleshooting Dead Torrents (nan% / stuck)
When a torrent is stuck at 0.0% (nan%) or a specific percentage:
1. **Forced Verification:** Use `ssh serverhogar 'transmission-remote -t <id> --verify'` to check if the existing data is intact.
2. **Tracker Injection:** If metadata isn't resolving, manually inject known-good public trackers and trigger `--reannounce`.
3. **Pruning:** If trackers report peers but metadata remains unresolved or seeders are 0, remove the torrent: `ssh serverhogar 'transmission-remote -t <id> --remove-and-delete'`

4. **English + subtitles** — If all Spanish/dual audio torrents have 0 peers,
   the practical final fallback is to download the well-seeded English version
   and add Spanish subtitles. Present this option clearly to the user:
   "The Dual/Spanish versions all have no seeders. I can download the English
   version (well-seeded, lightweight) and add Spanish subtitles. ¿Te parece bien?"

## User Preferences

This user has specific workflow preferences documented in `references/user-preferences.md`. Key points: keep stalled/no-seeder torrents in the queue (do not auto-remove), and when a Dual-Lat version is queued alongside an English-only copy of the same movie, remove the English version. Read the reference before making removal decisions.

## Language preference (DEFAULT)

**Default download language: Spanish Latino (Dual-Lat / Latino).**

Unless the user explicitly asks for English audio, always search for and prioritize torrents with:
- **Dual-Lat** or **Dual** in the name = English + Spanish Latino (dual audio track)
- **Lat** or **Latino** in the name = Spanish Latino only
- **Esp** or **Español** = Spanish
- **Cast** or **Castellano** = Spanish (European)

**CRITICAL: If the user provides specific magnet links, use them exactly as provided. Do not substitute them with other versions found via search unless the provided links fail to resolve or have no seeders and the user approves the alternative.**

**Fallback order for language:**\n1. Dual-Lat / Dual (English + Spanish Latino) — PREFERRED\n2. Latino only\n3. Castellano / Español (European Spanish)\n4. English + Spanish subtitles (only if 1-3 have 0 seeders)\n5. English only (last resort, only if user confirms)\n\n**CRITICAL: If the user provides specific magnet links, use them exactly as provided. Do not substitute them with other versions found via search unless the provided links fail to resolve or have no seeders and the user approves the alternative.**
## Laptop/remote usage via SSH\n\nWhen controlling the server from another machine—especially from this chat, desktop,\nor automation—treat `serverhogar` as the SSH host and the local skill tools as\nremote wrappers around `transmission-remote`.\n\n```bash\n# One-shot examples\nssh serverhogar 'transmission-remote -l'\nssh serverhogar \"transmission-remote -a '<magnet>' -w '/home/piro/multimedia/movies'\"\nssh serverhogar 'transmission-remote -t <id> --info'\n```\n\nIf the server's local skill copies the same reference docs, use those docs instead of\nre-explaining: `references/laptop-ssh-usage.md`.\n\nWhen many torrents accumulate — especially magnets that can't resolve metadata —\nthe **download queue** can fill up with dead entries, blocking real downloads\nfrom starting even when `download-queue-size` has available slots.\n
### How the queue works

- `download-queue-size` (default 5) limits how many torrents can be actively
  downloading concurrently.
- `queue-stalled-minutes` (default 30) — after N minutes with zero activity, a
  torrent is flagged as "Stalled" and its slot is freed.
- Torrents with `Percent Done: -nan%` (no metadata) **never** become "Stalled"
  because they haven't started any activity that the stall timer can measure.
  Result: they occupy queue slots permanently.

### Diagnosing queue clog

**Via CLI from laptop** — look for torrents with `n/a` size and `Idle` status:

```bash
ssh serverhogar 'transmission-remote -l'
# Look for: "n/a" in the Have column + "Idle" or "DownloadWait"
```

**Via RPC (detailed)** — use Python to query the daemon directly:

```bash
ssh serverhogar 'python3 ~/.hermes/skills/media/torrent-download/scripts/rpc-queue-check.py'
```

This shows each torrent's real status (`Downloading`/`DownloadWait`/`Seeding`),
metadata progress, peer count, queue position, and download rate. The CLI
`transmission-remote -l` collapses several RPC statuses into "Idle", hiding the
distinction between "downloading with no peers" vs "waiting for queue slot".

### Clearing stuck torrents

1. **Identify dead torrents** — those with `meta=0%`, `peers=0`, `down=0.0KB/s`,
   and `-nan%` progress. These will never download.

2. **Stop them** first to free queue slots instantly:
   ```bash
   ssh serverhogar 'transmission-remote -t <id1>,<id2>,... --stop'
   ```

3. **Remove definitively:**
   ```bash
   ssh serverhogar 'transmission-remote -t <id1>,<id2>,... --remove-and-delete'
   ```

4. **Verify** that previously-queued torrents transition to `Downloading`:
   ```bash
   ssh serverhogar 'transmission-remote -l'
   ```

### Adjusting queue size

If you frequently batch-add many torrents, increase the queue size on serverhogar:

```bash
# Edit settings.json via SSH:
ssh serverhogar 'jq ". \"download-queue-size\" = 8" ~/.config/transmission-daemon/settings.json > /tmp/tr-settings.json && mv /tmp/tr-settings.json ~/.config/transmission-daemon/settings.json'
# Then restart the daemon: transmission-remote --exit && transmission-daemon (on server)
ssh serverhogar 'transmission-remote --exit'
ssh serverhogar 'transmission-daemon'
```

WARNING: more concurrent downloads mean more bandwidth contention. Each
additional active download adds overhead. On a server connection (typically
~50-100 Mbps), more than 8 concurrent downloads can saturate the link and
slow everything down.

See `scripts/rpc-queue-check.py` for a re-runnable diagnostic script
that auto-highlights stuck torrents.

## Audio language verification

When the user asks about audio language (whether a torrent has Spanish/English/dual audio),
check the actual downloaded file's audio tracks with `ffprobe`:

```bash
# Check audio streams of a downloaded video file (on serverhogar)
ssh serverhogar 'ffprobe -v error -select_streams a \
  -show_entries stream=index,codec_name,language:stream_tags=language \
  -of json "/path/to/video.mkv"'
```

The output shows each audio stream with its `language` tag:
- `"eng"` = English
- `"spa"` = Spanish
- `"und"` = undetermined (usually English unless "Dual" is in the release name)
- Multiple streams = Dual/Multi audio

Torrent naming conventions for Spanish audio:
- **Dual-Lat** or **Dual** in the name = English + Spanish Latino (dual audio track)
- **Lat** or **Latino** in the name = Spanish only, no English
- **Esp** or **Español** = Spanish
- **Cast** or **Castellano** = Spanish (European/Spanish)

**Important:** Do NOT guess audio language from the file name alone if it doesn't
contain "Dual", "Lat", "Esp", or "Cast". YTS releases, most WEBRip x265 releases,
and generic HD releases are **English-only** even if the movie has a Spanish title.
Always prefer releases explicitly tagged with the language code.

See `references/audio-language-verification.md` for full usage and examples.

## Finding Spanish / dual audio torrents

When the user specifically requests Spanish (Latino) audio and the trackers
listed in this skill are exhausted, use this strategy:

1. **Search with Spanish keywords** on the TPB API:
   ```bash
   curl -sL "https://apibay.org/q.php?q=<movie>+dual+latino"
   curl -sL "https://apibay.org/q.php?q=<movie>+español+1080p"
   curl -sL "https://apibay.org/q.php?q=<movie>+dual-lat"
   ```

2. **Look for YG⭐ releases** — the YojimboGrupo (YG) tagging (e.g. `Dual YG⭐` or
   `Latino YG⭐`) is a reliable indicator of Spanish-language content on TPB.

3. **Trilogy/collection packs** — Search for `trilogía` or `colección` + `dual`.
   These are less common but consolidate all movies into one torrent.

4. **Fallback: English video + Spanish subtitles** — If no Spanish-audio torrent
   has seeders (a common situation for older niche releases on TPB), the practical
   solution is to download the well-seeded English version and add Spanish
   (Latino) subtitles separately. See the "Adding subtitles" section below.

### Spanish audio availability notes

- TPB has **limited Spanish Dual Latino** content compared to Spanish-specific
  trackers (DonTorrent, EliteTorrent, etc.)
- Spanish-specific trackers tend to use anti-bot protection (Anubis, Cloudflare)
  that cannot be bypassed programmatically
- YTS releases are **English-only** — excellent seeding but no Spanish audio
- Individual Dual releases for older movies (pre-2020) are rarely seeded; the
  trilogy pack may be the only option
- If even the trilogy pack has 0 peers, recommend English + subtitles as the
  only viable path

## Adding subtitles manually

If the user accepts English video + Spanish subtitles:

1. Download the subtitle file (`.srt` or `.vtt`) from a provider like
   OpenSubtitles or SubDivx. Subtitle files are tiny and download instantly.

2. Place the `.srt` file alongside the video file with the same base name.

   Mov files are often in a subdirectory; the subtitle file can go in the same
   subdirectory. For example:
   ```
   movies/The Equalizer 3 (2023) [YTS.MX]/
     The.Equalizer.3.2023.1080p.WEBRip.x265.10bit.AAC5.1-[YTS.MX].mp4
     The.Equalizer.3.2023.1080p.WEBRip.x265.10bit.AAC5.1-[YTS.MX].srt
   ```

3. Most media players (VLC, Jellyfin, Plex) auto-detect subtitles when they
   share the base name with the video file.

## Adding a download

When the user provides a magnet link or .torrent path, determine the target
directory from context (movies / series / music) and add it **via SSH to serverhogar**:

```bash
ssh serverhogar "transmission-remote -a '<magnet_link>' -w '/home/piro/multimedia/movies/'"
```

Or for a .torrent file:

```bash
ssh serverhogar "transmission-remote -a '/path/to/file.torrent' -w '/home/piro/multimedia/series/'"
```

### Checking status

```bash
ssh serverhogar 'transmission-remote -l'
```

Shows all active torrents with ID, progress, speed, and ETA.

### Post-completion verification

When a torrent reports `100%` / `Seeding` (or the user asks "¿cómo va?" shortly after adding), do not stop at the queue status — confirm the media physically landed in the destination and is playable:

```bash
# 1. Torrent state
ssh serverhogar 'transmission-remote -t <id> -i | grep -E "Name:|State:|Percent|Have"'

# 2. File/folder exists in the destination
ssh serverhogar 'ls -lh ~/multimedia/movies/ | grep -i <titulo>'

# 3. Playability sanity (ffprobe duration in seconds; a movie is 3000+)
ssh serverhogar 'find ~/multimedia/movies/ -maxdepth 2 -iname "*<titulo>*" -type f -exec ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {} \;'
```

Calibration data point (2026-08-11): a fresh 2.87 GB Dual-Lat magnet carrying only its 2 native public trackers (openbittorrent + opentrackr) resolved metadata in <20s and finished 100% in ~2 minutes with 30+ peers. `Idle`/`n/a` at add-time is expected, not alarming, when the magnet has working trackers — recheck before injecting trackers.

Sparse-swarm variant (2026-08-13, Identidad.Sustituta 2009 Dual-Lat, same 2 native trackers): with only 1-2 peers the torrent oscillates `Idle` ↔ `Downloading`, gaining a few percent per burst (2.87% → 5.7% over ~2 min, `Downloading` between Idle spells). This is HEALTHY — the swarm is small but alive; the tracker is serving peers, they just connect in ones. Handle it with: one `--reannounce` nudge, then check every 30-45s. Only escalate (tracker injection / replacement) when percent is frozen across consecutive checks AND peers = 0 — never when progress is creeping up between Idle spells.

### Post-download organization (Kodi naming)

After a torrent reaches 100% and is seeding (or stopped), organize the downloaded files according to Kodi naming conventions to ensure proper library scraping.

### Movies
1. Create a folder named `"Título (Año)"` inside `/home/piro/multimedia/movies/`.
2. Move the main video file (`.mkv`, `.mp4`, etc.) into that folder and rename it to `"Título (Año).ext"`.
3. Delete any auxiliary files (`.url`, `.vbs`, `.txt`, `.nfo`, sample folders, etc.).
4. Example:
   ```bash
   # Assuming the torrent downloaded to /home/piro/multimedia/movies/Moana.2026.1080p-Dual-Lat/
   mkdir -p "/home/piro/multimedia/movies/Moana (2026)"
   mv "/home/piro/multimedia/movies/Moana.2026.1080p-Dual-Lat/Moana.2026.1080p-Dual-Lat.mkv" "/home/piro/multimedia/movies/Moana (2026)/Moana (2026).mkv"
   rm -f "/home/piro/multimedia/movies/Moana.2026.1080p-Dual-Lat/Importante Leeme!.vbs" "/home/piro/multimedia/movies/Moana.2026.1080p-Dual-Lat/Descargar Películas, Series y Animes...url"
   rmdir "/home/piro/multimedia/movies/Moana.2026.1080p-Dual-Lat"
   ```

### Series
1. Ensure the series folder exists under `/home/piro/multimedia/series/` with a clean title in Spanish (no release tags).
2. Inside that folder, the torrent should have created a subfolder with the release name; move the video file out and rename it to `"Título - S01E02 - [Calidad] [Audio].ext"`.
3. Delete the release subfolder and any auxiliary files.
4. Example:
   ```bash
   # Assuming the torrent downloaded to /home/piro/multimedia/series/Stuar.No.Logra.Salvar.el.Universo.S01E08.2026.WEB-DL.1080p-Dual-Lat/
   mkdir -p "/home/piro/multimedia/series/Stuart no logra salvar el universo"
   mv "/home/piro/multimedia/series/Stuar.No.Logra.Salvar.el.Universo.S01E08.2026.WEB-DL.1080p-Dual-Lat/Stuar.No.Logra.Salvar.el.Universo.S01E08.2026.WEB-DL.1080p-Dual-Lat.mkv" "/home/piro/multimedia/series/Stuart no logra salvar el universo/Stuart no logra salvar el universo - S01E08 - 1080p WEB-DL Dual-Lat.mkv"
   rm -f "/home/piro/multimedia/series/Stuar.No.Logra.Salvar.el.Universo.S01E08.2026.WEB-DL.1080p-Dual-Lat/Importante Leeme!.vbs" "/home/piro/multimedia/series/Stuar.No.Logra.Salvar.el.Universo.S01E08.2026.WEB-DL.1080p-Dual-Lat/Descargar Películas, Series y Animes...url"
   rmdir "/home/piro/multimedia/series/Stuar.No.Logra.Salvar.el.Universo.S01E08.2026.WEB-DL.1080p-Dual-Lat"
   ```

**Note**: Always verify the file is playable (e.g., `ffprobe -v error -show_entries format=duration`) before deleting the source folder.

## Removing a torrent

```bash
ssh serverhogar 'transmission-remote -t <id> --remove-and-delete'
# or just --remove to keep files
```

## Message format from the user

The user sends torrent download requests in this exact format:

```
Tipo: movies|series|music
Link: <magnet_link_or_torrent_url>
```

Where `Tipo` is the content type and `Link` is the magnet link.

## Directory mapping

This user's convention:

| Content  | Target path                                   |
|----------|-----------------------------------------------|
| Movies   | `/home/piro/multimedia/movies/`               |
| Series   | `/home/piro/multimedia/series/` (subcarpeta por episodio, ver abajo) |
| Music    | `/home/piro/multimedia/music/`                |

Other content goes to `/home/piro/torrents/completos/` as a fallback (with
`/home/piro/torrents/incompletos/` for incomplete downloads).

**Series subfolder pattern (observado en el server 2026-08):** cada episodio
termina en su propia carpeta con el nombre completo del release, p.ej.
`/home/piro/multimedia/series/Stuart.no.logra.salvar.el.universo.S01E01.2026.WEB-DL.1080p-Dual-Lat/`.
No hace falta `-w` por episodio: el wrapper `remote_add_torrent.sh add series <magnet>`
rutea a `/home/piro/multimedia/series/` y la estructura interna del torrent crea
la subcarpeta sola. Jellyfin agrupa por serie aunque las carpetas se llamen por
episodio. NO crear `/multimedia/series/<SeriesName>/` manualmente — los
torrents de esta fuente (WEB-DL con carpeta raíz en el release) ya traen la
subcarpeta.

**Naming para mediacenter (preferencia del usuario):** los nombres estilo release (ej. .1080p-Dual-Lat) rompen el scraping de KODI/Jellyfin. Para asegurar la compatibilidad:
- Películas: La carpeta debe seguir el formato "Título (Año)" y el archivo interno debe estar limpio de etiquetas de release (ej. "Título (Año).mkv").
- Series: Consolidar a UNA carpeta por serie con título limpio en español y un archivo por episodio: "/series/Título/Título - S01E0X - 1080p WEB-DL Dual-Lat.mkv" (el marcador S01E0X es lo que parsean los scrapers). Workflow completo: skill `transmission-management` → `references/media-library-reorganization.md`.

## Kodi naming conventions
Consulte la guía detallada en `references/kodi-naming.md` para reglas de organización y renombrado post-descarga según el estándar de Kodi.

## Known torrent source sites

| Site | Notes | Search method |
|------|-------|---------------|
| **pelispanda.org** | Spanish/Latino content, series & movies | Browser scrape (anti-bot) → extract magnet links manually, OR use TPB API as fallback |
| **dontorrent.review** | Spanish tracker, heavy anti-bot (Anubis) | Cannot scrape programmatically — use TPB API fallback |
| **elitetorrent.net** | Spanish tracker, Cloudflare/Anubis | Cannot scrape — use TPB API fallback |
| **cinecalidad.to** | Spanish/Latino movies | Browser scrape possible, but TPB API preferred |
| **The Pirate Bay (apibay.org)** | JSON API, no anti-bot, global content | Primary programmatic search — see `references/tpb-api.md` |

**Strategy for pelispanda.org**: Since it's protected by anti-bot measures, navigate with browser to find the magnet links for specific episodes, then add them via `transmission-remote -a "magnet:..." -w /path/to/series/`. The TPB API (`apibay.org`) is the reliable programmatic fallback.

## Auto-notification on completion

The user wants to be notified automatically when a torrent finishes downloading.

**⚠️ VERIFY the cron exists before assuming it runs — it is documented here but NOT guaranteed deployed.** Checked 2026-08-09: `cronjob(action=list)` had NO "Torrent completion checker" job, even though the skill describes one. Also compare `~/.hermes/scripts/check_torrents.sh` against this skill's `scripts/check_torrents.sh` before relying on it — the deployed copy was the OLD noisy version (prints `NO_NEW_COMPLETED` every cycle = notification spam) while the skill's version is silent on no-news. If either is missing/stale, (re)create per the steps below and re-deploy the skill's script.

A cron job running every 5 minutes checks for newly completed torrents:

### Script (`~/.hermes/scripts/check_torrents.sh`)

A Bash script that:
1. Runs `transmission-remote -l` (or `ssh serverhogar 'transmission-remote -l'` from laptop) to list torrents
2. Parses completed ones (100% or "Done" status)
3. Tracks already-notified torrent IDs in `/tmp/.hermes_torrents_completed`
4. Only reports torrents not seen before
5. Emits `COMPLETED:` followed by the details, or `NO_NEW_COMPLETED`

The cron job uses `no_agent=True` so the script output is delivered verbatim
to the user's origin channel.

**Important:** The cron job runs in the context where Hermes is. If Hermes runs on serverhogar, use `transmission-remote -l` directly in the script. If Hermes runs on the laptop, wrap in `ssh serverhogar 'transmission-remote -l'`.

### Creating the cron job

```bash
cronjob(
  action="create",
  name="Torrent completion checker",
  script="check_torrents.sh",   # relative to ~/.hermes/scripts/
  no_agent=True,
  schedule="every 5m",
  deliver="origin"
)
```

## Automatic completion notifications

When the user asks to be notified when torrents finish, set up a **no-agent cron job** that checks `transmission-remote -l` periodically. The script must run wherever Hermes is — if on serverhogar, use direct commands; if on laptop, wrap in SSH.

### Steps

1. Create a script at `~/.hermes/scripts/check_torrents.sh` (adjust the `TR_CMD` line for your environment):

```bash
#!/bin/bash
# Auto-detect: use SSH if not on serverhogar
if hostname | grep -qi 'serverhogar'; then
  TR_CMD='transmission-remote'
else
  TR_CMD='ssh serverhogar transmission-remote'
fi

TR_STATE_FILE="/tmp/.hermes_torrents_completed"
TR_OUTPUT=$($TR_CMD -l 2>/dev/null)

COMPLETED=$(echo "$TR_OUTPUT" | awk '
/^ ID/ {next}
/^ Sum/ {next}
{ if ($2 == "100%" || $2 == "Done") {
    name = ""
    for(i = 2; i <= NF; i++) { if (i > 2) name = name " "; name = name $i }
    gsub(/^(100%|Done) /, "", name)
    print $1 ":" name }
}' 2>/dev/null)

if [ -z "$COMPLETED" ]; then exit 0; fi

touch "$TR_STATE_FILE" 2>/dev/null
NOTIFIED=""
while IFS=: read -r tid tname; do
    if [ -n "$tid" ] && ! grep -qx "$tid" "$TR_STATE_FILE" 2>/dev/null; then
        echo "$tid" >> "$TR_STATE_FILE"
        NOTIFIED="${NOTIFIED}✅ Torrent #${tid} completado: ${tname}"$'\n'
    fi
done <<< "$COMPLETED"

if [ -n "$NOTIFIED" ]; then echo "COMPLETED:"; echo "$NOTIFIED"; fi
```

✅ Auto-detects environment — works from serverhogar or laptop without modification.

**Critical**: the script must produce **empty stdout** when nothing is new — otherwise the user gets a notification every cycle. `exit 0` with no output = silent delivery.

2. Create the cron job with `no_agent=True` (script stdout is delivered verbatim):

```
cronjob(
  action='create',
  name='Torrent completion checker',
  schedule='every 5m',
  script='check_torrents.sh',
  no_agent=True,
  deliver='origin'
)
```

The state file `/tmp/.hermes_torrents_completed` tracks which torrent IDs have already been reported, so the user only gets one notification per completed torrent.

See `devops/cron-scheduling` skill for details on the `no_agent=True` watchdog pattern.

## Pitfalls

- **TPB API (apibay.org) Cloudflare behavior**: The API is behind Cloudflare
  and rate-limits aggressively. Two distinct failure modes exist:
  
  1. **Timeout (exit code 28)**: After 3-5 queries, curl hangs and times out.
  2. **Fake empty response**: A valid JSON array with a single item:
     `[{"id":"0","name":"No results returned","info_hash":"000...","seeders":"0",...}]`
     This is indistinguishable from genuinely empty search territory — always
     verify with a known-good query (e.g. a popular mainstream movie) before
     concluding there are no torrents. When either symptom appears, wait a few
     minutes or switch to a different search approach.
  
  Treat apibay.org as rate-limited; do NOT assume an empty response means the
  torrent doesn't exist.

- **Daemon not running on serverhogar**: If `ssh serverhogar 'transmission-remote -l'` returns exit code 1 with
  no output, the daemon is likely dead. Diagnose with
  `ssh serverhogar 'ps aux | grep transmission-daemon | grep -v grep'`. If empty, just start it:
  `ssh serverhogar 'transmission-daemon'`.
- **Config changes only apply on restart**: Transmission reads `settings.json`
  at startup only. After editing it, you **must** stop (`transmission-remote --exit`)
  and restart the daemon. There is no SIGHUP reload.
- **Torrent IDs change after restart**: After you stop/start transmission-daemon,
  torrent IDs can shift (e.g. ID 5 becomes ID 2). This can confuse the
  `check_torrents.sh` completion notification script because it tracks completed
  torrents by numeric ID. The state file at `/tmp/.hermes_torrents_completed`
  will have stale IDs. **Workaround**: delete the state file after a restart:
  `rm -f /tmp/.hermes_torrents_completed`

- **Config directory inconsistency**: If you start the daemon one time with
  `-g /some/path` and another time without `-g` (or with a different path),
  Transmission uses a different *resume* directory each time. Torrents added
  under one config won't appear when the daemon starts with a different config —
  they aren't lost, just stored in a different resume database. **Always use
  the same config directory** consistently. Both approaches in this skill use
  `-g /home/piro/.config/transmission-daemon`.

  **Migrating between config dirs with active torrents:** If you switch the
  daemon to a new config directory (e.g. from the default system config to
  `~/.config/transmission-daemon/`), Transmission reads the *new* resume
  directory and the torrents under the *old* config appear lost. They still
  exist in the old config's `resume/` dir — stop the daemon, copy the old
  `resume/` and `torrents/` directories (if any) into the new config dir, then
  restart. If you don't have the old resume data, simply re-add the magnet
  links after the switch.

- **"Unable to save resume file" error**: When running `--info` on a torrent,
  you may see `Error: Unable to save resume file: No such file or directory`.
  This means the daemon's config directory is missing the `resume/` and/or
  `torrents/` subdirectory. This happens when the daemon was started with a
  config directory that has `settings.json` but not the standard Transmission
  subdirectory structure — common when using `/etc/transmission-daemon/`
  directly without the user config dir. **Fix**: stop the daemon, switch to
  `~/.config/transmission-daemon/` (which should have `resume/`, `torrents/`,
  `blocklists/` already) using the `-g` flag, or create the missing dirs:
  ```bash
  mkdir -p /home/piro/.config/transmission-daemon/{resume,torrents,blocklists}
  ```

- **systemd integration**: Do not rely on `systemctl start transmission-daemon`.
  if the runtime user can't read `settings.json` (see **Permissions** above).
  Diagnose with `journalctl -xeu transmission-daemon.service`. The daemon uses
  `Type=notify` which may interact poorly with systemd sandboxing depending on
  configuration, but permissions are the far more common cause of timeout.
  If systemd start fails after fixing permissions, fall back to starting the
  daemon directly as a Hermes background process:
  ```
  terminal(
    command="transmission-daemon -f --log-level=error -g /home/piro/.config/transmission-daemon",
    background=true
  )
  ```
- **Permissions**: The daemon runs as the `debian-transmission` user by default
  and cannot write to `/home/piro/` directories. Override the service to run as
  `piro`, or start the daemon directly from the user's shell (which inherits
  the user identity automatically).

  **Critical: `settings.json` must be readable by the runtime user.** If the
  daemon's settings file is owned by `debian-transmission` with mode `600`
  but the service runs as `piro`, the daemon fails to read its config and
  times out during startup (90 seconds in `activating (start)` state).
  Fix:
  ```bash
  sudo chown piro:debian-transmission /etc/transmission-daemon/settings.json
  sudo chmod 640 /etc/transmission-daemon/settings.json
  ```
  Always check permissions first when diagnosing startup timeouts.
- **Background process lifecycle**: The daemon is a long-lived process that
  never exits on its own. Use `background=true` **without**
  `notify_on_complete=true` (it's a server, not a batch job).
- **Port conflicts**: Default peer port is 51413. If stuck in "activating",
  check port availability with `ss -tlnp | grep 51413`.
- **Anti-bot protected torrent sites**: Sites like dontorrent.review, 1337x,
  and TPB use Anubis, Cloudflare, or similar anti-bot measures. The browser
  and curl will get "Acceso denegado" or a proof-of-work challenge. Do NOT
  try to bypass these — use the **TPB API** (`apibay.org/q.php`) as a search
  backend instead (see "Searching for magnet links" above).
- **No-peer magnets**: Some magnet links (especially obscure or very new releases) may stay Idle despite tracker reports. Use `ssh serverhogar 'transmission-remote -t <id> --reannounce'` or manually add high-reliability public trackers to jumpstart discovery. If trackers report seeders but the torrent still doesn't connect, it may be due to a closed port (NAT/Firewall), which is common in residential networks without port forwarding. In this case, the only solution is to find a different torrent with more seeders or use a VPN with port forwarding. Verify after 10-15 seconds:
  `ssh serverhogar 'transmission-remote -t <id> --info | grep Peers'`. If
  still 0 after 10-15 seconds, the torrent won't download. Remove and find an
  alternative (see "Handling torrents that get no peers" above).

- **Metadata not resolving**: If a magnet shows `Percent Done: -nan%` and the
  name is still the hash or URL-encoded, the tracker(s) in the link are dead.
  Do NOT remove the torrent yet — add known-good public trackers with
  `--tracker-add` and force `--reannounce` (see \"Metadata not resolving\"
  section above). This is especially common with magnet links from Spanish
  trackers like tracker.torrentbay.to, which are often dead or slow.

**Proactive Tracker Injection:** To avoid the `-nan%` state entirely, add public trackers (e.g., `udp://tracker.opentrackr.org:1337/announce`) immediately after adding the torrent. This significantly increases the chance of metadata resolving quickly before the daemon marks the torrent as idle.
  `--tracker-add` and force `--reannounce` (see "Metadata not resolving"
  section above). This is especially common with magnet links from Spanish
  trackers like tracker.torrentbay.to, which are often dead or slow.

- **Base32 vs hex infohash**: Magnet links can use Base32-encoded infohashes
  (e.g. `urn:btih:zeqc2ymrnxcw3hy3hew6shkeqhq7mquk`) instead of the more
  common hex encoding. Transmission auto-converts Base32 to hex internally
  (e.g. `zeqc2y...` → `c9202d...`). This is transparent to the user — the
  magnet link is valid as-is, just don't expect the hex hash to match the
  Base32 string character-for-character when referencing the torrent.
  Transmission-remote will show the hex version in `--info` output.

- **Tracker-add may fail with "error setting announce list"**: Adding trackers
  via `transmission-remote -t <id> --tracker-add` can fail with this error
  when the torrent already has trackers in its magnet link. The tracker list
  is essentially locked after the initial metadata fetch begins. In this case,
  the only viable approach after adding is `--reannounce` to force the torrent
  to contact its existing trackers more aggressively. If metadata still won't
  resolve after that, the torrent has no working trackers and should be removed. When adding a new torrent, use
  the `-w` flag (`transmission-remote -a "<magnet>" -w /path/to/dir/` via SSH from laptop, or direct from server) to set
  the download directory upfront. If you forget and need to move an already-
  added torrent, use `transmission-remote -t <id> --move /new/path/`. Both
  work, but `-w` is cleaner for new torrents.
- **Field name gotcha**: The TPB API field for seed count is `seeders`, NOT
  `seeds`. The related script examples in this skill use `seeders` — if
  copying code from other sources, double-check the field name. Using
  `seeds` will silently return `None` for every result.
- **Duplicate magnet — wrapper "success" with no new ID**: The wrapper prints
  `RESULTADO_AGREGADO: ... responded: success` and a list tail even when
  Transmission silently dedupes by infohash. If the magnet's hash already
  exists in the queue (even as a completed 100% torrent), NO new ID appears in
  the tail. Observed 2026-08-09 (Avatar.Aang 1080p re-sent while #60 was at
  100%): wrapper said success, tail had no new ID. Before re-adding any magnet
  the user passes, verify with
  `ssh serverhogar 'transmission-remote -l | grep -i <title>'` — if present,
  tell the user it's already downloaded/queued. Quick cross-check: compare the
  magnet's `xl=` (total bytes) against the queue's displayed size (Transmission
  shows decimal GB, ~1e9 bytes/GB) — same name + same size = almost certainly
  the same torrent, confirm with the Hash check. Second observed occurrence
  2026-08-13 (Minions.y.Monstruos re-sent while #70 sat at 100% Seeding with
  identical 2.87 GB = xl=2874146816). Same for "alternatives": check
  `transmission-remote -t <id> -i | grep Hash:` against the new magnet's
  `urn:btih:`; a real alternative must have a different infohash.
- **Telegram rejects .torrent files**: Telegram cannot send or receive `.torrent`
  files directly — the platform returns `Unsupported document type '.torrent'`.
  If the user tries to send a .torrent file, ask them to **compress it in a .zip**
  first, or extract the magnet link / info_hash from it yourself via the
  terminal and add it to Transmission directly.
- **YTS releases as fallback**: When x265/HEVC lightweight versions have
  zero peers, try YTS releases (search with `YTS` in the query). They use
  optimized x264 at 1080p with good size-to-quality ratio (1.2-2 GB per
  movie) and are almost always well-seeded (50-150+ seeders). Example:
  `query=equalizer+2+2018+YTS`.

- **Dead torrents clog the download queue**: Magnets that can't resolve
  metadata (`Percent Done: -nan%`, 0 peers) sit in the download queue
  permanently. Because they never start any measurable activity, the
  `queue-stalled-minutes` timer never triggers. They occupy `download-queue-size`
  slots indefinitely, preventing queued torrents from starting. **Diagnose**
  by checking how many torrents show `meta=0%` with `peers=0` via the RPC
  diagnostic script. **Fix**: stop and remove the dead torrents, then verify
  queued torrents transition to active downloading.

# Verification

After starting the daemon, run:

```bash
# From laptop CachyOS:
ssh serverhogar 'transmission-remote -l'

# From serverhogar directly:
transmission-remote -l
```

If you see a table header (even with no torrents), the daemon is alive and accepting commands.

## Remote laptop wrapper script

Use the laptop-side helper to control the server daemon safely over SSH:

```
/home/migbert/.local/bin/remote_add_torrent.sh add <movies|series|music> <magnet|.torrent url>
/home/migbert/.local/bin/remote_add_torrent.sh list
/home/migbert/.local/bin/remote_add_torrent.sh info <id>
```

This wrapper:
- Normalizes the target directory by content type.
- Avoids shell-quoting issues with `&` in magnet links by passing the payload through a temp file/JSON path, then invoking `transmission-remote` on the server.
- Verifies addition and prints a short tail of the current torrent list.

Do not add `192.168.1.*` to `rpc-whitelist` unless the user explicitly asks for web UI access from the laptop; SSH control is the supported default.
