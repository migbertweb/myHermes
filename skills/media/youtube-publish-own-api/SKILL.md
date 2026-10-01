---
name: youtube-publish-own-api
description: Publica videos en YouTube usando API propia y tokens.
version: 1.0.0
author: Migbert
license: MIT
platforms: [cachyos]
metadata:
  hermes:
    type: script-wrapper
related_skills: []
---

# Publicar en YouTube (API Propia)

Skill para automatizar la subida de videos a YouTube utilizando el script `publish_youtube_own_api.py` con credenciales OAuth2.

## Configuración

Requiere las siguientes variables de entorno en `~/.env`:
- `YOUTUBE_REFRESH_TOKEN`: Token de refresco obtenido vía `generate_youtube_token.py`.
- `YOUTUBE_CLIENT_SECRET`: Secreto del cliente de Google Cloud.
- `YOUTUBE_CREDENTIALS_FILE`: Ruta al archivo JSON de credenciales.

## Uso

El script procesa videos desde la carpeta de sincronización configurada y los sube automáticamente.

```bash
python3 /home/migbert/publish_youtube_own_api.py
```

## Flujo de Tokens
Para rotar el canal o renovar el token:
1. Ejecutar `python3 /home/migbert/generate_youtube_token.py`.
2. Copiar la URL en el navegador y autorizar el canal.
3. Pegar el código de autorización en el script.
4. Actualizar `YOUTUBE_REFRESH_TOKEN` en `~/.env`.
