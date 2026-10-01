---
name: server-ssh
description: SSH from laptop to serverhogar. Prefer rsync over scp.
---

# SSH a Server serverhogar

Conexión desde la laptop CachyOS al servidor Ubuntu (serverhogar).

## Datos de conexión

| Campo | Valor |
|-------|-------|
| Hostname (alias) | `serverhogar` |
| IP | `192.168.1.8` |
| Usuario | `piro` (NO `migbert`) |
| Puerto | `22` |
| Llave | `~/.ssh/id_ed25519` (ed25519, autenticación por llave) |

## Conectar

```bash
ssh serverhogar
# usa el alias definido en ~/.ssh/config — User piro ya configurado
```

**Pitfall:** NO uses `ssh migbert@192.168.1.8` — el usuario del server es `piro`, no `migbert`. El alias `serverhogar` ya tiene el usuario correcto. Usar el usuario equivocado causa `Permission denied (publickey,password)`.

## Config SSH en la laptop (`~/.ssh/config`)

```
Host serverhogar
     HostName 192.168.1.8
     User piro
     Port 22
```

## Directorios importantes en el server

| Ruta | Descripción |
|------|-------------|
| `~/multimedia/movies/` | Biblioteca de películas (Kodi) |
| `~/movies/` | Carpeta creada por error — NO usar |

**Pitfall:** La carpeta de películas es `~/multimedia/movies/` (minúscula `multimedia`). Si no existe, el path está mal. Verificar con `ls` antes de copiar.

## Transferring Large Files (laptop → server)

### Pitfall: scp genera errores de shell en serverhogar

`scp -r` a serverhogar produce errores de inicialización de zsh/gitstatus:

```
(anon):setopt:7: can't change option: monitor
[ERROR]: gitstatus failed to initialize.
(eval):1: can't change option: zle
scp: realpath .../: No such file
```

Esto puede causar que scp falle o copie parcialmente.

**Solución:** Usar `rsync` en lugar de `scp` para transferencias a serverhogar.

```bash
rsync -av --progress "/local/path/" serverhogar:~/multimedia/movies/Destino/
```

### Background para archivos grandes

Para transferencias grandes (>1GB, películas, etc.):

1. Usar `terminal(background=true, notify_on_complete=true)` para evitar timeout de sesión.
2. `rsync` con `--progress` para seguimiento.
3. Verificar con `ssh serverhogar "ls -lh ~/ruta/destino/"` al terminar.

```bash
rsync -av --progress "/home/migbert/Escritorio/Carpeta/" serverhogar:~/multimedia/movies/Carpeta/
```

## Verificación

```bash
ssh serverhogar "hostname && whoami"
# Debe responder: serverhogar (o el hostname del server) + piro
```

## Referencias

- `references/kodi-series-renaming.md` — Convención KODI para series (temporadas/episodios)
- `references/kodi-movies-renaming.md` — Convención KODI para películas (carpeta + archivo)

## Workflow recomendado

1. **Verificar primero** — confirmar que el directorio destino existe antes de copiar.
2. **Usar rsync, no scp** — rsync es más robusto para serverhogar.
3. **Background para archivos grandes** — evitar timeout de sesión.
4. **Verificar al final** — `ls -lh` en destino para confirmar tamaños.
5. **Copias masivas** — listar archivos origen, verificar año/título con web_search, crear cada carpeta con `mkdir -p`, lanzar rsync en background por archivo y esperar confirmación de tamaño.
6. **No duplicar carpetas** — comprobar existencia previa con `ssh serverhogar "ls -d '/home/piro/multimedia/movies/Título (Año)'"` antes de crear/transferir.

## Notas

- Usuario del server: `piro`
- Usuario de la laptop: `migbert`
- El server corre Ubuntu Server sin GUI
- Kodi gestiona la biblioteca multimedia en `~/multimedia/`
- Ver también: `laptop-ssh` para la dirección inversa (server → laptop)
