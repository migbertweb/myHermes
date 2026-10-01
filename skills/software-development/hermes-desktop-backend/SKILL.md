---
name: hermes-desktop-backend
description: "Configurar el backend remoto para Hermes Desktop — dashboard, systemd, credenciales y conexión desde la app de escritorio."
version: 1.1.0
author: Hermes Agent
platforms: [linux]
tags: [hermes, desktop, dashboard, backend, systemd, remote]
---

# Hermes Desktop Backend

Configura el servidor remoto (backend) para que Hermes Desktop se conecte desde otra máquina.

## Visión general

Hermes Desktop es una app nativa (Electron) para macOS/Windows/Linux. Se conecta a un **backend** remoto donde corre `hermes dashboard`, no al API Server directamente.

## Paso 1: Credenciales en `.env`

Agrega al `~/.hermes/.env` del servidor:

```bash
HERMES_DASHBOARD_BASIC_AUTH_USERNAME=admin
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=$(openssl rand -base64 32)
HERMES_DASHBOARD_BASIC_AUTH_SECRET=$(openssl rand -base64 32)
```

- `USERNAME` / `PASSWORD` — credenciales para login en la app Desktop
- `SECRET` — firma de sesión; sin esto se cierra sesión en cada reinicio

Siempre pon `chmod 600 ~/.hermes/.env`.

## Paso 2: Iniciar el dashboard

```bash
hermes dashboard --no-open --host 0.0.0.0 --port 9119
```

- `--host 0.0.0.0` permite conexiones desde otras máquinas en la red
- `--port 9119` es el puerto por defecto
- El `--no-open` evita abrir el navegador (útil en servidor headless)

## Paso 3: Systemd service (arranque automático)

El proceso dashboard debe **persistir** entre reinicios. Crear servicio user systemd:

### `/home/piro/.config/systemd/user/hermes-dashboard.service`

```ini
[Unit]
Description=Hermes Agent Dashboard - Remote Backend for Hermes Desktop
After=network-online.target hermes-gateway.service
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart=/home/piro/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main dashboard --no-open --host 0.0.0.0 --port 9119
WorkingDirectory=/home/piro/.hermes
Environment="PATH=/home/piro/.hermes/hermes-agent/venv/bin:/home/piro/.hermes/hermes-agent/node_modules/.bin:/home/piro/.hermes/node/bin:/home/piro/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="VIRTUAL_ENV=/home/piro/.hermes/hermes-agent/venv"
Environment="HERMES_HOME=/home/piro/.hermes"
EnvironmentFile=%h/.hermes/.env
Restart=always
RestartSec=10
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable hermes-dashboard.service
systemctl --user start hermes-dashboard.service
```

Verificar:
```bash
systemctl --user status hermes-dashboard.service
ss -tlnp | grep 9119
curl -s http://localhost:9119/api/status | python3 -m json.tool
```

## Paso 4: Conectar desde la app Desktop

En **Settings → Gateway → Remote gateway**:

1. **Remote URL**: `http://<ip-del-servidor>:9119` (ej: `http://192.168.1.8:9119`)
2. **Sign in** → entrar con las credenciales del `.env`
3. **Save and reconnect**

También se puede prefijar con `HERMES_DESKTOP_REMOTE_URL` antes de lanzar la app.

## Voice & Transcription (STT)

Hermes Desktop tiene un botón de grabación de voz que envía el audio al backend del dashboard para transcripción.

### Flujo del audio

1. El navegador/Desktop graba audio (webm, opus, wav, etc.)
2. Convierte a **base64 data URL** y hace POST a `/api/audio/transcribe`
3. El dashboard guarda el audio en un archivo temporal y llama a `transcribe_audio()`
4. Devuelve el texto transcrito al Desktop

**⚠️ Diferencia clave con Telegram:** Telegram envía el audio como archivo (descarga directa .ogg), mientras que el Desktop lo envía como base64. Ambos terminan llamando a la misma función `transcribe_audio()`, pero el **formato de audio** puede variar (webm del navegador vs ogg de Telegram).

### Configuración STT

```yaml
stt:
  enabled: true
  provider: local          # local | groq | openai | mistral | xai | elevenlabs
  local:
    model: base            # tiny, base, small, medium, large-v3
    language: es           # idioma para faster-whisper
```

### Proveedores disponibles

| Provider | API Key | Gratuito |
|----------|---------|----------|
| `local` (faster-whisper) | Ninguna | Sí — requiere `pip install faster-whisper` |
| `groq` | `GROQ_API_KEY` | Sí (free tier) |
| `openai` | `VOICE_TOOLS_OPENAI_KEY` | No |
| `mistral` | `MISTRAL_API_KEY` | No |
| `xai` | `XAI_API_KEY` | No |
| `elevenlabs` | `ELEVENLABS_API_KEY` | No |

### Troubleshooting

