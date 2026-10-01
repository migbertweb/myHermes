# Hermes API Server Integration with DMS AI Assistant Plugin

## Overview

Connect a DMS daemon plugin (specifically the AI Assistant) to Hermes Agent as an OpenAI-compatible backend. The plugin becomes "Hermes-aware" — showing agent status, capturing metadata, and providing slash commands.

## Architecture

```
Plugin (QML) ──curl──▶ Hermes Gateway API Server ──▶ Hermes Agent ──▶ Provider (OpenCode Zen, etc.)
                            127.0.0.1:8420
```

- Hermes Gateway exposes an OpenAI-compatible `/v1/chat/completions` endpoint
- Plugin uses `custom` provider → `http://127.0.0.1:8420` with the configured API key
- Hermes handles auth, memory, skills, tools internally

## Setup

### Hermes Gateway

1. Enable API server in `~/.hermes/.env`:
   ```
   API_SERVER_ENABLED=true
   API_SERVER_HOST=127.0.0.1
   API_SERVER_PORT=8420
   API_SERVER_KEY=<hex-key>
   API_SERVER_MODEL_NAME=hermes-agent
   ```
2. Start: `hermes gateway run`
3. Install as systemd service: `hermes gateway install` (auto-start on login)

⚠️ **API key redaction**: The built-in secret redaction can block API keys in terminal output. Use hex keys (`secrets.token_hex(16)`) or avoid patterns that trigger redaction. Use Python via `urllib.request` for testing instead of shell curl.

### Plugin Configuration

In `~/.config/DankMaterialShell/plugin_settings.json`:
```json
{
  "aiAssistant": {
    "provider": "custom",
    "baseUrl": "http://127.0.0.1:8420",
    "model": "hermes-agent",
    "apiKey": "<same-hex-key>",
    "saveApiKey": true
  }
}
```

## Extension Patterns

### 1. Hermes Mode Detection

In `AIAssistantService.qml`, detect when the plugin is talking to Hermes:

```qml
property bool isHermesMode: false

function checkHermesMode() {
    isHermesMode = provider === "custom"
        && (baseUrl.includes("127.0.0.1:8420")
         || baseUrl.includes("localhost:8420")
         || baseUrl.includes("hermes"));
}
```

Call in `loadSettings()` and `handleConfigChanged()`.

### 2. Capture Session ID and Token Usage

Add properties:
```qml
property string hermesSessionId: ""
property int lastPromptTokens: 0
property int lastCompletionTokens: 0
property int lastTotalTokens: 0
```

Capture in `parseProviderDelta()` (OpenAI-compatible branch — streaming path):
```javascript
if (data.id && !hermesSessionId)
    hermesSessionId = data.id;
if (data.usage) {
    lastPromptTokens = data.usage.prompt_tokens || 0;
    lastCompletionTokens = data.usage.completion_tokens || 0;
    lastTotalTokens = data.usage.total_tokens || 0;
}
```

Capture in `handleStreamFinished()` (non-streaming fallback):
```javascript
try {
    const fallbackData = JSON.parse(bodyText);
    if (fallbackData.id && !hermesSessionId)
        hermesSessionId = fallbackData.id;
    if (fallbackData.usage) { /* capture tokens */ }
} catch (_) {}
```

Reset at start of each request in `startStreaming()`.

### 3. UI Badges in Header

In `AIAssistant.qml` header `RowLayout`, add after the online-status dot:

```qml
// Hermes badge — visible only in Hermes mode
Rectangle {
    visible: aiService.isHermesMode
    // ... styling ...
    StyledText { text: "🤖 Hermes" }
}

// Token counter — visible after each response
Rectangle {
    visible: !aiService.isStreaming && aiService.isHermesMode && aiService.lastTotalTokens > 0
    StyledText { text: "⚡" + aiService.lastTotalTokens + " tok" }
}
```

⚠️ **Avoid ToolTip from QtQuick.Controls** — not fully compatible with Quickshell runtime per AGENTS.md conventions.

### 4. Hermes Status Section in Settings

In `AIAssistantSettings.qml`, add a section visible only when `aiService.isHermesMode`:
- Model name
- Endpoint URL
- Connection status (✅/⏳)
- Session ID (safe guard: use `aiService.hermesSessionId && aiService.hermesSessionId.length > 0`)
- Token usage from last response

### 6. Real Provider/Model from Hermes Config File + Streaming

