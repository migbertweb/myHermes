---
name: tuya-smart-plugs
description: Controla enchufes inteligentes Tuya desde el servidor con tinytuya. TV sala, TV cuarto y Tramontina.
platforms: [linux]
tags: [tuya, smart-plugs, iot, smart-home, wifi-plugs]
---

# Integración de Enchufes Inteligentes Tuya

> **Librería:** [TinyTuya](https://github.com/jasonacox/tinytuya) v1.18.1
> **Estado:** ✅ TV cuarto funcionando · ⚠️ Sala no responde (buscar IP) · ⚠️ Tramontina sin IP local
> **Última prueba:** `tuya cuarto on/off` — OK (28/jun/2026)

## 📡 Descripción

Control local de enchufes Tuya en la red doméstica. TinyTuya se comunica directamente con los dispositivos sin pasar por la nube de Tuya.

## 📋 Dispositivos Configurados

| Nombre | Device ID | IP | Versión | Estado |
|--------|-----------|-----|---------|--------|
| **TV cuarto** | `5676087234ab950d3f67` | 192.168.1.2 | v3.3 | ✅ Funciona |
| **TV sala** | `eb36eef3376660c896dcqo` | 192.168.1.4 | v3.5 | ⚠️ Desconectada físicamente |
| **Tramontina** | `vdevo178131546308609` | — (IPv6 only) | v3.1 | ⚠️ Sin IP local |

## 🖥️ Comandos Rápidos

```bash
# Comando principal (script ejecutable en PATH)
tuya cuarto on
tuya cuarto off
tuya cuarto status
tuya sala on
plugs

# Invocación directa si el wrapper falla (usa el venv del entorno Tuya)
/home/piro/.tuya-venv/bin/python /home/piro/.hermes/tuya_control.py cuarto on
```

- `tuya` → `/home/piro/.local/bin/tuya` (script bash/python con venv propio, requiere permisos de ejecución `chmod +x`)
- `plugs` → `/home/piro/.local/bin/plugs` (bash wrapper que muestra todos)
- 📖 Guía de descubrimiento y troubleshooting: `references/discovery-guide.md`

## 🐍 Script de Control

**Ruta:** `/home/piro/.hermes/tuya_control.py` (copia en skill: `scripts/tuya_control.py`)

```python
DEVICES = {
    "cuarto": {
        "id": "5676087234ab950d3f67",
        "ip": "192.168.1.2",
        "key": "k;q<#)ei6~H2R<`p",
        "version": 3.3
    },
    "sala": {
        "id": "eb36eef3376660c896dcqo",
        "ip": "192.168.1.4",
        "key": "!5fV~`:v7+i@@nIL",
        "version": 3.5
    },
    "tramontina": {
        "id": "vdevo178131546308609",
        "ip": "",
        "key": "m~IClr['!./`>P=B",
        "version": 3.1
    }
}
```

## 🤖 Integración con Hermes Agent (Viernes)

Desde Telegram puedo ejecutar directamente en el servidor:

- *"Viernes, apaga la TV del cuarto"* → `tuya cuarto off`
- *"Viernes, enciende la TV de la sala"* → `tuya sala on`
- *"Viernes, apaga la tele del cuarto y a los 10 segundos la volvé a encender"* → `tuya cuarto off` + sleep 10 + `tuya cuarto on`
- *"¿Cómo están los enchufes?"* → `plugs`

## 🔄 Plug Reset (absorbed from `tuya-plug-reset`, now archived)

To reset a Tuya plug (power-cycle it):
```bash
tuya <plug_name> off && sleep <seconds> && tuya <plug_name> on
```

Examples:
```bash
# Reset TV del cuarto (5 seconds)
tuya cuarto off && sleep 5 && tuya cuarto on

# Reset TV de la sala (3 seconds)
tuya sala off && sleep 3 && tuya sala on
```

You can add an alias to `~/.bashrc`:
```bash
alias reset-plug='tuya $1 off && sleep ${2:-5} && tuya $1 on'
```
Usage: `reset-plug cuarto` or `reset-plug sala 3`

Verification: `tuya <name> status`

**Pitfall: `Permission denied` en el wrapper tuya**
Si falla con `Permission denied` al invocar `tuya`:
- **Causa:** El ejecutable perdió permisos `+x`.
- **Fix:** Ejecutar `chmod +x /home/piro/.local/bin/tuya` o usar la ruta directa `/home/piro/.tuya-venv/bin/python /home/piro/.hermes/tuya_control.py <dispositivo> <accion>`.

**Pitfall: `Error: 'dps'`**
If `tuya status` or control commands return `Error: 'dps'` while the device is reachable via ping:
- **Cause:** The IoT module's application layer has hung (Firmware hang).
- **Resolution:** A physical power-cycle (unplug/replug) is required. Software resets will not work if the DPS interface is unresponsive.

**Pitfall: backticks en local keys rompen SSH commands**
Las keys de Tuya contienen backticks (\`) y otros caracteres especiales. Si pasás la key inline en un comando SSH, bash interpreta el backtick como command substitution.
**Fix:** Escribir el script con `write_file()` (no pasa por shell) → `scp` al server → ejecutar con `timeout`. Ver `references/discovery-guide.md` para detalles.

## 🧠 Automatizaciones Posibles

- Cronjob para apagar TVs automáticamente a una hora
- Secuencias con temporizador (apagar X, esperar Y, encender Z)
- Plug reset (power-cycle) pattern
- Monitoreo de consumo eléctrico (DPS 19 = potencia en W/10)

## ⚠️ Notas Importantes

- ✅ **TV cuarto** funciona en 192.168.1.2 con protocolo v3.3
- ⚠️ **TV sala** (ID: eb36eef3376660c896dcqo) no responde en 192.168.1.4 ni se detectó en escaneo de red — puede estar apagada, en otra subred, o la IP/local_key cambiaron desde el wizard
- ⚠️ **Tramontina** tiene IPv6 pública pero no IP local disponible (no responde a escaneo UDP)
- El servidor (192.168.1.8, por cable Ethernet) **sí** ve los enchufes
- La laptop por WiFi puede no detectarlos si hay AP isolation
- Los enchufes solo funcionan en banda 2.4GHz
- `set_socketPersistent(False)` evita conexiones colgadas
- `set_socketTimeout(5)` acelera la detección de fallos
- Para re-scanear: `tinytuya wizard` en el servidor o `deviceScan()` — ver `references/discovery-guide.md`
- ⚠️ **SSH quoting trap:** las keys de Tuya contienen backticks y chars especiales que rompen heredocs de bash. Nunca pasar una key inline en un comando SSH — escribir el script localmente y copiarlo con scp

## 🔧 Configuración Inicial (ya realizada)

- Cuenta iot.tuya.com: API Key `my8fcvcjnatcvpcpamct`, región `us`
- Wizard ejecutado: `tinytuya wizard` → devices.json con 3 dispositivos
- Script de control creado en `~/.hermes/tuya_control.py`
- Symlinks: `~/.local/bin/tuya` y `~/.local/bin/plugs`