| Problema | Causa | Solución |
|----------|-------|----------|
| 401 / "Invalid credentials" | Usuario/contraseña incorrectos | Revisar `.env` |
| No aparece botón Sign in | No detecta `basic` auth | Confirmar USERNAME + PASSWORD en `.env` |
| Cierra sesión al reiniciar | Falta `AUTH_SECRET` | Agregar `HERMES_DASHBOARD_BASIC_AUTH_SECRET` |
| Connection refused | Dashboard no corre o bind a 127.0.0.1 | `systemctl --user status hermes-dashboard.service` |
| Dashboard no escucha | Está compilando frontend (primera vez) | Esperar 30-60s, luego verificar con `ss` |
| "Voice transcription failed" | STT provider configurado sin API key | Cambiar `stt.provider` a `local` (ya instalado) o agregar la API key correspondiente en `.env` |
| "Voice transcription failed" (con local) | faster-whisper no instalado o falta `tokenizers` | `uv pip install faster-whisper --python ~/.hermes/hermes-agent/venv/bin/python` |
| "Voice transcription failed" solo en Desktop (Telegram funciona) | Diferencia en formato de audio entre navegador y Telegram o desincronización entre Dashboard y Gateway | Verificar logs del dashboard: `journalctl --user -u hermes-dashboard --since "5 min ago" | grep -i "transcri|voice|error"`. Reiniciar AMBOS servicios: `systemctl --user restart hermes-dashboard.service hermes-gateway.service` |
| Transcripción no funciona tras cambiar config | Gateway no reiniciado | El dashboard lee la config del gateway. Reiniciar: `systemctl --user restart hermes-gateway` (desde terminal separada, no desde TUI) |
| Audio grabado pero no se envía | Error de micrófono/permissions en el navegador | Verificar que Hermes Desktop tenga permiso de micrófono en el sistema |\n\n### Security & Networking\n\nTo avoid the \"API server is network-accessible\" warning and secure the instance, use a firewall to restrict access to the dashboard and API ports to trusted local IPs:\n\n```bash\nsudo ufw allow from 192.168.1.0/24 to any port 8642\nsudo ufw allow from 192.168.1.0/24 to any port 9119\n```\n\n## Verificación (desde el servidor)

```bash
# 1. ¿Está escuchando?
ss -tlnp | grep 9119

# 2. Estado general (sin auth)
curl -s http://localhost:9119/api/status | python3 -m json.tool

# 3. Verificar que la autenticación funciona con credenciales reales
curl -s -u "admin:password" http://localhost:9119/api/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"Auth required: {d.get('auth_required')}\")
print(f\"Providers: {d.get('auth_providers')}\")
print(f\"Version: {d.get('version')}\")
"
```

Debe responder `auth_required: true` con `providers: ["basic"]`.  
Si el paso 3 falla con 401, las credenciales en `.env` no coinciden con lo que cargó el proceso — revisar el `EnvironmentFile` del systemd service o reiniciar el servicio.

## Paso 5: Client-side — .desktop entry para la laptop

Para tener Hermes Desktop como una app lanzable desde el menú de aplicaciones de la laptop (GNOME/KDE/Hyprland), crear un `.desktop` entry y copiar el ícono.

### Ubicación del ícono

El ícono oficial está en el repositorio de Hermes del servidor:

```
~/.hermes/hermes-agent/apps/desktop/assets/icon.png
~/.hermes/hermes-agent/apps/desktop/assets/icon.ico
```

Copiarlo a la laptop y registrarlo en el tema de íconos:

```bash
# Crear directorios si no existen
mkdir -p ~/.local/share/icons
mkdir -p ~/.local/share/icons/hicolor/256x256/apps

# Copiar el ícono
cp /ruta/al/icon.png ~/.local/share/icons/hermes.png
cp /ruta/al/icon.png ~/.local/share/icons/hicolor/256x256/apps/hermes.png

# Refrescar caché de íconos
gtk-update-icon-cache ~/.local/share/icons/hicolor 2>/dev/null || true
```

### Archivo `.desktop`

`~/.local/share/applications/hermes-desktop.desktop`:

```ini
[Desktop Entry]
Name=Hermes Desktop
Comment=Cliente de escritorio para Hermes Agent
Exec=/home/migbert/.local/bin/hermes desktop
Icon=hermes
Terminal=false
Type=Application
Categories=Network;Development;
StartupNotify=true
StartupWMClass=hermes-desktop
```

**Notas:**
- Ajustar `Exec` a la ruta real de `hermes` en la laptop (puede ser `~/.local/bin/hermes`, `/usr/bin/hermes`, o la ruta al wrapper del venv).
- El wrapper `~/.local/bin/hermes` suele ser un script que ejecuta el binario del venv. Verificar con `cat ~/.local/bin/hermes`.
- Si la app no aparece en el menú inmediatamente, ejecutar `update-desktop-database ~/.local/share/applications` o reiniciar sesión.
- Validar el archivo con: `desktop-file-validate ~/.local/share/applications/hermes-desktop.desktop`

## Datos de la sesión

- Dashboard + Gateway son procesos independientes. Ambos deben correr.
- **Primer arranque lento**: `hermes dashboard` compila el frontend (Vite/React) en el primer inicio — puede tardar 30-60s en empezar a escuchar en el puerto. Esperar y verificar con `ss -tlnp | grep 9119`.
- El path del ícono dentro del repositorio es `apps/desktop/assets/icon.png`.
- Para redes externas, usar Tailscale (bind a IP tailscale) en vez de exponer a internet.
- El dashboard lee/escribe `.env` — no exponer al internet abierto.