Instead of showing hardcoded "CUSTOM hermes-agent" in the header, fetch the actual Hermes provider and model from `~/.hermes/config.yaml` using a `Process` component.

**New properties in** `AIAssistantService.qml`:
```qml
property bool isHermesMode: false
property string hermesProvider: ""
property string hermesModel: ""
```

**Config reader Process** (add after `mkdirProcess`):
```qml
Process {
    id: hermesConfigReader
    command: [
        "sh", "-c",
        "head -4 ~/.hermes/config.yaml | tail -2 | sed 's/.*: //'"
    ]
    running: false

    stdout: StdioCollector {
        id: hermesConfigCollector
        onTextChanged: {
            const text = (this.text || "").trim();
            const lines = text.split('\n').filter(l => l.trim());
            if (lines.length >= 2) {
                root.hermesModel = lines[0].trim();
                root.hermesProvider = lines[1].trim();
            }
        }
    }

    onExited: (code) => {
        if (code !== 0) {
            console.warn("[AIAssistantService] Failed to read Hermes config, exit code:", code);
            root.hermesProvider = "opencode-zen";
            root.hermesModel = "deepseek-v4-flash-free";
        } else {
            console.log("[AIAssistantService] Hermes config loaded:", root.hermesProvider, root.hermesModel);
        }
    }
}
```

**Updated `checkHermesMode()`** to trigger config reading:
```qml
function checkHermesMode() {
    const p = provider;
    const url = baseUrl;
    const wasHermesMode = isHermesMode;
    isHermesMode = p === "custom" && (url.includes("127.0.0.1:8420") || url.includes("localhost:8420") || url.includes("hermes"));
    if (isHermesMode && !wasHermesMode) {
        hermesConfigReader.running = true;
    }
    if (!isHermesMode) {
        hermesProvider = "";
        hermesModel = "";
    }
}
```

**Conditional badge display in** `AIAssistant.qml`:
```qml
// Provider + Model badge — shows real values in Hermes mode
StyledText {
    text: aiService.isHermesMode
        ? (aiService.hermesProvider || "opencode-zen") + " " + (aiService.hermesModel || "deepseek-v4-flash-free")
        : (aiService.provider || "openai").toUpperCase() + " " + (aiService.model || "")
}
```

**Output (head -4 ~/.hermes/config.yaml):**
```
model:
  base_url: ''
  default: deepseek-v4-flash-free
  provider: opencode-zen
```
Lines 3-4 give `model` then `provider`. The `sed 's/.*: //'` strips the key prefix.

**Fallback values** included in the onExited handler so the header still shows sensible defaults if the config file is missing or unreadable.

#### Two Levels of Model/Provider Changes

Hermes has two mechanisms for changing the model, and the plugin handles both:

| Change type | What it modifies | How the plugin detects it |
|---|---|---|
| `hermes config set model.default X` | `~/.hermes/config.yaml` (persistent) | Config reader Process reads the file |
| `/model X` (TUI/CLI slash command) | Current Hermes session only (NOT config.yaml) | Dynamic capture from `data.model` in streaming response |

**⚠️ Important**: `/model` in TUI/CLI changes the model for the active Hermes session without touching config.yaml. The config reader alone would never detect this change.

#### Dynamic Model Capture from Streaming

To handle session-level changes (like `/model`), capture `data.model` from each streaming SSE chunk. Hermes returns the model name in its OpenAI-compatible format in every chunk of `/v1/chat/completions`:

```javascript
// In parseProviderDelta() — OpenAI-compatible branch:
if (data.model && data.model !== hermesModel)
    hermesModel = data.model;
```

Add this right after the `hermesSessionId` capture (before token usage), inside the `else { // openai }` block:

```javascript
// Capture the active model Hermes reports in each chunk
if (data.model && data.model !== hermesModel)
    hermesModel = data.model;
```

**Flow**: The first chunk after a `/model` command will contain the new model name, and `hermesModel` updates immediately. The next message's response confirms the change visually.

#### Conditional Badge Display

Common minimalistic cleanups for the AI Assistant chat UI:

#### Remove Redundant Role Labels/Icons from Bubbles

In `MessageBubble.qml`, remove the `Rectangle` pill with `I18n.tr("You")` / `I18n.tr("Assistant")` and the circular `DankIcon` (`person` / `smart_toy`). The bubble color + right/left alignment already signals the role — text labels and icons are redundant.

#### Compact Spacing

