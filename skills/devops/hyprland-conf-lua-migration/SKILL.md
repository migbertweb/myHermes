---
name: hyprland-conf-lua-migration
description: Use when migrating Hyprland config from hyprlang to Lua.
category: devops
---

# Hyprland: Migración hyprlang `.conf` → Lua

## Contexto
Desde Hyprland 0.55, el formato hyprlang (`.conf`) está deprecado. El nuevo formato es Lua con `~/.config/hypr/hyprland.lua` como entry point. La configuración del usuario está en `/home/migbert/.config/hypr/` (laptop CachyOS).

## Archivos migrados
Ruta: `~/.config/hypr/lua/`

| Archivo | Origen | Contenido |
|---|---|---|
| `hyprland.lua` | `hyprland.conf` | Entry point: env, input, animaciones, misc, layer rules, requires |
| `colors.lua` | `dms/colors.conf` | Esquema cromático de bordes y grupos |
| `outputs.lua` | `dms/outputs.conf` | Configuración de monitores (HDMI-A-2, eDP-1, DP-1) |
| `layout.lua` | `dms/layout.conf` | Gaps (1px), border (1px), rounding (15px) |
| `cursor.lua` | `dms/cursor.conf` | Tema Qogirr-Dark, tamaño 24, hide timeout 2s |
| `startup.lua` | `dms/startup.conf` | Autostart vía `hl.on("hyprland.start", ...)` |
| `binds.lua` | `dms/binds.conf` | Todos los keybinds (DMS, media, workspace, resize, apps) |
| `windowrules.lua` | `dms/windowrules.conf` | Reglas de ventana + asignaciones de workspace 1-9 |

## Mapeo de sintaxis

| hyprlang | Lua |
|---|---|
| `env = K,V` | `hl.env("K", "V")` |
| `input { ... }` | `hl.config({ input = { ... } })` |
| `bezier = N,x0,y0,x1,y1` | `hl.curve("N", { type="bezier", points={{x0,y0},{x1,y1}} })` |
| `animation = leaf,1,speed,curve,style` | `hl.animation({ leaf="leaf", enabled=true, speed=N, bezier="curve", style="style" })` |
| `monitor = OUT,MODE,POS,SCALE` | `hl.monitor({ output="OUT", mode="MODE", position="POS", scale=N })` |
| `exec-once = CMD` | `hl.on("hyprland.start", function() hl.exec_cmd("CMD") end)` |
| `source = ./path/file.conf` | `require("file")` (ruta relativa al .lua) |
| `bind = MOD,KEY,DISP,PARAM` | `hl.bind("MOD + KEY", hl.dsp.XXX(PARAM))` |
| `bindl` | `hl.bind(..., { locked = true })` |
| `bindel` | `hl.bind(..., { locked = true, repeating = true })` |
| `binde` | `hl.bind(..., { repeating = true })` |
| `bindd` | `hl.bind(..., { locked = true })` |
| `bindr` | `hl.bind(..., { release = true })` |
| `bindmd` | `hl.bind(..., { mouse = true })` |
| `windowrule = ...` | `hl.window_rule({ ... })` |
| `layerrule = ...` | `hl.layer_rule({ ... })` |

## Dispatchers comunes

| hyprlang | Lua DSL |
|---|---|
| `exec, cmd` | `hl.dsp.exec_cmd("cmd")` |
| `workspace, N` | `hl.dsp.focus({ workspace = N })` |
| `movetoworkspace, N` | `hl.dsp.window.move({ workspace = N })` |
| `movefocus, DIR` | `hl.dsp.focus({ direction = "DIR" })` |
| `movewindow, DIR` | `hl.dsp.window.move({ direction = "DIR" })` |
| `togglefloating` | `hl.dsp.window.float({ action = "toggle" })` |
| `togglegroup` | `hl.dsp.group.toggle()` |
| `killactive` | `hl.dsp.window.close()` |
| `exit` | `hl.dsp.exit()` |
| `layoutmsg, togglesplit` | `hl.dsp.layout("togglesplit")` |

## Cómo probar
```bash
# Sin arriesgar la sesión actual:
Hyprland --config ~/.config/hypr/lua/hyprland.lua

# O cargar en sesión actual (si confías):
hyprctl reload  # solo si hyprland.lua está en ~/.config/hypr/
```

## Notas importantes
- Los valores fuente de verdad son los `.conf` activos (NO los `.lua` generados por DMS que tienen valores distintos)
- `hl.exec_cmd()` es asíncrono, no necesita `&` al final
- `require()` usa rutas relativas al archivo que lo invoca
- Las reglas de ventana se evalúan en orden (top → bottom)
- `luac -p archivo.lua` verifica sintaxis pero no errores de runtime
- Para regex en Lua, usar `\\.` para escapar puntos (ej: `org\\.gnome\\.`)
