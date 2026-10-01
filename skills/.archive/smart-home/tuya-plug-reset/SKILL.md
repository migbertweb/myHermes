---
name: tuya-plug-reset
title: Tuya Plug Reset - Apagar y Encender
description: Secuencia para resetear un enchufe Tuya (apagar, esperar N segundos, encender)
category: smart-home
---

## Comando

```bash
tuya <nombre_del_enchufe> off && sleep <segundos> && tuya <nombre_del_enchufe> on
```

## Ejemplos

### Reset TV del cuarto (5 segundos)
```bash
tuya cuarto off && sleep 5 && tuya cuarto on
```

### Reset TV de la sala (3 segundos)
```bash
tuya sala off && sleep 3 && tuya sala on
```

## Plugins disponibles
- **cuarto** - 192.168.1.4 (v3.3) - TV cuarto
- **sala** - 192.168.1.2 (v3.5) - TV sala
- **tramontina** - Desconectado

## Alias recomendado (añadir a ~/.bashrc)
```bash
alias reset-plug='tuya $1 off && sleep ${2:-5} && tuya $1 on'
```
Uso: `reset-plug cuarto` o `reset-plug sala 3`

## Verificación
```bash
tuya <nombre> status
```