| Location | Before | After |
|----------|--------|-------|
| Bubble padding | `Theme.spacingM * 2` | `Theme.spacingS * 2` |
| Bubble column spacing | `Theme.spacingS` | `Theme.spacingXS` |
| List spacing | `Theme.spacingM` | `Theme.spacingXS` |
| List topGap (role change) | `Theme.spacingM` | `Theme.spacingXS` |

#### Remove Gap Between Action Buttons and Content

In `MessageBubble.qml`, remove the separator `Item { width: 1; height: Theme.spacingS }` between the action button row and the message content.

#### Clean Input Row

In `AIAssistant.qml` composer `RowLayout`:

| Icon | State | Description |
|------|-------|-------------|
| `attach_file` | Always visible (when not streaming) | Paperclip placeholder for future attachment feature |
| `arrow_upward` | Visible when NOT streaming | Send button with `backgroundColor: Theme.primary` + `iconColor: Theme.onPrimary` |
| `hourglass_empty` | Visible when streaming | Thinking indicator, replaces old `stop` icon |

The spacer `Item { Layout.fillWidth: true }` keeps attach_file left-aligned and send/thinking right-aligned.

### 8. Slash Commands

In `AIAssistantService.qml`, add `executeHermesCommand(cmdText)` that returns a markdown response string:

| Command | Response |
|---------|----------|
| `/help` | List of commands |
| `/hermes status` | Agent state (model, endpoint, connection, tokens) |
| `/hermes model` | Active model + provider |
| `/hermes session` | Current Hermes session ID |
| `/hermes usage` | Token breakdown |
| `/hermes tools` | Available Hermes toolsets |
| `/hermes memory` | Memory status |

In `AIAssistant.qml`, modify `sendCurrentMessage()` to detect `/` prefix:
```javascript
if (text.startsWith("/")) {
    const response = svc.executeHermesCommand(text);
    // Add as user message + assistant response to messagesModel
    svc.messagesModel.append({ role: "user", content: text, ... });
    svc.messagesModel.append({ role: "assistant", content: response, ... });
    svc.saveSession();
    return;
}
```

## Timeout Handling (Watchdog Timer)

When Hermes is unreachable or a request hangs, the plugin must not show an infinite "streaming" state. Implement a watchdog timer in `AIAssistantService.qml`:

### Watchdog Timer Component

```qml
// Property to track timeout state
property bool isTimingOut: false

Timer {
    id: requestTimeoutTimer
    interval: 90000  // 90 seconds — ajusta si tu proveedor es lento
    repeat: false
    onTriggered: {
        if (isStreaming && chatFetcher.running) {
            console.log("[AIAssistantService] Request timeout reached. Cancelling...");
            chatFetcher.running = false;
            markError(activeStreamId, "Hermes took too long to respond. Connection timeout.");
        }
    }
}
```

### Lifecycle

| Event | Action |
|-------|--------|
| Stream starts (`startStreaming()`) | `requestTimeoutTimer.start()` |
| User cancels (`cancel()`) | `requestTimeoutTimer.stop()` before `markError()` |
| Stream completes naturally (`finalizeStream()`) | `requestTimeoutTimer.stop()` before setting `isStreaming = false` |
| Stream fails (connection error) | Timer fires but `chatFetcher.running` is already `false` -> no-op |

**Pitfall - escaped quotes in QML Timer `onTriggered`**: The `patch` tool can inject spurious backslash escapes (`\"`) into string literals inside `Timer.onTriggered` blocks. After patching, verify the file compiles by restarting DMS and checking `journalctl --user -u dms --since "10 seconds ago" --no-pager | grep -i "component error"`. If you see `Expected token ')'`, check the Timer block for `\\\"` literal sequences and replace with unescaped `"`.

**Pitfall - duplicate property declarations**: After applying multiple patches to `AIAssistantService.qml`, verify there are no duplicate `property` declarations (same name declared twice). QML rejects duplicates with `Duplicate property name`. Read lines 30-70 of the file and remove duplicates.

### Improved scroll-to-bottom

The original MessageList.qml had issues where newly appended messages didn't trigger auto-scroll because the ListView's `stickToBottom` logic was too sensitive.

**Tolerance**: Increase the tolerance in `onContentYChanged` from 20px to 40px:
```qml
onContentYChanged: {
    const maxY = Math.max(0, listView.contentHeight - listView.height);
    root.stickToBottom = listView.contentY >= maxY - 40;
}
```
This prevents small rendering jitters (from markdown height changes during streaming) from accidentally detaching the scroll.

