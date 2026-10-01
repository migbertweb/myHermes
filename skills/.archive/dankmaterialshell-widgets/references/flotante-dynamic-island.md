# Flotante Dynamic Island — Reference Implementation

## Origin

Inspired by [NothingLess](https://github.com/leriart/NothingLess) (KDE Plasma notch/island theme). Ported to DankMaterialShell as a `PluginComponent`-based bar widget with popout expansion.

## Architecture

```
plugin.json                    → Manifiesto
FlotanteWidget.qml             → PluginComponent principal
FlotanteSettings.qml           → PluginSettings panel
```

## Key Implementation Details

### 1. Pill (Compact View)

The `horizontalBarPill` is a **capsule-shaped Rectangle** (radius: height/2) with:
- Semi-transparent accent color background (`opacity: 0.15`)
- Thin border (`border.width: 1`, `opacity: 0.3`)
- Row: indicator dot + clock text + notification badge
- `MouseArea` covering the whole pill for click-toggle and optional hover-expand

```qml
Rectangle {
    radius: height / 2          // ← pill shape
    color: root.accentColor
    opacity: 0.15

    Behavior on color {
        ColorAnimation { duration: root.animationDuration; easing.type: root.getEasing() }
    }
}
```

### 2. Popout (Expanded View)

Uses `PopoutComponent` from `qs.Modules.Plugins`:

```qml
popoutContent: Component {
    PopoutComponent {
        headerText: "Flotante"
        detailsText: root.currentDate || ""
        showCloseButton: true

        // Direct children = content. NO contentItem wrapper.
        ColumnLayout { ... }
    }
}
```

### 3. Animations

The popout uses a **two-axis scale animation** with a fade:

| Property | Collapsed | Expanded | Easing | Duration |
|---|---|---|---|---|
| `opacity` | 0.0 | 1.0 | OutCubic | 210ms (350*0.6) |
| `Scale.xScale` | 0.85 | 1.0 | OutBack (overshoot 1.2) | 350ms |
| `Scale.yScale` | 0.85 | 1.0 | OutBack (overshoot 1.2) | 350ms |

The easing is selectable via settings. Mapping:

| Setting value | QML Easing |
|---|---|
| `"OutBack"` | `Easing.OutBack` (spring-like) |
| `"OutCubic"` | `Easing.OutCubic` (smooth) |
| `"OutElastic"` | `Easing.OutElastic` (bouncy) |
| `"OutBounce"` | `Easing.OutBounce` (bounce) |

### 4. Section Visibility (Animated)

Each content section uses the pattern:

```qml
Rectangle {
    visible: root.showSectionName
    implicitHeight: condition ? expandedHeight : 0

    Behavior on implicitHeight {
        NumberAnimation { duration: 250; easing.type: Easing.OutCubic }
    }
}
```

This creates smooth reveal/hide transitions when toggling sections in settings.

### 5. Data Flow

```
PluginSettings (save) → plugin_settings.json → pluginData (auto-sync)
                                        ↓
                              PluginComponent reads:
                              property bool showX: pluginData.showX !== false
```

The `pluginData` object is **reactive** — changing a setting automatically updates the corresponding property in the widget via the `pluginDataChanged` signal. No manual loading/saving needed.

### 6. Timer-Based Updates

```qml
Timer {
    interval: 1000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: {
        var d = new Date()
        currentTime = d.toLocaleTimeString(Qt.locale(), "HH:mm")
        currentDate = d.toLocaleDateString(Qt.locale(), "ddd d MMM")
    }
}
```

`triggeredOnStart: true` ensures the first update happens immediately, not after one interval.

### 7. Layer Namespace

```qml
PluginComponent {
    layerNamespacePlugin: "flotante"
    // Becomes "dms:plugins:flotante" in Wayland layers
}
```

Needed for compositor blur/shader effects on the popout.

## Settings Panel

All setting types used:

| Component | Setting |
|---|---|
| `ToggleSetting` | showClock, showWeather, showMetrics, showMedia, showNotifications |
| `SelectionSetting` | animationEasing (4 options) |
| `SliderSetting` | animationDuration (150–800ms) |
| `ColorSetting` | accentColor |
| `ToggleSetting` | autoExpandOnHover |

## Hot-Reload Workflow

```bash
# After editing QML:
dms ipc call plugins reload flotante

# Check status:
dms ipc call plugins status flotante

# Full restart if needed:
dms restart
```

## Limitations

- **Bar-anchored**: The popout opens near the bar widget, NOT as a free-floating window. NothingLess on KDE Plasma creates an independent `wlr-layer-shell` surface that can be positioned anywhere. DMS plugins cannot do this — `PluginComponent` is always attached to a bar section.
- **No true MPRIS yet**: The media player section currently shows placeholder text. Full MPRIS integration requires `Quickshell.Services.Mpris` or similar.
- **Performance**: `Behavior on implicitHeight` for sections can cause layout jitter if the popout is rapidly resizing. Recommended to keep `animationDuration >= 200ms`.
