# Desktop/TUI Model Resolution Chain

How Hermes Desktop (Electron/Ink) determines the model and provider for a new chat session.

## Priority Chain

When a session is created, the model is resolved in this order:

### 1. Frontend UI Store (`$currentModel`) — highest priority

The desktop app's React/Ink frontend maintains `$currentModel` and `$currentProvider` in its own nanostores store (`apps/desktop/src/store/session.ts`). When the user or app calls `session.create`, the frontend sends:

```json
{
  "model": "deepseek-v4-flash-free",
  "provider": "opencode-zen"
}
```

These become the **`model_override`** in `_make_agent()` (`tui_gateway/server.py:4922-4926`):

```python
create_model = str(params.get("model") or "").strip()
session_model_override = (
    {"model": create_model, "provider": str(params.get("provider") or "").strip() or None}
    if create_model
    else None
)
```

When `model_override` is a dict with `"model"`, it bypasses `config.yaml` entirely:

```python
# server.py:4270-4271
if isinstance(model_override, dict) and model_override.get("model"):
    model = str(model_override.get("model") or "")
    requested_provider = model_override.get("provider") or provider_override or None
```

### 2. Config file (`config.yaml > model.default`) — fallback

When no model is sent from the frontend (empty/null), `_resolve_startup_runtime()` reads from config:

```python
# server.py:4311
model, requested_provider = _resolve_startup_runtime()
```

Which calls `_resolve_model()` (`server.py:1924`):
```python
def _resolve_model() -> str:
    env = os.environ.get("HERMES_MODEL", "") or os.environ.get("HERMES_INFERENCE_MODEL", "")
    if env:
        return env
    m = _load_cfg().get("model", "")
    if isinstance(m, dict):
        return str(m.get("default", "") or "").strip()
    ...
```

### 3. Env vars (`HERMES_MODEL`, `HERMES_INFERENCE_MODEL`) — lowest priority

Consulted only if config has no `model.default`.

## How the UI State Gets Seeded

On app startup, `refreshCurrentModel()` (`use-model-controls.ts:43`) calls `getGlobalModelInfo()`, which hits the gateway's `/api/model/info` endpoint. This returns the **resolved model from config.yaml** (or env). The result populates `$currentModel` and `$currentProvider`.

However, once seeded, the frontend store is **independent** — changing `config.yaml` does NOT update it. The user must:
- Restart the desktop app (triggers a fresh `/api/model/info` call)
- Explicitly switch models in Settings → Model (UI picker → `selectModel()`)

## The `_SlashWorker` Model

The slash-command subprocess also receives the model via `--model` flag:

```python
# server.py:274-282
argv = [
    sys.executable,
    "-m", "tui_gateway.slash_worker",
    "--session-key", session_key,
]
if model:
    argv += ["--model", model]
```

This is the **same model** as the agent's — sourced from the same resolution chain above.

## Practical Implications for Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `config.yaml > model.default` changed but new chats use old model | Desktop UI store has stale model from old seed | Switch model in Settings → Model picker, or restart desktop app |
| `/model` switch only applies to current chat | The switch calls `config.set` which writes to config AND updates the live session's `model_override`, but does NOT update the `$currentModel` in the frontend's `session.ts` store | The next new chat will re-read the UI store (which may still hold the prior model) |
| New chat uses `deepseek-v4-flash-free` while config says `deepseek/deepseek-v4-flash` | The frontend `$currentModel` was seeded before the config change and retains the old value | Manually select the new model in the desktop UI model picker |

## Key Source Files

| File | Purpose |
|------|---------|
| `tui_gateway/server.py` | Gateway: `_make_agent()`, `_resolve_model()`, `_resolve_startup_runtime()`, `session.create` handler |
| `apps/desktop/src/store/session.ts` | Frontend: `$currentModel`, `$currentProvider`, `$currentReasoningEffort` stores |
| `apps/desktop/src/app/session/hooks/use-model-controls.ts` | Frontend: `refreshCurrentModel()`, `selectModel()` — seeding and switching logic |
| `apps/desktop/src/app/shell/model-menu-panel.tsx` | Frontend: model picker UI dropdown |
| `apps/desktop/src/hermes.ts` | Frontend: `getGlobalModelInfo()` — calls `/api/model/info` |
| `cli.py` | CLI-side model resolution for comparison (`model or config > default > fallback`) |
