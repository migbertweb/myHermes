# Hermes API Server Setup

The Hermes Agent gateway includes an OpenAI-compatible API Server
(puerto 8642 por defecto) que expone los endpoints:
- `GET /health` — health check
- `GET /v1/models` — lista de modelos
- `POST /v1/chat/completions` — chat (OpenAI-compatible, con streaming SSE)

## Activación

1. Agregar al `.env` del profile:
```
API_SERVER_ENABLED=true
API_SERVER_KEY=<random-key>
API_SERVER_HOST=0.0.0.0
# API_SERVER_PORT=8642  # opcional, default 8642
```

2. Instalar dependencias en el venv de Hermes:
```
uv pip install aiohttp --python ~/.hermes/hermes-agent/venv/bin/python
```

3. Si Telegram también se usa, instalar además:
```
uv pip install idna 'httpcore[asyncio]' --python ~/.hermes/hermes-agent/venv/bin/python
```

4. Reiniciar el gateway:
```
systemctl --user restart hermes-gateway
```

5. Verificar:
```bash
curl http://localhost:8642/health
curl http://localhost:8642/v1/models
curl http://localhost:8642/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <API_SERVER_KEY>" \
  -d '{"model":"hermes-agent","messages":[{"role":"user","content":"Hola"}]}'
```

## Plugin DMS / Cliente externo

Configurar en el cliente:
- **Provider**: `custom`
- **URL**: `http://<server-ip>:8642/v1/chat/completions`
- **API Key**: el valor de `API_SERVER_KEY`

## Troubleshooting

- Si el gateway falla con `No module named 'idna'` o `ModuleNotFoundError` después de activar el API Server: instalar `idna` en el venv.
- Si Telegram falla con `Running with asyncio requires installation of 'httpcore[asyncio]'`: instalar `httpcore[asyncio]` en el venv.
- Si `send_message` tool falla con `ImportError: cannot import name 'TaskHandle' from 'anyio._core._tasks'`: es un bug conocido al instalar `aiohttp` (trae `anyio>=4.14.0`). Workaround: reiniciar el gateway para limpiar pycache, o enviar directo via API de Telegram con `curl/urllib`.
- Si OpenCode u otro cliente OpenAI-compatible falla con _"Type validation failed: Value: {"tool":"...","emoji":"...","label":"..."}"_ al usar streaming: el API Server envía eventos custom `hermes.tool.progress` que clientes con validación estricta de esquema no aceptan. Ver `acp-coding-agents` skill → sección OpenCode → "Known issue: custom SSE events break streaming" para la solución completa.
- El API Server no aparece en `ss -tlnp` inmediatamente después del restart — esperar 5-10s.
