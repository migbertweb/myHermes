---
name: dankmaterialshell-widgets
description: Develop and maintain QML plugins for DankMaterialShell (Quickshell-based bar). Covers both widget-type bar plugins (PluginComponent) and daemon-type slideout plugins (DankSlideout). Theme API signatures, plugin file structure, reference implementations, and sizing conventions.
category: software-development
triggers:
  - "dankmaterialshell"
  - "quickshell"
  - "dankbar"
  - "plugincomponent"
  - "bariconsize"
  - "bartextsize"
  - "AllMonitorsW"
  - "resourcemonitor"
  - ".qml plugin widget"
---

# DankMaterialShell Widget Development

## Reference Implementations

System widgets live at:
```
/usr/share/quickshell/dms/Modules/DankBar/Widgets/
```

Key examples to reference: **Battery.qml**, **CpuMonitor.qml**, **RamMonitor.qml**, **NetworkMonitor.qml**, **Clock.qml**. These follow the canonical patterns.

## Plugin File Structure

A DankMaterialShell plugin typically has:
```
plugins/<PluginName>/
├── plugin.json              # Plugin metadata + entry point
├── <PluginWidget>.qml       # ACTIVE plugin — extends PluginComponent
├── <PluginSettings>.qml     # Settings panel — extends PluginSettings
├── assets/
│   └── screenshot.png
├── ayuda/                   # REFERENCE copies ONLY
│   └── AllMonitorsWidget.qml
├── README.md
└── .git/
```

**⚠️ Pitfall**: The `ayuda/` directory contains reference/documentation copies, NOT the active widget. Always edit the root-level `.qml` file (e.g., `ResourceMonitor.qml`) that has `pluginId: "..."` set. Editing `ayuda/*.qml` instead is a no-op.

The active plugin component file extends `PluginComponent` and declares `pluginId` (used in `plugin.json` and `PluginSettings`). The `ayuda/` copy is an independent alternate implementation for reference — the system loads the root file, not the `ayuda/` one.

**⚠️ Parameter pitfall**: `Theme.barIconSize` takes **4 parameters**, not 3. Do NOT pass `root.barConfig?.noBackground` as the 3rd argument — that position expects `maximizeWidgetIcons`. If you pass `noBackground` there, the maximize-widget-icons setting is ignored. Similarly, `Theme.barTextSize` takes **3 parameters** — do not omit the 3rd (`maximizeWidgetText`).

**⚠️ Color pitfall**: `Colors.overBackground` does **NOT** exist in DMS. If you're porting code from another Quickshell-based shell (like Ambxst/NothingLess), replace it with `Theme.surfaceText`. Do NOT use `Colors.*` for surface text — use `Theme.surfaceText` instead.

## Theme API — Dynamic Sizing

Always use these **dynamic** functions instead of static `Theme.fontSizeSmall` / `Theme.iconSizeSmall`. The static values ignore the user's bar config (thickness, font scale, icon scale, maximize settings).

### `Theme.barIconSize(thickness, offset, maximizeWidgetIcons, iconScale)`

| Param | Type | Example |
|---|---|---|
| `thickness` | real | `root.barThickness` |
| `offset` | variant | `undefined` (no offset) or a number like `-4` to shrink |
| `maximizeWidgetIcons` | bool? | `root.barConfig?.maximizeWidgetIcons` |
| `iconScale` | real? | `root.barConfig?.iconScale` |

Full signature:
```qml
size: Theme.barIconSize(root.barThickness, undefined, root.barConfig?.maximizeWidgetIcons, root.barConfig?.iconScale)
```

### `Theme.barTextSize(thickness, fontScale, maximizeWidgetText)`

| Param | Type | Example |
|---|---|---|
| `thickness` | real | `root.barThickness` |
| `fontScale` | real? | `root.barConfig?.fontScale` |
| `maximizeWidgetText` | bool? | `root.barConfig?.maximizeWidgetText` |

Full signature:
```qml
font.pixelSize: Theme.barTextSize(root.barThickness, root.barConfig?.fontScale, root.barConfig?.maximizeWidgetText)
```