**Force scroll on streaming start**: Add a second `Connections` block to force `stickToBottom` when `isStreaming` becomes `true`:
```qml
Connections {
    target: root.aiService
    function onIsStreamingChanged() {
        if (root.aiService && root.aiService.isStreaming) {
            root.stickToBottom = true;
            Qt.callLater(() => listView.positionViewAtEnd());
        }
    }
}
```
This ensures the user sees new tokens even if they had manually scrolled up to review earlier messages.

## Tool Call Detection from Streaming

When Hermes invokes a tool (e.g., `web_search`, `terminal`), modern models report tool calls via OpenAI-compatible `tool_calls` in `delta`. The plugin should detect these and display a visual indicator rather than showing raw JSON.

### Detection in `parseProviderDelta()`

In the `else { // openai }` branch, add detection **before** the text content handler:

```javascript
// In parseProviderDelta() -- after token capture, before text delta handling:

// Detectar tool_calls en streaming OpenAI-compatible
const toolCalls = data.choices?.[0]?.delta?.tool_calls;
if (toolCalls && Array.isArray(toolCalls)) {
    for (const tc of toolCalls) {
        if (tc.function && tc.function.name) {
            const toolMsg = "\n\n🛠️ **Hermes ejecutó:** `" + tc.function.name + "`\n";
            updateStreamContent(activeStreamId, toolMsg);
        }
    }
}
```

**Placement**: Insert this block immediately after the `const deltas = ...` line and before the `if (Array.isArray(deltas))` block:

```javascript
const deltas = data.choices?.[0]?.delta?.content;

// 🔧 Insert tool_calls detection HERE

if (Array.isArray(deltas)) { ... }
```

**Output**: When Hermes calls a tool, a line like `🛠️ Hermes ejecutó: web_search` appears in the chat bubble before the final response text. Tool execution results are included in the model's follow-up text.

**⚠️ Non-streaming fallback**: Some providers/models may send `tool_calls` only in the final message (not delta). If you don't see the indicator, check whether your model sends tool_calls in delta chunks or only in the non-streaming completion message. The pattern above handles only the delta/streaming case -- the most common path for Hermes.

### Gap-Based + Pattern-Based Tool Detection (Fallback for Models Without Delta tool_calls)

If the model does NOT emit `tool_calls` in streaming delta (e.g., DeepSeek v4 via opencode-zen), use a two-mechanism fallback:

#### Properties

```qml
property bool isHermesUsingTools: false
property int lastChunkTimestamp: 0
```

#### Mechanism 1: Gap Detection Timer

Add a timer that runs while `isStreaming` and checks how long since the last chunk:

```qml
Timer {
    id: toolActivityTimer
    interval: 600
    repeat: true
    running: isStreaming
    onTriggered: {
        if (isStreaming) {
            var elapsed = Date.now() - lastChunkTimestamp;
            if (elapsed > 2500 && !isHermesUsingTools) {
                console.log("[AIAssistantService] Tool activity detected (gap: " + elapsed + "ms)");
                isHermesUsingTools = true;
            }
        } else {
            isHermesUsingTools = false;
        }
    }
}
```

Update `lastChunkTimestamp` in `parseProviderDelta()` (OpenAI branch) on every chunk:

```javascript
// Inside the streaming handler, right after model capture:
lastChunkTimestamp = Date.now();
```

Reset on stream start:

```javascript
// In startStreaming(), before chatFetcher.running = true:
isHermesUsingTools = false;
lastChunkTimestamp = Date.now();
```

#### Mechanism 2: Pattern Matching in Response Text

After each text delta, scan the accumulated content for phrases that indicate tool usage:

```javascript
if (!isHermesUsingTools && deltas) {
    const content = getMessageContentById(activeStreamId) || "";
    const toolPatterns = [
        /based on (the|my|a) (search|web|research|analysis)/i,
        /according to (the )?(search|web|source|data)/i,
        /i (searched|looked up|found|retrieved|fetched)/i,
        /let me (search|look up|find|check|fetch|get)/i,
        /🔍|📊|📈|📉|🌐/,
        /the (search|web) (results?|data|information) (show|indicate|suggest)/i,
        /i (ran|executed|performed) (a|the) (search|query|analysis)/i,
    ];
    for (var pi = 0; pi < toolPatterns.length; pi++) {
        if (toolPatterns[pi].test(content)) {
            isHermesUsingTools = true;
            break;
        }
    }
}
```

