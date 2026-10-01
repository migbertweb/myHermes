---
name: youtube-playlist-download
description: Use when downloading YouTube playlists as MP3 with yt-dlp.
---

# Descarga de playlists de YouTube → MP3

Baja playlists de YouTube como MP3 con **yt-dlp** + **ffmpeg**, usando un script
Python parametrizado por `config.json`. Reutilizable para cualquier carpeta de
música del usuario.

## Instalaciones existentes

| Carpeta | Playlists | Script |
|---------|-----------|--------|
| `~/Música/fiestaMigy/` | reggaeton mix, Reggaeton2025 | `descargar_playlists.py` |
| `~/Música/romantica/` | romanticas en español, charlie zaa y amigos | mismo patrón (config.json + main.py viejo en playlistPlubica) |

## Cómo obtener los IDs de playlist (MCP YouTube)

Usar las tools MCP `youtube-mcp`:

1. `mcp__youtube_mcp__list_playlists` → devuelve JSON con `playlistId`, `title`, `itemCount`.
2. Buscar el título exacto y copiar el `playlistId`.
3. Añadir al `config.json` del script con URL `https://www.youtube.com/playlist?list=<ID>`.

## Pasos para descargar

1. Verificar deps: `which yt-dlp ffmpeg ffprobe`.
2. Crear carpeta destino con `logs/` y copiar `cookies.txt` desde una instalación previa
   (ej. `cp ~/Música/romantica/cookies.txt ~/Música/<nueva>/cookies.txt`) — necesarias
   para playlists privadas o con restricción de edad.
3. Escribir `config.json` con el esquema del script:
   - `nombre` (informativo), `playlist_url`, `playlist_id`, `carpeta_destino`
     (relativa al script), `max_canciones`, `prioridad` (orden).
4. Escribir `descargar_playlists.py` (ver plantilla en `scripts/descargar_playlists.py`)
   y `README.md`.
5. Probar con `python3 descargar_playlists.py --lista`.
6. Ejecutar: foreground si son pocas; `terminal(background=true, notify_on_complete=true)`
   para 30+ videos.

## Flags yt-dlp clave

- `-f bestaudio/best -x --audio-format mp3 --audio-quality 0` → MP3 de máxima calidad.
- `--embed-metadata --embed-thumbnail --add-metadata` → tags ID3 + carátula.
- `-o "<dest>/%(playlist_index)03d - %(title)s.%(ext)s"` → numeración por orden de playlist.
- `--download-archive <dir>/.archive.txt` → solo baja videos nuevos en corridas futuras.
- `--playlist-items 1:<max>` → límite por playlist.
- `--ignore-errors --no-overwrites --newline` → resiliencia en corridas largas.
- `--cookies cookies.txt` solo si existe.

## Pitfalls

- **`--download-archive` es GLOBAL entre playlists** (mismo `.archive.txt`): si dos
  playlists comparten un video, la segunda corrida lo salta ("already been recorded")
  y la carpeta queda incompleta. Fix: copiar el mp3 ya existente a la carpeta faltante
  (`cp <playlist1>/<idx> - <title>.mp3 <playlist2>/<idx> - <title>.mp3`), o usar un
  archive por playlist si se quieren duplicados.
- **Playlists privadas**: el MCP youtube-mcp las lista (cuenta autenticada) pero
  yt-dlp falla con "The playlist does not exist" si las cookies no autentican la
  sesión. Fix: pedir al usuario que la haga pública o exportar cookies frescas
  (Get cookies.txt). Verificar con
  `yt-dlp --cookies cookies.txt --flat-playlist --print "%(id)s | %(title)s" "https://www.youtube.com/@MigbertYanez/playlists" | grep -i "<nombre>"`.
- **Video individual sin índice de playlist** → nombre con "NA". Fix: renombrar
  `NA - <title>.mp3` → `<idx> - <title>.mp3` después de descargar.
- `--ignore-errors` traga fallos individuales: verificar al final con
  `find <dest> -name "*.mp3" | wc -l` vs `itemCount`; re-ejecutar el comando
  (el archive marca lo ya bajado y muestra solo lo que falta).
- Videos con `｜` u otros chars en título: yt-dlp los sanea solo en el nombre de archivo; no problem.
- Si una playlist es privada y falla con "Sign in to confirm you're not a bot":
  renovar `cookies.txt` (exportar de nuevo con el navegador logueado).
- Formato de salida termina en `.webm` si ffmpeg no está → verificar `which ffmpeg` antes.

## Verificación

- `process(action=wait)` o revisar `logs/descarga_*.log`.
- Contar archivos: `ls <dest>/*.mp3 | wc -l` vs `itemCount` de la playlist del MCP.
