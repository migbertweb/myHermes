# Laptop / Hermes TUI -> serverhogar cheat sheet

Remote control of Transmission running as `piro` on `serverhogar`.

## One-liners

```bash
ssh serverhogar 'transmission-remote -l'
ssh serverhogar "transmission-remote -a '<magnet>' -w '/home/piro/multimedia/movies'"
ssh serverhogar 'transmission-remote -t <id> --info'
ssh serverhogar 'transmission-remote -t <id> --stop'
ssh serverhogar 'transmission-remote -t <id> --remove-and-delete'
```

## Web UI

```
http://192.168.1.8:9091/transmission/web/
```

Default LAN host `serverhogar` resolves in the home LAN; if not, replace with `192.168.1.8`.

## Directory mapping

| Content | Target path |
| Movies | `/home/piro/multimedia/movies/` |
| Series | `/home/piro/multimedia/series/<name>/` |
| Music | `/home/piro/multimedia/music/` |

## Notes

- Make sure `rpc-whitelist` on the daemon allows the laptop subnet, and `rpc-authentication-required` is `false` for passwordless use.
- Config changes require stop/restart: `transmission-remote --exit && transmission-daemon`.
- Torrent IDs may change across restarts; if notification statefile uses IDs, delete `/tmp/.hermes_torrents_completed` after restart.
- Never try to scrape anti-bot sites from the laptop; fall back to the TPB API skill workflow.
