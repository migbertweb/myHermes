# Renombrado de series a convención KODI (serverhogar)

## Convención

- Carpeta por serie: `Título (Año)/` — año = estreno de la serie en TMDB, NO de la temporada.
- Episodios: `Título (Año) - SxxExx - RES FUENTE Lang.EXT`
  - `Reacher (2022) - S04E01 - 720p WEB-DL Dual-Lat.mp4`
  - `Lanterns (2026) - S01E01 - 720p WEB-DL Dual-Lat.mp4`
  - `Stuart no logra salvar el universo (2026) - S01E05 - 720p WEB-DL Dual-Lat.mp4`

## Regla de oro: no fabricar etiquetas

Probar el archivo ANTES de nombrar (resolución real + idiomas de audio):

```bash
# Inspección local previa a la transferencia:
ffprobe -v error -select_streams v:0 -show_entries stream=height,codec_name -of csv=p=0 "archivo.mp4"
ffprobe -v error -select_streams a -show_entries stream_tags=language -of csv=p=0 "archivo.mp4"

# Inspección remota en servidor:
ssh serverhogar 'for f in ~/multimedia/series/CARPETA/*.mp4; do echo "== $f"; ffprobe -v error -select_streams v:0 -show_entries stream=height,codec_name -of csv=p=0 "$f"; ffprobe -v error -select_streams a -show_entries stream_tags=language -of csv=p=0 "$f"; done'
```

- `h264,720` → etiqueta `720p` (nunca asumir 1080p).
- Idiomas de todas las pistas: `spa,eng` → `Dual-Lat`. Si hay pistas extra (`spa,spa,eng,por`), se mantiene `Dual-Lat` pero anotar la extra al usuario.
- Mantener la extensión real: `.mp4` queda `.mp4`. La convención escrita dice `.mkv`, pero NO se renombra el contenedor — sería una mentira técnica.

## Ejemplos reales

### 2026-08-18
| Origen (laptop) | Destino (server) |
|---|---|
| `reacher/Reacher-S04E01.mp4` | `Reacher (2022)/Reacher (2022) - S04E01 - 720p WEB-DL Dual-Lat.mp4` |
| `reacher/Reacher-S04E02.mp4` | `Reacher (2022) - S04E02 - 720p WEB-DL Dual-Lat.mp4` |
| `reacher/Reacher-S04E03.mp4` | `Reacher (2022) - S04E03 - 720p WEB-DL Dual-Lat.mp4` |
| `Lanterns/Linternas-S01E01.mp4` | `Lanterns (2026)/Lanterns (2026) - S01E01 - 720p WEB-DL Dual-Lat.mp4` |

### 2026-08-29
| Origen (laptop) | Destino (server) |
|---|---|
| `Reacher 4x5.mp4` | `Reacher (2022)/Reacher (2022) - S04E05 - 720p WEB-DL Dual-Lat.mp4` |
| `stuart/Stuart no consigue salvar el Universo 1x5.mp4` | `Stuart no logra salvar el universo (2026)/Stuart no logra salvar el universo (2026) - S01E05 - 720p WEB-DL Dual-Lat.mp4` |
| `stuart/Stuart no consigue salvar el Universo 1x6.mp4` | `Stuart no logra salvar el universo (2026)/Stuart no logra salvar el universo (2026) - S01E06 - 720p WEB-DL Dual-Lat.mp4` |

Comandos usados (paréntesis siempre entre comillas dobles):

```bash
# Transferencia directa con renombrado via rsync
rsync -av --progress "/home/migbert/Escritorio/stuart/Stuart no consigue salvar el Universo 1x5.mp4" "serverhogar:/home/piro/multimedia/series/Stuart no logra salvar el universo (2026)/Stuart no logra salvar el universo (2026) - S01E05 - 720p WEB-DL Dual-Lat.mp4"
```

## Pitfall de quoting SSH

`~` NO expande dentro de comillas dobles en el shell remoto:

```bash
# FALLA — "~" queda literal, "No such file or directory"
ssh serverhogar 'ls "~/multimedia/series/Reacher (2022)"'

# OK — ruta completa, o tilde sin comillas
ssh serverhogar 'ls /home/piro/multimedia/series/Reacher\ \(2022\)/'
```

## Cómo elegir el año (TMDB)

- Reacher: estreno 2022-02 → carpeta `Reacher (2022)`, aunque S04 sea de 2026.
- Lanterns: estreno 2026 → `Lanterns (2026)`.
- Stuart no logra salvar el universo: estreno 2026 → `Stuart no logra salvar el universo (2026)`.
- Coherente con la biblioteca existente: `Elle (2026)`, `X-Men '97 (2024)`, `La Casa del Dragon` (sin año, inconsistencia heredada).
