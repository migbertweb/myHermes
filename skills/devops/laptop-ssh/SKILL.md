---
name: laptop-ssh
description: Conectar via SSH desde el server a la laptop CachyOS (192.168.1.17)
---

# SSH a Laptop CachyOS

## Datos de conexión

| Campo | Valor |
|-------|-------|
| Hostname | `cachyos-x8664` |
| IP | `192.168.1.17` (wlan0) |
| Usuario | `migbert` |
| Puerto | `22` |
| Alias SSH | `cachy` (definido en `~/.ssh/config`) |

## Conectar

```bash
ssh cachy
# o directamente:
ssh migbert@192.168.1.17
```

## Config SSH en el server (`~/.ssh/config`)

```
Host cachy
     HostName 192.168.1.17
     User migbert
     Port 22
     StrictHostKeyChecking accept-new
```

## Si falla por Permission denied

La llave pública del server (`~/.ssh/id_ed25519.pub`) debe estar en `~/.ssh/authorized_keys` de la laptop (usuario `migbert`).

Para autorizar desde la laptop:
```bash
# copiar la llave pública del server y agregarla:
cat id_ed25519.pub >> ~/.ssh/authorized_keys
# o usar ssh-copy-id si hay acceso por password:
ssh-copy-id migbert@192.168.1.17
```

## Verificación

```bash
ssh cachy "hostname && whoami && ip -4 addr show | grep inet"
```

Debe responder con:
- `cachyos-x8664`
- `migbert`
- IP `192.168.1.17/24` in `wlan0`

## Transferring Large Files
For large files (movies, ISOs), use `rsync` with the `-avhP` flags to ensure progress tracking and the ability to resume interrupted transfers.
- **Pitfall:** Large transfers may hit the `terminal()` tool timeout (default 600s). 
- **Solution:** Run the transfer in the background using `terminal(background=true, notify_on_complete=true)` to avoid session timeouts and allow the process to complete autonomously.

Example:
```bash
rsync -avhP --progress cachy:'/path/to/remote/file' /local/destination/
```

## Notas

- Usuario del server: `piro`
- Usuario de la laptop: `migbert`
- La laptop tiene Docker (`172.17.0.1/16`)
- Autenticación por llave ed25519