### `Theme.spacingXS`, `Theme.cornerRadius`, etc.

These `Theme.*` constants are safe to use directly — they are static design tokens, not config-dependent.

## Orientation Patterns

Both `horizontalBarPill` and `verticalBarPill` should use the **same** dynamic `Theme.barIconSize()` / `Theme.barTextSize()` calls. The system widgets (Battery.qml, CpuMonitor.qml, etc.) use `barIconSize` and `barTextSize` in both orientations, not static sizes.

## PluginComponent Properties Available

When extending `PluginComponent` (the base for bar widgets), these are available automatically:

- `root.barThickness` — current bar thickness (pixels)
- `root.barConfig?.fontScale` — user's font scale multiplier
- `root.barConfig?.iconScale` — user's icon scale multiplier
- `root.barConfig?.maximizeWidgetIcons` — whether icons should be enlarged
- `root.barConfig?.maximizeWidgetText` — whether text should be enlarged
- `root.barConfig?.noBackground` — whether widget backgrounds are hidden
- `root.isVerticalOrientation` — true when bar is on left/right edge
- `root.parentScreen` — the screen this widget instance is on
- `root.pluginData` — settings data (saved via PluginSettings)
- `root.section` — which bar section this widget is in
- `root.widgetThickness` — available thickness for the widget
- `root.horizontalPadding` — horizontal padding inside the widget

## Custom Components (ResourceRingIcon pattern)

When building custom visual components (like circular progress rings around icons), follow these conventions:

```qml
component ResourceRingIcon: Item {
    id: ringRoot
    // ... properties ...

    // Ring outer dimensions: barIconSize + padding
    // ⚠️ Tuning: +12 gives 6px margin per side (clean but can extend past thin bars).
    //            +8  gives 4px margin per side (tighter, safer for thin bars).
    //            Pick based on your bar thickness and personal taste.
    width: ringRoot.iconSize + 8
    height: ringRoot.iconSize + 8

    // iconSize should match system widgets — use barIconSize directly
    readonly property int iconSize: Theme.barIconSize(
        root.barThickness, undefined,
        root.barConfig?.maximizeWidgetIcons, root.barConfig?.iconScale
    )

    Canvas {
        anchors.fill: parent
        // ... draw arc with lineWidth: 3 ...
    }

    DankIcon {
        anchors.centerIn: parent
        size: ringRoot.iconSize      // ← same as system DankIcon usage
    }
}
```

**⚠️ Icon sizing pitfall**: Do NOT use a multiplier like `barIconSize * 0.54` for the inner icon. The icon inside a ring should be `barIconSize` directly — the same size as standalone `DankIcon` elements in native widgets. A multiplier produces tiny, unusable icons. Add padding to the ring (e.g., `+ 12`) instead of shrinking the icon.

## Popout (Expandable) Widgets

For widgets that expand on click (Dynamic Island / Notch style), use `horizontalBarPill` + `popoutContent`.

### Structure

```qml
PluginComponent {
    id: root

    // Properties from settings
    property bool showClock: pluginData.showClock !== false

    // Compact pill in the bar
    horizontalBarPill: Component {
        Item {
            implicitWidth: row.implicitWidth + 24
            implicitHeight: 36

            // Background pill capsule
            Rectangle {
                anchors.fill: parent
                radius: height / 2
                color: root.accentColor
                opacity: 0.15
            }

            // Content — icon + time + indicators
            Row { id: row; anchors.centerIn: parent; spacing: 6
                // ... texts, icons ...
            }

            // MouseArea for click/hover
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.isExpanded = !root.isExpanded
            }
        }
    }

    // Expanded content (opens as popout near the bar widget)
    popoutContent: Component {
        PopoutComponent {
            headerText: "Widget Title"
            detailsText: root.currentDate || ""
            showCloseButton: true

            // ⚠️ CONTENT GOES AS DIRECT CHILDREN — NOT contentItem
            // PopoutComponent has a default property that wraps children
            // in its layout. Do NOT use `contentItem: Item { ... }`.
            ColumnLayout {
                width: parent.width
                spacing: 8

                StyledText {
                    text: "Expanded content here"
                    font.pixelSize: 18
                    color: Theme.surfaceText
                }
            }
        }
    }
}
```