#### UI Badge

In `AIAssistant.qml`, add after the status dot:

```qml
// Badge herramienta activa
Rectangle {
    visible: aiService.isHermesMode && aiService.isHermesUsingTools
    radius: Theme.cornerRadius
    color: Qt.rgba(Theme.warning.r, Theme.warning.g, Theme.warning.b, 0.15)
    border.color: Qt.rgba(Theme.warning.r, Theme.warning.g, Theme.warning.b, 0.4)
    border.width: 1
    height: Theme.fontSizeSmall * 1.6
    Layout.preferredWidth: toolsBadgeText.implicitWidth + Theme.spacingM
    Layout.alignment: Qt.AlignVCenter
    opacity: aiService.isHermesUsingTools ? 1.0 : 0.0
    Behavior on opacity { NumberAnimation { duration: 200 } }

    StyledText {
        id: toolsBadgeText
        anchors.centerIn: parent
        text: "🛠️ Tools"
        font.pixelSize: Theme.fontSizeSmall
        color: Theme.warning
    }
}
```

## Files Modified

| File | Role |
|------|------|
| `AIAssistantService.qml` | Properties, metadata capture, `checkHermesMode()`, `executeHermesCommand()` |
| `AIAssistant.qml` | UI badges, slash command routing |
| `AIAssistantSettings.qml` | Hermes status section |

## Session Linking (Plugin ↔ Hermes traceability)

By default, each plugin message is an anonymous chat completion in Hermes.
Session linking adds traceability so plugin conversations appear in `hermes sessions list`.

### Level 1: Local persistence (session.json v3)

Upgrade storage format to include hermesSessionId:

```qml
function persistCurrentMessagesForHash(configHash) {
    // ... collect messages ...
    nextSessions[configHash] = {
        hermesSessionId: hermesSessionId,  // ← NEW
        messages: capped
    };
}
```

Load with backward compatibility for v2 (flat array) and v3 (metadata object):

```qml
function switchConfigHistory(nextHash) {
    const raw = sessionsByConfig[nextHash];
    let nextMessages = [];
    if (Array.isArray(raw)) {
        nextMessages = raw;           // v2 legacy
        hermesSessionId = "";
    } else if (raw && typeof raw === "object" && Array.isArray(raw.messages)) {
        nextMessages = raw.messages;  // v3 metadata
        if (raw.hermesSessionId)
            hermesSessionId = raw.hermesSessionId;
    }
    loadMessages(nextMessages);
}
```

Bump saveSession version:
```qml
const data = { version: 3, ... };  // was 2
```

### Level 2: X-Hermes-Session-Id header (future-proofing)

Pass session ID back to Hermes on subsequent requests.

**⚠️ SAFE PATTERN — modify headers in the service, NOT the `.pragma library`:**

Modifying `.pragma library` JS files (like `AIApiAdapters.js`) while DMS is running can crash the QML engine due to aggressive compilation caching. Instead, inject the header **after** the adapter returns its result, in the service's `buildCurlCommand()`:

```qml
// In AIAssistantService.qml — buildCurlCommand():
const req = AIApiAdapters.buildRequest(provider, payload, key);
if (hermesSessionId && req && req.headers) {
    req.headers = req.headers.concat(["-H", "X-Hermes-Session-Id: " + hermesSessionId]);
}
```

This pattern:
- Uses `.concat()` (creates new array — safe, no `const` mutation)
- Keeps the change in a regular `.qml` file (not a compiled library)
- Has defensive null checks (`req && req.headers`)
- Only activates when `hermesSessionId` is truthy

Also pass the session_id in the payload from `buildPayload()`:
```qml
if (hermesSessionId)
    payload.hermesSessionId = hermesSessionId;
```

## Version History

| Version | Format | Loading path |
|---------|--------|-------------|
| 1 | Flat message array + providerConfigHash | `else` in onLoaded |
| 2 | Config-hash keyed: `{hash: [msg1, ...]}` | `data.version >= 2` |
| 3 | Metadata wrapper: `{hash: {hermesSessionId, messages}}` | Same as v2; switchConfigHistory() differentiates |

## Verification

1. Restart DMS: `dms restart`
2. Open assistant → verify "🤖 Hermes" badge in header (when connected)
3. Send a message → verify token counter appears after response
4. Type `/hermes status` → verify instant response without API call
5. Open settings → verify "🤖 Hermes Agent" section visible
