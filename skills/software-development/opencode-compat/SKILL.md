---
name: opencode-compat
description: Resolver errores de validación SSE en OpenCode (extensión VSCodium/CLI) al conectar con el API server de Hermes. OpenCode valida estrictamente el esquema OpenAI sobre toda línea `data:` del SSE y falla cuando recibe eventos custom `hermes.tool.progress`.
---

# OpenCode Compatibility

## Síntoma

OpenCode (extensión VSCodium o CLI) muestra error de validación de tipo al conectarse al API server de Hermes:

```
Type validation failed: Value: {"tool":"browser_navigate","emoji":"🌐","label":"<url>","toolCallId":"call_...","status":"running"}
Error message: [{"code":"invalid_union","errors":[[{"expected":"array","code":"invalid_type","path":["choices"],"message":"Invalid input: expected array, received undefined"}]],"path":[],"message":"Invalid input"}]
```

## Causa

El API server de Hermes envía eventos SSE custom (`event: hermes.tool.progress`) con objetos que contienen `tool`, `emoji`, `label`, `toolCallId`, `status` — campos que no forman parte del esquema OpenAI. OpenCode valida cada línea `data:` contra el esquema estricto de chat.completion.chunk y rechaza cualquier objeto que no tenga `choices[]`.

## Solución (tres capas)

### Capa 1 — config.yaml (override por plataforma)

Agrega `tool_progress: off` dentro del bloque `display.platforms` existente:

```yaml
display:
  platforms:
    api_server:
      tool_progress: off
```

> **⚠ Importante:** Debe estar dentro del MISMO bloque `platforms:` que ya existe en tu config.yaml (donde normalmente están `telegram`, `discord`, etc.). Si hay dos bloques `platforms:` al mismo nivel en YAML, el segundo pisa al primero — YAML no hace merge, usa el último valor.

### Capa 2 — código: `gateway/platforms/api_server.py`

En la función `_handle_chat_completions`, dentro del bloque `if stream:`, agregar verificación de la configuración ANTES de definir los callbacks `_on_tool_start` / `_on_tool_complete`:

```python
# Dentro de `if stream:`, ANTES de definir _on_tool_start
from gateway.run import _load_gateway_config as _lgc
from gateway.display_config import resolve_display_setting as _rds
_show_tool_progress = _rds(_lgc(), "api_server", "tool_progress") != "off"
```

Y al pasar los callbacks a `self._run_agent(...)`:

```python
tool_start_callback=_on_tool_start if _show_tool_progress else None,
tool_complete_callback=_on_tool_complete if _show_tool_progress else None,
```

### Capa 3 — default en código: `gateway/display_config.py`

En `_PLATFORM_DEFAULTS`, agregar `"tool_progress": "off"` a la entrada `api_server`:

```python
"api_server": {**_TIER_HIGH, "tool_preview_length": 0, "tool_progress": "off"},
```

Esto hace que el default sea `off` aunque el usuario no configure nada.

## Verificación

Probar con curl que el stream SSE ya no contiene `hermes.tool.progress`:

```bash
curl -s -N -X POST http://localhost:8642/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer *** \
  -d '{"model":"<model>","messages":[{"role":"user","content":"say hello"}],"stream":true}'
```

Confirmar que:
- No hay líneas `event: hermes.tool.progress`
- Toda línea `data:` tiene `choices[]` (formato OpenAI estándar)
- Termina con `data: [DONE]`

## Notas

- El API server escucha en puerto 8642 por defecto.
- La API key está en `~/.hermes/.env` como `API_SERVER_KEY`.
- Los eventos `hermes.tool.progress` son puramente decorativos para el frontend (Open WebUI los usa para mostrar animaciones de tool calls). Deshabilitarlos no afecta la funcionalidad del agente.
- La plataforma `api_server` no tenía entrada explícita en `_PLATFORM_DEFAULTS`, heredando el default global `tool_progress: "all"`.