**⚠️ Critical popout pitfall**: `PopoutComponent` uses direct QML children for its content — do NOT wrap content in a `contentItem` property. Children are placed inside the popout layout automatically. Using `contentItem` will cause the content to not render.

### Recommended Settings Panel pattern

```qml
PluginSettings {
    id: root
    pluginId: "myPlugin"

    // Section header
    StyledText {
        width: parent.width
        text: "My Plugin Settings"
        font.pixelSize: Theme.fontSizeLarge
        font.weight: Font.Bold
        color: Theme.surfaceText
    }

    // Toggle
    ToggleSetting {
        settingKey: "showClock"
        label: "Show Clock"
        defaultValue: true
    }

    // Dropdown
    SelectionSetting {
        settingKey: "animationEasing"
        label: "Animation Style"
        options: [
            { label: "Spring", value: "OutBack" },
            { label: "Smooth", value: "OutCubic" }
        ]
        defaultValue: "OutBack"
    }

    // Slider
    SliderSetting {
        settingKey: "animationDuration"
        label: "Duration"
        defaultValue: 350
        minimum: 150
        maximum: 800
        unit: "ms"
    }

    // Color picker
    ColorSetting {
        settingKey: "accentColor"
        label: "Accent Color"
        defaultValue: "#7C3AED"
    }

    // Text input
    StringSetting {
        settingKey: "apiKey"
        label: "API Key"
        placeholder: "Enter key"
        defaultValue: ""
    }
}
```

## Animation Techniques (Dynamic Island / Expansion Effects)

To replicate spring-like Dynamic Island animations (NothingLess-style), use the Item's native `scale` property with `Behavior on scale`:

```qml
popoutContent: Component {
    PopoutComponent {
        id: popout

        opacity: root.isExpanded ? 1.0 : 0.0
        scale: root.isExpanded ? 1.0 : 0.85   // 85% → 100%
        transformOrigin: Item.Top             // expands downward like an island

        // Fade in
        Behavior on opacity {
            NumberAnimation {
                duration: 250
                easing.type: Easing.OutCubic
            }
        }

        // Spring-like scale (closest to NothingLess Anim.springSnappy())
        Behavior on scale {
            NumberAnimation {
                duration: 350
                easing.type: Easing.OutBack
                easing.overshoot: 1.2
            }
        }
    }
}
```

**⚠️ CRITICAL PITFALL — Do NOT use `Behavior on` with `Scale` objects in `transform:`**

This pattern **does NOT work** and causes a runtime crash:
```qml
// ❌ BROKEN — "Cannot assign to non-existent property 'popoutScale.xScale'"
transform: Scale { id: popoutScale; xScale: 0.85; yScale: 0.85 }
Behavior on popoutScale.xScale { ... }   // ← RUNTIME ERROR
```

QML cannot apply `Behavior` to properties of objects referenced by id inside the `transform: []` array. Always use the Item's native `scale` property instead, which is directly animated by `Behavior on scale`.

**Key animation properties table:**

| Effect | Technique | Easing |
|--------|-----------|--------|
| Scale expansion (spring) | `Behavior on scale` + `NumberAnimation` | `Easing.OutBack` (overshoot 1.2) |
| Fade in/out | `Behavior on opacity` + `NumberAnimation` | `Easing.OutCubic` |
| Height reveal | `Behavior on implicitHeight` + `NumberAnimation` | `Easing.OutCubic` |
| Color transition | `Behavior on color` + `ColorAnimation` | flat duration (no easing) |
| Section show/hide | `visible: condition` + `Behavior on implicitHeight` | `Easing.OutCubic` |

**Spring equivalences** (NothingLess → DMS plugin):

