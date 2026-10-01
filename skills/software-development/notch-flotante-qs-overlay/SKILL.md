---
name: notch-flotante-qs-overlay
title: "NotchFlotante — Dynamic Island overlay con Quickshell independiente"
description: "Crear un notch/Dynamic Island que corre como instancia Quickshell independiente (PanelWindow WlrLayer.Overlay) junto a DMS, en lugar de usar PluginComponent de DMS."
---

# NotchFlotante — Notch overlay independiente con Quickshell

## Por qué NO usar PluginComponent de DMS
- `PluginComponent` es un widget de barra con `popoutContent` limitado
- El popout abre como ventana separada, no como expansión suave
- NothingLess usa `PanelWindow` con `WlrLayer.Overlay` — arquitectura diferente
- DMS y la instancia notch coexisten sin conflictos (probado)

## Arquitectura
```
~/.config/quickshell/notch-flotante/
  shell.qml            # Entry point con ShellRoot
  NotchOverlay.qml     # PanelWindow overlay + notch pill + animaciones
```

## Componentes clave

### shell.qml
```qml
//@ pragma UseQApplication
import QtQuick
import Quickshell

ShellRoot {
    Loader { source: "NotchOverlay.qml" }
}
```

### NotchOverlay.qml
```qml
PanelWindow {
    anchors { top: true; left: true; right: true }
    implicitHeight: 280
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    exclusionMode: ExclusionMode.Ignore
    mask: Region { item: notchHitbox }
    // ... notch pill con Behavior + Easing.OutBack + overshoot 1.7
    // Contenido: reloj, CPU, RAM, MPRIS vía playerctl
}
```

## Animaciones (perfil ambxst)
| Propiedad | Valor |
|---|---|
| Expand duration | 550ms |
| Collapse duration | 400ms |
| Easing | Easing.OutBack |
| Overshoot | 1.7 |

## Systemd service
```ini
[Unit]
Description=NotchFlotante — Dynamic Island overlay
PartOf=graphical-session.target
After=graphical-session.target

[Service]
Type=exec
ExecStart=/usr/bin/quickshell --config notch-flotante
Restart=on-failure
RestartSec=2

[Install]
WantedBy=graphical-session.target
```

## Comandos útiles
- Iniciar: `quickshell --config notch-flotante --daemonize`
- Listar instancias: `quickshell list --all`
- Ver logs: `cat /run/user/1000/quickshell/by-id/<ID>/log.qslog`
- Matar: `pkill -f "quickshell.*notch-flotante"` (NO mata DMS)

## Import disponibles (standalone Quickshell)
- `Quickshell` — core (ShellRoot)
- `Quickshell.Io` — Process, StdioCollector, FileView
- `Quickshell.Wayland` — PanelWindow, WlrLayershell, WlrLayer
- `QtQuick` — componentes estándar
- `QtQuick.Layouts` — layouts

## Lectura de sistema
- Reloj: `Date().toLocaleTimeString()` en QML
- CPU: `grep '^cpu ' /proc/stat | awk ...` via Process + StdioCollector
- RAM: `free | awk ...` via Process + StdioCollector
- Media: `playerctl -a metadata --format '{{title}}␞{{artist}}'` via Process + StdioCollector
