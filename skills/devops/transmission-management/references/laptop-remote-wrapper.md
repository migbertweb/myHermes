# Laptop-side wrapper script

Location: `scripts/remote_add_torrent.sh` on the local machine, or
`~/.local/bin/remote_add_torrent.sh` on the laptop.

## Requirements

- `ssh` key-based auth to the remote host (`serverhogar piro`)
- REMOTE_HOST env/arg resolved to the SSH hostname or IP

## Usage

```bash
remote_add_torrent.sh add <movies|series|music> <magnet|https://...torrent>
remote_add_torrent.sh list
remote_add_torrent.sh info <id>
```

## Behavior

- Validates content type and maps to `/home/piro/multimedia/<type>`
- For HTTP/HTTPS URLs, fetches the `.torrent` file to `/tmp/<filename>` on the remote server before adding it
- Quotes remote args via Python `shlex.quote` to avoid SSH fragmenting `-w`/`-a`
- Prints: destination path, remote command, add result, and last few lines of `transmission-remote -l`

## Integration with Hermes

The Hermes TUI can invoke this script directly via `terminal(command="remote_add_torrent.sh add movies '<magnet>'")` or from a skill prompt. Prefer this wrapper over inline SSH one-liners when adding torrents from the laptop.