| NothingLess Anim.* | Plugin equivalent |
|---|---|
| `Anim.springSnappy()` | `NumberAnimation { easing.type: Easing.OutBack; easing.overshoot: 1.2 }` |
| `Anim.emphasizedNormal` | `duration: 350` (with OutBack easing) |
| `Anim.spring()` | `NumberAnimation { easing.type: Easing.OutBack; easing.overshoot: 1.5 }` |

## Layer Namespaces

Add a custom Wayland layer namespace so the popout can have proper compositor effects (e.g., blur):

```qml
PluginComponent {
    layerNamespacePlugin: "my-plugin-name"
    // The shell prefixes it automatically → "dms:plugins:my-plugin-name"
}
```

Without this, the popout defaults to `dms:plugins:plugin`. Layer namespaces only work with popout-enabled (non-daemon) widgets.

## Daemon-type Plugin Architecture

DMS supports two plugin types. The skill covers **widget** plugins (bar items with `horizontalBarPill`/`popoutContent`). This section covers **daemon** plugins — singleton services that provide slideout panels, not bar widgets.

### Key differences: Widget vs Daemon

| Aspect | Widget Plugin | Daemon Plugin |
|--------|--------------|---------------|
| `plugin.json` `type` | `"widget"` (or omitted) | `"daemon"` |
| Entry component | Extends `PluginComponent` (bar item) | Custom `Item` (injected by PluginService) |
| UI surface | `horizontalBarPill` / `popoutContent` in bar | `DankSlideout` — panel that slides from edge |
| File structure | Single `.qml` for bar + optional popout | Two files: **Daemon** (lifecycle + Variants) + **Service** (business logic) |
| Screen instances | One per screen (auto) | One per screen via `Variants { model: Quickshell.screens }` |
| HTTP communication | Not needed (local data) | Uses `Process` + `curl` (Quickshell has no `XMLHttpRequest`) |

### Canonical example: AI Assistant plugin

The plugin at `~/.config/DankMaterialShell/plugins/dms-ai-assistant-II/` demonstrates the pattern:

```
AIAssistant/
├── plugin.json              # { "id": "aiAssistant", "type": "daemon", ... }
├── AIAssistantDaemon.qml    # Entry: PluginService + Variants + slideout
├── AIAssistantService.qml   # Singleton: API calls, streaming, state
├── AIAssistant.qml          # UI: chat interface
├── AIAssistantSettings.qml  # Settings panel
├── AIApiAdapters.js         # Provider adapters (JS library)
├── Markdown2Html/           # Custom markdown renderer
├── MessageBubble.qml        # Message component
└── MessageList.qml          # Message list container
```

### Daemon entry point pattern

```qml
// AIAssistantDaemon.qml
import QtQuick
import Quickshell
import qs.Common
import qs.Widgets
import qs.Services

Item {
    id: root
    property var pluginService: null
    property string pluginId: "aiAssistant"

    function toggle() {
        if (variants.instances.length > 0)
            variants.instances[0].toggle();
    }

    // Singleton service (business logic)
    AIAssistantService {
        id: aiLogic
        pluginId: root.pluginId
    }

    // One slideout per screen
    Variants {
        id: variants
        model: Quickshell.screens
        delegate: DankSlideout {
            id: slideout
            required property var modelData
            title: "Plugin Title"
            slideoutWidth: 480
            expandable: true
            expandedWidthValue: 960
            content: AIAssistant {
                aiService: aiLogic
                onHideRequested: slideout.hide()
            }
        }
    }
}
```

**Key patterns:**
- **PluginService** is injected as a property (`pluginService: null`) — NOT at `Component.onCompleted` for the service. The daemon component itself gets it via injection.
- **`Variants` with `Quickshell.screens`** — one slideout per monitor. Each instance gets `modelData` for its screen.
- **`DankSlideout`** — the built-in DMS slideout panel. Set `expandable: true` for a wider mode toggle.
- The service is a **singleton** (created once in the daemon). All slideout instances share it.

### IPC communication

Daemon plugins listen for IPC commands via `dms ipc call`:

```bash
# Toggle the slideout
dms ipc call plugins toggle aiAssistant

# Reload plugin (QML cache)
dms ipc call plugins reload aiAssistant

# Check plugin status
dms ipc call plugins status aiAssistant
```

The daemon's `toggle()` function is the IPC entry point.

### HTTP API calls in QML (Process + curl)

Since Quickshell does not expose `XMLHttpRequest` or Qt's `NetworkAccessManager`, plugins use `Process` + `curl` for HTTP. The `AIAssistantService.qml` pattern:

```qml
Process {
    id: chatFetcher
    running: false

    stdout: StdioCollector {
        id: streamCollector
        property int lastLen: 0

        onTextChanged: {
            const newData = text.substring(lastLen);
            lastLen = text.length;
            handleStreamChunk(newData);  // parse SSE + update UI
        }

        onStreamFinished: {
            handleStreamFinished(text);
        }
    }

    onExited: exitCode => {
        if (exitCode !== 0 && isStreaming)
            markError(activeStreamId, "Request failed (exit " + exitCode + ")");
    }
}
```

**Critical curl flags:**
- `-N` — no-buffering (required for streaming)
- `--no-buffer` — extra buffer disable
- `-sS` — silent but show errors
- `-w "\\nDMS_STATUS:%{http_code}\\n"` — footer append for HTTP status capture

**⚠️ `--compressed` flag breaks streaming:** The `--compressed` flag causes QML's `StdioCollector` to fail capturing stdout incrementally — the entire response appears only when curl exits. Do NOT add it. Only `-N` and `--no-buffer` are needed for streaming.

**⚠️ `StyledText` does NOT support `elide`:** The `elide` property (`Text.ElideMiddle`, `Text.ElideRight`) is available in Qt Quick's standard `Text` but **not** in DMS's `StyledText` wrapper. Using it silently breaks rendering or causes a runtime warning. For long text that needs clipping, use `clip: true` + `elide` is not supported on this StyledText instance instead — or wrap a standard `Text` item with the font/size properties manually.

**⚠️ `.pragma library` JS files crash DMS when modified:** JS library files with `.pragma library` at the top are compiled by the QML engine at import time and aggressively cached (`.jsc` / `.qmlc`). Modifying them while DMS is running, or even during a `dms restart`, can **crash the entire DMS process** because the cached compiled version becomes stale. The QML engine does NOT auto-invalidate the cache for library files.

To safely modify a `.pragma library` file:
1. Make the edit
2. Clear the QML cache: `rm -rf ~/.cache/noctalia-qs/qmlcache/`
3. Restart DMS fresh (not just restart, a full process kill + start)

Alternatively, **avoid modifying `.pragma library` files entirely** by injecting behavior in the caller (e.g., `AIAssistantService.qml`). For example, to add an HTTP header:

```javascript
// In service's buildCurlCommand(), NOT in the adapter library:
const req = AIApiAdapters.buildRequest(provider, payload, key);
if (hermesSessionId && req && req.headers) {
    req.headers = req.headers.concat(["-H", "X-My-Header: " + value]);
}
```
This uses `.concat()` (creates new array, no mutation of const arrays from the library) and keeps the change in the safe `.qml` file.

**⚠️ Avoid `const` + `.push()` in QML JS:** QML's V4 JIT engine may reject `.push()` on arrays declared with `const`. This produces a silent runtime error that can crash the plugin. Always use `var` + `.concat()` to build dynamic arrays:

```javascript
// ❌ MAY CRASH:
const headers = ["-H", "Content-Type: application/json"];
if (condition) headers.push("-H", "Extra");  // const mutation — can fail

// ✅ SAFE:
var parts = [];
if (condition) parts = ["-H", "Extra"];
const headers = ["-H", "Content-Type: application/json"].concat(parts);
```

### Reading local config files (Process + sh)

