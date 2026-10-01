---
name: syncthing
description: Manage and troubleshoot Syncthing — status checks, stignore management, common errors, rescan workflows.
category: devops
---

# Syncthing Management

## Overview

Syncthing keeps `~/.hermes` (skills, cron, auth) in sync between laptop and server, plus vaults and general files. Each machine keeps its own config.yaml, .env, sessions, and databases — those are excluded via per-machine `.stignore`.

## Quick Reference

| Action | Command |
|--------|---------|
| Service status | `systemctl --user status syncthing --no-pager -l` |
| Recent errors | `journalctl --user -u syncthing --since "1h ago" -p err --no-pager` |
| Full recent log | `journalctl --user -u syncthing --since "2h ago" --no-pager` |
| Web UI | `http://127.0.0.1:8384` |
| Config file | `~/.local/state/syncthing/config.xml` (laptop) / `~/.config/syncthing/config.xml` (server) |
| REST API key | `grep -oP '<apikey>\\K[^<]+' ~/.config/syncthing/config.xml` (server) / `~/.local/state/syncthing/config.xml` (laptop) |
| stignore location | `<folder-path>/.stignore` (one per synced folder) |

## Hermes Config stignore

Located at `~/.hermes/.stignore`. Kept in sync between laptop and server manually (they don't sync each other's stignore). Common exclusions:

```
state.db, state.db-shm, state.db-wal    # session DB — machine-unique
memory_store.db                          # memory DB — machine-unique
config.yaml                              # local personality
.env                                     # local credentials
profiles/                                # perfiles — SOLO laptop (server tiene su propia identidad)
sessions/, logs/                         # ephemeral state
cache/, bin/, node/, lsp/               # caches & binaries
hermes-agent/, hooks/
*.lock, *.pid
.hermes_history, *_cache.json
.stversions/                             # Syncthing versions
pairing/
```

What **does** sync: `skills/`, `cron/`, `auth/`, `secrets.yaml`.

## Pitfall: DBs sqlite dentro de carpetas sincronizadas (cron/, kanban/)

`cron/` syncs by default — and `~/.hermes/cron/executions.db` is a sqlite DB
both machines' gateways write independently. Syncing it corrupts it
(`database disk image is malformed`, `cron/executions.py` recover fails,
gateway exits 1). Same for the kanban boards: `~/.hermes/kanban/boards/*/kanban.db`
are machine-local (each host runs its own dispatcher) — a mid-sync copy leaves
a schemaless `kanban.db` that makes the dispatcher throw `no such table: tasks`
on every tick (the corrupt-board quarantine does NOT catch schemaless files).

Required stignore entries on BOTH machines — use GLOBS, not exact filenames.
An exact `cron/executions.db` pattern still lets `executions.db.corrupt-*`
backups and `*.sync-conflict-*` leftovers sync (seen 2026-08-08: the laptop's
corrupt backup propagated to the server the same day). Final patterns:
```
cron/*.db
cron/*.db-shm
cron/*.db-wal
kanban/
*.sync-conflict-*
```

