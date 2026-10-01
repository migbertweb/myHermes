# Syncthing-based `.hermes` Sync

Keep `~/.hermes/` in sync between a server and laptop over LAN using Syncthing. The goal is **two independent instances** sharing the same credentials, skills, cron jobs and auth files — but each with its own personality (via per-machine `config.yaml`), session history (`state.db`), and memory (`memory_store.db`).

**What syncs:** `secrets.yaml`, `skills/`, `cron/`, `auth/`, `Cuadernos/`, `SOUL.md` — the shared knowledge layer.

**What stays per-machine:** `config.yaml`, `.env`, `state.db`, `memory_store.db`, `sessions/`, `logs/`, `cache/`, `bin/`, `hermes-agent/`, `lsp/`, `pairing/` — the operational and identity layer. Each machine keeps its own API keys, credentials, sessions, memory, and caches.

This is a companion to the main `hermes-remote-access` skill — it covers the Syncthing-specific setup and the `.stignore` exclusion patterns that make this split work.

## Prerequisites

- Syncthing already on the laptop (or install from https://syncthing.net)
- Both machines on the same LAN
- SSH key-based auth between them (useful for diagnostics, not required by Syncthing itself)
- Hermes Agent installed on both machines (or at least on the server to seed the config)

## Server Setup (the source of truth)

### 1. Install Syncthing binary (no sudo needed)

```bash
curl -sL "https://github.com/syncthing/syncthing/releases/download/v1.29.5/syncthing-linux-amd64-v1.29.5.tar.gz" | tar xz -C /tmp/
mkdir -p ~/.local/bin
cp /tmp/syncthing-linux-amd64-v1.29.5/syncthing ~/.local/bin/
chmod +x ~/.local/bin/syncthing
```

### 2. Generate config and get the Device ID

```bash
~/.local/bin/syncthing -generate=~/.config/syncthing
```

This prints the Device ID — copy it down. Example format:
`YFN74QF-5EBAEPY-4GOVVO7-LBS52AB-RRLS6YF-F65COL4-D65G7QD-DNMEKQB`

### 3. Configure the shared folder

Edit `~/.config/syncthing/config.xml` and add a folder entry for `.hermes` (replacing the default folder):

```xml
<folder id="hermes-config" label="Hermes Config" path="/home/piro/.hermes"
        type="sendreceive" rescanIntervalS="60" fsWatcherEnabled="true"
        fsWatcherDelayS="10" ignorePerms="false" autoNormalize="true">
    <filesystemType>basic</filesystemType>
    <device id="YOUR-DEVICE-ID-HERE" introducedBy="">
        <encryptionPassword></encryptionPassword>
    </device>
    <!-- ... rest of folder options ... -->
</folder>
```

Also set the device name for clarity:
```xml
<device id="..." name="servidor-hermes" compression="metadata" ...>
```

### 4. Create `.stignore` with exclusion patterns

Inside `.hermes`, create `~/.hermes/.stignore`. This file is **local per machine** — the server and laptop can have slightly different exclusions. What matters is which files sync.

#### Server `.stignore` example

```
// === EXCLUSIONES PARA HERMES (Servidor) ===
// Archivos locales por máquina — NO sincronizar

// Base de datos de sesiones — única por máquina (se corrompe con acceso concurrente)
state.db
state.db-shm
state.db-wal

// Base de datos de memoria — única por máquina (cada instancia su propia memoria)
memory_store.db
memory_store.db-shm
memory_store.db-wal

// --- Configuración (local por máquina) ---
// config.yaml define la personalidad y capacidades de cada instancia
config.yaml
.env

sessions/
logs/
cache/
audio_cache/
image_cache/
images/
sandboxes/
pastes/
bin/
node/
hermes-agent/
hooks/
lsp/
pairing/

*.lock
*.pid
.hermes_history
interrupt_debug.log
.update_check
.skills_prompt_snapshot.json
context_length_cache.yaml
ecosistema_hermes.txt
kanban.db
processes.json
gateway_state.json

models_dev_cache.json
ollama_cloud_models_cache.json
provider_models_cache.json

.stversions/
```

#### Laptop `.stignore` example

```ignore
// === EXCLUSIONES LOCALES (LAPTOP) ===

// Base de datos de sesiones — única por máquina
state.db
state.db-shm
state.db-wal

// Base de datos de memoria — única por máquina
memory_store.db
memory_store.db-shm
memory_store.db-wal

// Configuración local (cada máquina su personalidad)\nconfig.yaml\n.env

// Sesiones y logs locales
sessions/
logs/

// Caches y archivos temporales
cache/
audio_cache/
image_cache/
images/
sandboxes/
pastes/
node/

// Archivos instalados (pueden diferir por versión de SO)
bin/
hermes-agent/
lsp/
hooks/

// Locks y estado local
*.lock
*.pid
.hermes_history
interrupt_debug.log
.update_check
.skills_prompt_snapshot.json
context_length_cache.yaml
kanban.db
processes.json
gateway_state.json

// Caches de modelos (se regeneran solos)
models_dev_cache.json
ollama_cloud_models_cache.json
provider_models_cache.json

// Archivos de versiones de Syncthing
.stversions/

// Archivos de pairing (son locales por máquina)
pairing/
```

> **Key distinction:** `skills/`, `memories/`, `cron/`, and `skins/` are deliberately **NOT** excluded — these are the shared knowledge layer you want on every machine. Only machine-local operational data (config, sessions, DB, logs, caches, installed code) is excluded.

### 5. systemd user service

Use the built-in service file from the tarball:

```bash
cp /tmp/syncthing-linux-amd64-v1.29.5/etc/linux-systemd/user/syncthing.service \
   ~/.config/systemd/user/syncthing.service
```

Edit it to point to the static binary:
```
ExecStart=%h/.local/bin/syncthing serve --no-browser --no-restart --logflags=0
```

Enable and start:

```bash
systemctl --user daemon-reload
systemctl --user enable syncthing.service
systemctl --user start syncthing.service
```

**Note:** If the service fails with `Failed to acquire lock: no such file or directory`, create the state directory first:

```bash
mkdir -p ~/.local/state/syncthing
```

## Laptop Setup

### 1. Open the Syncthing GUI

Open `http://localhost:8384` in the laptop's browser.

### 2. Add the server as a remote device

- **Actions → Add Remote Device**
- Device ID: paste the server's Device ID
- Device Name: `servidor-hermes`
- Addresses: leave as `dynamic` (auto-discovers on LAN)

### 3. Add the shared folder

- **Actions → Add Folder**
- **Folder ID:** `hermes-config` (must match the server)
- **Folder Path:** `/home/<laptop-user>/.hermes`
- **Type:** Send & Receive
- **Sharing tab:** check `servidor-hermes`
- **Ignore Patterns tab:** confirm the `.stignore` patterns match (they'll sync from the server on first connection)

### 4. (If laptop doesn't have Hermes yet) Install Hermes

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

The first sync will seed all config, skills, and memory from the server.

## Why These Exclusions

| Excluded | Reason |
|----------|--------|
| `state.db*` | SQLite sessions DB — corrupts if both machines write concurrently |
| `memory_store.db*` | Holographic memory DB — each instance has independent memory and personality |
| `config.yaml` | Each machine's provider/model/plugin personality — independent per instance |
| `.env` | API keys and credentials — per-machine; avoids exposing both instances if one is compromised |
| `sessions/` | Per-machine session history |
| `logs/` | Per-machine logs |
| `cache/*` | Machine-specific caches (regenerated automatically) |
| `*.lock`, `*.pid` | Runtime locks — machine-specific |
| `*_cache.json` | Model provider caches (regenerated) |

**Not excluded (auto-synced):** `secrets.yaml`, `skills/`, `cron/`, `auth/`. Shared knowledge and cross-machine credentials stay consistent across all instances.

## Config Sync — Manual (confirm before copying)

Since `config.yaml` is excluded from Syncthing, each machine's config will diverge naturally — that's intentional (each instance has its own personality and capabilities). Credentials (`.env`, `secrets.yaml`) sync automatically via Syncthing, so API keys stay consistent across all machines.

When you want to **push** config changes from one machine to the other, do it manually with SCP.

### Prerequisite: Bidirectional SSH

Both directions must work without a password:

| Direction | Command | When to use |
|-----------|---------|-------------|
| Laptop → Server | `ssh piro@<server-ip>` | Copy laptop config to server |
| Server → Laptop | `ssh migbert@<laptop-ip>` | Copy server config to laptop |

### Push laptop config to server

```bash
scp ~/.hermes/config.yaml piro@server-ip:~/.hermes/config.yaml
```

### Pull server config to laptop

```bash
scp piro@server-ip:~/.hermes/config.yaml ~/.hermes/config.yaml
```

### Important

- **Always confirm with the user** before copying — `config.yaml` affects which providers, models, API keys, TTS voices, and skill directories are active on each machine. A server config with `provider: openrouter` might use tokens the laptop shouldn't.
- After copying, restart Hermes or start a new session for config changes to take effect.
- `secrets.yaml` syncs automatically via Syncthing — no manual copy needed. `.env` is **not synced** intentionally (each machine has its own API keys). If you ever need to force-resync `secrets.yaml`, stop Syncthing on both sides, copy the file, then restart.

## Pitfalls

- **`state.db` and `memory_store.db` corruption is silent and permanent.** Don't include these in the sync. Each machine needs its own sessions database and memory database.
- **First sync seeds the laptop.** If the laptop already has a `.hermes` with local changes, Syncthing will conflict-resolve. Move the laptop's existing `.hermes` aside before the first sync if you want a clean copy from the server.
- **Syncthing must run on both machines.** The server service is configured above; on the laptop, Syncthing is likely already running if the user uses it for other sync (phone, etc.).
- **`~/.local/state/syncthing/` must exist before systemd starts.** If the service fails immediately, create this directory manually.
- **Editing config.xml does NOT auto-reload new devices.** After adding a device entry or folder to `config.xml` on a running Syncthing instance, the server may keep logging `Connection rejected: unknown device`. You MUST run `systemctl --user restart syncthing.service` (or `killall -HUP syncthing`) after any manual config.xml edits for the new device to be recognised. Simple config value changes (GUI port, name) often auto-reload; device and folder additions do not.
- **Must add the laptop's device ID in two places in config.xml:** both as a `<device>` entry at the top level (so the server recognises it) AND as a `<device>` entry inside the `<folder>` block (so the folder is shared with it). Omitting either one keeps the pair unconnected.
- **`.env` and `secrets.yaml` — different sync behavior:** `secrets.yaml` is auto-synced (shared credentials across machines). `.env` is **excluded** from sync — each machine keeps its own API keys and credentials independently. If you need to force-resync credentials on one machine (e.g. it got a stale copy of `secrets.yaml`), stop Syncthing on both sides temporarily, copy the file manually, then restart.