The same `Process` + `StdioCollector` pattern works for reading local files, not just HTTP endpoints. Useful for fetching external configuration (e.g., Hermes Agent's `~/.hermes/config.yaml`) to display real provider/model in the UI instead of hardcoded plugin settings.

```qml
Process {
    id: configReader
    command: [
        "sh", "-c",
        "head -4 ~/.hermes/config.yaml | tail -2 | sed 's/.*: //'"
    ]
    running: false

    stdout: StdioCollector {
        id: configCollector
        onTextChanged: {
            const text = (this.text || "").trim();
            const lines = text.split('\n').filter(l => l.trim());
            if (lines.length >= 2) {
                root.someProperty = lines[0].trim();  // first output line
                root.otherProperty = lines[1].trim(); // second output line
            }
        }
    }

    onExited: (code) => {
        if (code !== 0) {
            // Set sensible fallbacks
        }
    }
}
```

**Trigger the process** only when needed (e.g., on mode detection):
```qml
if (conditionChanged) {
    configReader.running = true;
}
```

Full pattern with Hermes-specific context: see `references/hermes-api-server-integration.md` sections 6 (config reader + two levels of model changes) and section 6's data.model capture sub-section for dynamic session-level updates.

### Streaming response parsing

The plugin reads SSE-formatted lines from curl's stdout:

```javascript
function handleStreamChunk(chunk) {
    let buffer = streamBuffer + chunk;
    const parts = buffer.split(/\r?\n/);

    // Keep incomplete line in buffer
    if (buffer.length > 0 && !buffer.endsWith("\n") && !buffer.endsWith("\r"))
        streamBuffer = parts.pop();
    else
        streamBuffer = "";

    for (let i = 0; i < parts.length; i++) {
        const line = parts[i].trim();
        if (!line) continue;
        if (line === "data: [DONE]") { finalizeStream(); continue; }
        if (line.startsWith("data:")) {
            const jsonPart = line.substring(5).trim();
            parseProviderDelta(jsonPart);
        }
    }
}
```

The HTTP status code is extracted from the `DMS_STATUS:XXX` footer line appended by curl's `-w` flag.

### Provider adapter pattern (JS library)

Provider-specific formatting lives in `.pragma library` JS files (shared by all instances):

```javascript
.pragma library

function buildRequest(provider, payload, apiKey) {
    switch (provider) {
    case "anthropic": return anthropicRequest(payload, apiKey);
    case "gemini":    return geminiRequest(payload, apiKey);
    case "ollama":    return ollamaRequest(payload);
    case "custom":    return customRequest(payload, apiKey);
    default:          return openaiRequest(payload, apiKey);
    }
}
```

Each adapter returns `{ url, headers: ["-H", ...], body: JSON.stringify(...) }`.

### Chat history persistence

```qml
readonly property string baseDir: Paths.strip(
    StandardPaths.writableLocation(StandardPaths.GenericStateLocation)
    + "/DankMaterialShell/plugins/aiAssistant")
readonly property string sessionPath: baseDir + "/session.json"
```

Uses `FileView` for atomic writes (atomicWrites: true). Session data format supports multiple provider configs keyed by a hash of `provider|baseUrl|model`.

### Dynamic settings loading

The daemon subscribes to `PluginService.onPluginDataChanged` to reload settings at runtime without a plugin restart:

```qml
Connections {
    target: PluginService
    function onPluginDataChanged(pId) {
        if (pId !== root.pluginId) return;
        loadSettings();
    }
}
```

### Aesthetic customizations (chat UI)

Common QML-only changes (no JS libraries touched) for the AI Assistant chat:

| Goal | Files | Changes |
|------|-------|---------|
| Remove redundant role labels/icons | `MessageBubble.qml` | Delete `headerPill` Rectangle (has `I18n.tr("You"|"Assistant")` + `DankIcon`) |
| Compact spacing | `MessageBubble.qml`, `MessageList.qml` | Reduce padding from `spacingM*2` → `spacingS*2`, column `spacingS` → `spacingXS`, list `spacingM` → `spacingXS` |
| Remove action-button gap | `MessageBubble.qml` | Delete separator `Item { width:1; height:Theme.spacingS }` |
| Clean input row | `AIAssistant.qml` | Replace send `>` with `arrow_upward` + `backgroundColor: Theme.primary`, replace stop `■` with `hourglass_empty`, add `attach_file` placeholder |
| Theme-integrated header badges | `AIAssistant.qml` | 🤖 badge uses `Qt.rgba(Theme.primary.r, ... , 0.15)` fill + primary border, provider badge uses `Theme.surfaceVariant` |
| Animated status dot | `AIAssistant.qml` | Color changes (green/warning/grey) with `ColorAnimation`; streaming pulse via child `Rectangle` with infinite `opacity` + `scale` animations |
| Left accent bar on bubbles | `MessageBubble.qml` | 3px `Rectangle` at left edge with `Qt.rgba(Theme.primary.r, ... , 0.5)` for assistant messages |
| Tool activity badge | `AIAssistant.qml` + `AIAssistantService.qml` | `🛠️ Tools` badge (warning-tinted) appears when gap-based or pattern-based detection fires |

**Design principle**: Bubble color + right/left alignment already signals sender role. Text labels ("You" / "Assistant") and role icons (👤/🤖) are redundant — removing them makes the UI cleaner without losing information.

**Theme integration patterns**:
- Use `Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, alpha)` for primary-tinted fills
- Use `Theme.warning` for streaming/tool-active states (`ColorAnimation` for transitions)
- Add accent borders/bars with `border.color: Qt.rgba(Theme.primary.r, ... , 0.4)` + `border.width: 1`
- Animate streaming indicators with `NumberAnimation on opacity/scale { loops: Animation.Infinite }`
- Button states: `backgroundColor: Theme.primary` + `iconColor: Theme.onPrimary` for primary actions

Full detail in `references/hermes-api-server-integration.md` sections "Aesthetic customizations", "Timeout Handling (Watchdog Timer)", "Tool Call Detection from Streaming" (including gap-based + pattern-based fallback sub-sections), and "Improved scroll-to-bottom".

## Settings Components Reference

| Component | QML Type | Configures | Default value |
|---|---|---|---|
| `ToggleSetting` | Boolean switch | on/off toggles | `defaultValue: true/false` |
| `SelectionSetting` | Dropdown menu | enum options via `options: [{label, value}]` | `defaultValue: "value"` |
| `SliderSetting` | Numeric slider | ranges with `minimum`, `maximum`, `unit` | `defaultValue: 50` |
| `ColorSetting` | Color picker modal | hex colors | `defaultValue: "#7C3AED"` |
| `StringSetting` | Text input | free text, `placeholder` | `defaultValue: ""` |

Access in your widget via `pluginData`:
```qml
property bool showClock: pluginData.showClock !== false   // default true
property int interval: pluginData.interval || 60          // default 60
property string color: pluginData.color || "#7C3AED"      // default hex
```

## Reference Implementation: Flotante Dynamic Island

The user's Flotante plugin (`~/.config/DankMaterialShell/plugins/flotante/`) is a complete working Dynamic Island implementation. Key patterns it demonstrates:
- **Pill**: `horizontalBarPill` with capsule background + hover/click interaction
- **Popout**: `PopoutComponent` with clock, CPU/RAM metrics, media player placeholder, notification counter
- **Animations**: Scale fade-in + spring-like expansion with `Easing.OutBack`
- **Settings**: Full settings panel with toggles, easing selector, duration slider, color picker
- **Data**: `pluginData` auto-sync, `Timer` for clock updates, `SystemResources` for metrics

```qml
// Minimal skeleton from Flotante:
PluginComponent {
    layerNamespacePlugin: "flotante"
    property bool isExpanded: false

    horizontalBarPill: Component {
        Item {
            // Pill with Rectangle bg + Row of icons/text + MouseArea
            implicitWidth: 36; implicitHeight: 36
            // ...
        }
    }

    popoutContent: Component {
        PopoutComponent {
            headerText: "Flotante"
            showCloseButton: true
            scale: root.isExpanded ? 1.0 : 0.85
            transformOrigin: Item.Top
            Behavior on scale { NumberAnimation { duration: 350; easing.type: Easing.OutBack; easing.overshoot: 1.2 } }
            Behavior on opacity { NumberAnimation { duration: 250 } }
            ColumnLayout {
                // Clock, Metrics, Media, Notifications sections
            }
        }
    }
}
```

> **📚 Reference**: See `references/nothingless-ambxst-analysis.md` for the full architecture comparison between NothingLess, Ambxst, and DMS plugin APIs — useful when porting features from other Quickshell-based shells.

## Safe Development Workflow (User Preference)

When iterating on DMS plugin QML/JS changes, follow this workflow:

1. **Show the plan first** — Present the approach (which files, what changes, risk level) before writing code. Ask for confirmation.
2. **Apply one functional change at a time** — Split work into atomic, testable steps. Each step should be verifiable on its own without needing later steps.
3. **Restart DMS between each step** — `dms restart` after each change. Verify the plugin loads and the feature works before the next step.
4. **Commit after each verified milestone** — Creates safe rollback points. Push only when the user says to.
5. **If the plugin stops activating, revert the last change first.** Then check for:
   - Duplicate DMS instances (see pitfall below)
   - QML cache staleness (`rm -rf ~/.cache/noctalia-qs/qmlcache/`)
   - JS syntax errors in `.pragma library` files
   - Unsupported QtQuick properties on DMS custom components (`elide` on `StyledText`, `ToolTip` from QtQuick.Controls)
6. **When changing storage format** (e.g., session.json), ship backward-compatible loading code before writing the new format. Reader first, then writer.

## Verification

After editing a widget .qml file:
1. Hot-reload just the plugin (faster than full restart):
   ```bash
   dms ipc call plugins reload <pluginId>
   ```
   ⚠️ Note: the command is `dms ipc call plugins reload <id>` — NOT `dms ipc plugins reload`. The `call` subcommand is required.
   Find `pluginId` in the QML file (e.g., `pluginId: "flotante"`) or from `plugin.json`'s `"id"` field.
2. Check plugin status:
   ```bash
   dms ipc call plugins status <pluginId>
   ```
3. List all plugins:
   ```bash
   dms ipc call plugins list
   ```
4. **If reload fails with `PLUGIN_RELOAD_FAILED`**, clear the QML cache and restart:
   ```bash
   rm -rf ~/.cache/noctalia-qs/qmlcache/
   dms restart
   ```
   ⚠️ DMS caches compiled QML (`.qmlc`/`.jsc` files) aggressively and does NOT auto-invalidate when plugin source changes. A stale cache causes `reload` and `enable` to fail silently even when the QML is syntactically correct. Always try cache-clearing + full restart before debugging phantom errors.
5. Full restart if hot-reload doesn't catch changes: `quickshell --replace` or `dms restart`.
6. After a full restart, check plugin loads without errors:
   ```bash
   journalctl --user -u dms --since "30 seconds ago" --no-pager | grep -i "plugin loaded"
   ```
   Look for `INFO qml: DankBar: Plugin loaded: <yourPlugin>` — no ERROR or WARN for your plugin.

7. **Duplicate DMS instance pitfall**: Running `dms run` (foreground debug
   mode) while DMS is already running as a user service spawns a second DMS
   process. This produces two visible DankBars (duplicated bar on all
   monitors) and causes daemon-plugin toggles to silently fail.

   Fix: kill ALL DMS processes, then restart:
   ```bash
   pkill -f 'dms run'     # kill any debug instances
   dms restart              # restart service cleanly
   ps aux | grep -c '[q]uickshell'  # should be 1
   ```

   To debug plugin errors without spawning a second DMS, use journalctl:
   ```bash
   journalctl --user -u dms -f --no-pager | grep -i 'error\\|warning\\|plugin loaded\\|aiAssistant'
   ```
7. Verify icon/text sizes respond to bar config changes (thickness, font scale, maximize toggles).
8. Check both horizontal (top/bottom) and vertical (left/right) bar orientations.