Fix for an already-corrupt `cron/executions.db`: move it aside (jobs live in
`cron/jobs.json`, not executions.db), restart the gateway — the scheduler
regenerates it. If the gateway hangs in `deactivating` after the restart
(shutdown stuck joining the dead cron-scheduler thread), SIGKILL the MainPID
directly — systemd relaunches it:
`systemctl --user show hermes-gateway -p MainPID --value` → `kill -9 <pid>`.
(`systemctl --user kill -s SIGKILL` can fail with "Failed to send signal to
auxiliary processes: Invalid argument" — the direct `kill -9` works.)

## Pitfall: `state/` del gateway genera conflictos de heartbeat

Ambos gateways escriben `~/.hermes/state/gateway.heartbeat` y `gateway.lifecycle.json` en cada tick — si `state/` no está en el stignore, Syncthing lo sincroniza y genera `gateway.sync-conflict-<ts>-<device>.heartbeat` a montones (visto 2026-08-23: 11 conflictos en un día). Regla: `state/` en el stignore de AMBAS máquinas (estado local, como `state.db`). Limpiar residuos: `rm -f ~/.hermes/state/gateway.sync-conflict-*`.

## Pitfall: `(?d)` no siempre se aplica en el índice

Un patrón `(?d)dir/` existente en stignore no garantiza que Syncthing borre el dir: el índice puede seguir reportando `ignored: False` y el needDelete persiste tras el rescan. Fix pragmático: `rm -rf <dir>` manual en la máquina + rescan — con `(?d)` ya en stignore no vuelve (visto 2026-08-23 con `state-snapshots/`).

## Pitfall: stignore mal editado = Syncthing re-pushea lo borrado

Si una entrada de stignore queda mal escrita (p. ej. `\n` literales dentro de
un comentario, o se edita solo un lado), Syncthing SIGUE sincronizando esa
carpeta. Borrar manualmente los archivos en el destino NO basta: vuelven en el
siguiente sync (visto 2026-08-23 con `profiles/`: se borraron los perfiles en
el server y reaparecieron ~15 min después porque el stignore del laptop estaba
roto y el del server no tenía la regla).

Regla: editar el stignore en AMBAS máquinas (no se sincronizan entre sí), con
entradas reales por línea (sin `\n` literales — usar patch con newlines reales
o write_file), y forzar rescan en ambas tras editar:

```bash
APIKEY=$(grep -oP '<apikey>\K[^<]+' ~/.local/state/syncthing/config.xml)
curl -s -X POST -H "X-API-Key: $APIKEY" "http://127.0.0.1:8384/rest/db/scan?folder=hermes-config"
```

En el server la config está en `~/.config/syncthing/config.xml` (NO en
`~/.local/state/syncthing/` como en la laptop).

## Pitfall: Corrupción XML en config.xml

Ediciones manuales (especialmente via `sed` o `patch` mal aplicados) pueden romper las etiquetas de cierre de Syncthing (p. ej. `<sendOwnership>` cerrado por `</syncOwnership>`).

**Síntoma:** Syncthing falla al iniciar con `XML syntax error on line X: element <Y> closed by </Z>` en los logs de systemd.

**Fix:** Corregir la etiqueta de cierre para que coincida exactamente con la de apertura. Reiniciar el servicio.

## Troubleshooting: "directory has been deleted on a remote device but contains ignored files"

### Cause
A remote device deleted a directory that locally contains files matching stignore patterns. Syncthing refuses to delete directories with untracked content to prevent data loss.

### Diagnosis
1. `systemctl --user status syncthing --no-pager -l` — look for `Failed to sync` or `Folder failed to sync`
2. Open `http://127.0.0.1:8384` — check folder shows "No sincronizado"
3. Click into the folder, click "Elementos fallidos" to see exact path + error

### Solutions

**A) Manual delete** (quick fix):
```bash
rm -rf <path-to-directory>
# Then force rescan
```

**B) (?d) prefix in stignore** (prevents recurrence):
```
(?d)state-snapshots/
```
The `(?d)` prefix tells Syncthing it may delete directories matching the pattern even with ignored content inside.

### Force rescan after fix
```bash
APIKEY=$(grep -oP '<apikey>\K[^<]+' ~/.local/state/syncthing/config.xml)
curl -s -X POST -H "X-API-Key: $APIKEY" "http://127.0.0.1:8384/rest/db/scan?folder=hermes-config"

# Verify completion
curl -s -H "X-API-Key: $APIKEY" "http://127.0.0.1:8384/rest/db/completion?folder=hermes-config"
```
Response fields to check: `completion: 100`, `needDeletes: 0`, `needItems: 0`.

## Comparing stignore between machines

```bash
# laptop → server
ssh serverhogar "cat ~/.hermes/.stignore"

# server → laptop
ssh cachy "cat ~/.hermes/.stignore"
```

Both machines should have compatible stignore (exclude the same things). Differences in ordering or extra entries are harmless as long as no critical file is excluded on one side but not the other.

## Config inspection

```bash
# List folders and their devices
grep -E '(folder|device) id=' ~/.local/state/syncthing/config.xml

# Get named devices
grep -A2 '<device id=' ~/.local/state/syncthing/config.xml | grep -E '(device|name=)'
```

Folder-device mapping matters: if a folder is shared with the wrong device, Syncthing can't sync it.
