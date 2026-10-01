---
name: youtube-api-setup
description: Configura OAuth 2.0 y tokens para la API de YouTube.
platforms: [linux]
---

# YouTube API Auth Setup

Procedimiento para configurar el acceso a la API de YouTube y gestionar la rotación de tokens, especialmente en entornos TUI/Headless.

## Flujo de Generación de Token (Manual Code Flow)

Para evitar errores de `run_local_server` (puertos bloqueados) o `run_console` (obsoleto), utiliza el flujo de código manual:

1. **Carga de Credenciales:** Usar el archivo `client_secret.json` descargado de Google Cloud Console.
2. **URL de Autorización:** Generar la URL mediante `flow.authorization_url(prompt='consent', access_type='offline')`.
3. **Interacción:** El usuario visita la URL, acepta los permisos y es redirigido a una URL de callback (ej. `http://localhost:8080/?code=XYZ`).
4. **Captura:** Copiar el valor del parámetro `code` de la barra de direcciones del navegador.
5. **Intercambio:** Ejecutar `flow.fetch_token(code=code)` para obtener el `refresh_token`.

## Pitfalls Críticos

### Error `unauthorized_client`
**Síntoma:** `google.auth.exceptions.RefreshError: ('unauthorized_client: Unauthorized', ...)`

**Causa Raíz:** El `refresh_token` fue generado con un par `client_id`/`client_secret` distinto al que el script usa actualmente. El token está vinculado permanentemente al cliente que lo creó.

**Regla:** Si cambias el archivo JSON de credenciales $\rightarrow$ DEBES regenerar el token usando el nuevo JSON.

### Requisitos de Autorización
- **Scope:** Usar `https://www.googleapis.com/auth/youtube.force-ssl` para permisos de subida.
- **Consentimiento:** Usar siempre `prompt='consent'` para asegurar que Google entregue el `refresh_token` (sin esto, solo entrega el `access_token` temporal).
- **Canales Múltiples:** Cada cuenta de Google/Canal requiere su propio `refresh_token`.

## Multi-Channel Setup (env vars, no config.yaml)

Cuando manejas más de un canal con un solo script de publicación:

1. Descarga un `client_secret*.json` distinto por canal (ej. `client_secret_channel2.json`).
2. Genera un `refresh_token` por canal con su propio JSON.
3. Asigna variables de entorno con sufijo para distinguirlos:
   ```bash
   export YOUTUBE_REFRESH_TOKEN="<token canal 1>"
   export YOUTUBE_REFRESH_TOKEN2="<token canal 2>"
   export YOUTUBE_CREDENTIALS_FILE="/home/migbert/client_secret_channel2.json"
   ```
4. Haz que el script prefiera el token con sufijo, con fallback al genérico:
   ```python
   REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN2") or os.getenv("YOUTUBE_REFRESH_TOKEN")
   ```
   Si el script solo lee la variable sin sufijo y tú actualizas la variable sin sufijo, el script sigue usando el token viejo.

## Verificación del canal antes de subir

Un token válido no significa el canal correcto. Verifica antes de publicar:

```python
service = build("youtube", "v3", credentials=creds)
resp = service.channels().list(part="id,snippet", mine=True, maxResults=5).execute()
for ch in resp.get("items", []):
    print(ch["snippet"]["title"], ch["id"])
```

**No uses `videos().list(mine=True)`** — lanza `TypeError: unexpected keyword argument 'mine'`. `mine` solo es válido en `channels()`.
