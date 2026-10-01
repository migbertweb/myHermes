# Reorg Addendum 2026-08-16 (deltas sobre media-library-reorganization.md)

Complementa `media-library-reorganization.md` (convención KODI + procedimiento seguro).
Tres adiciones verificadas en la reorg masiva del 2026-08-16 (57 pelis + 4 series):

## 1. Verificación masiva de títulos en TMDB (batch)
Antes de renombrar ~20+ títulos ambiguos, verifícalos en lote con execute_code en UNA llamada:
```python
from hermes_tools import web_search
import time
for q in ["72 horas pelicula 2026", "Asesino a sueldo pelicula 2006", ...]:
    r = web_search(q, limit=2)
    print("###", q, "|", "; ".join(x.get('title','') for x in r["data"]["web"][:2]))
    time.sleep(0.3)
```
Ejemplos resueltos así: `Asesino a sueldo (2006)` = Lucky Number Slevin,
`La emboscada (1999)` = Entrapment, `Scary Movie: Terroríficamente incorrecta (2026)` =
Scary Movie 6, `Un día descabellado (2015)` = Bad Hair Day (Disney Channel).

## 2. Watcher scripts con IDs stale
`~/multimedia/series/elle_watcher.sh` apuntaba a torrent IDs 52-59 que se habían
desplazado con la cola — script muerto (borrado con su .log). Regla: antes de confiar o
conservar cualquier `*_watcher.sh`/cron helper dentro de `multimedia/`, verifica que sus
IDs sigan correspondiendo en `transmission-remote -l`.

## 3. Scan de librería
KODI (no Jellyfin) detecta las carpetas nuevas en su próximo scan; forzar con
"Scan for new content" o `kodi-send` si el usuario lo quiere inmediato.

## 4. Harness reutilizable
`scripts/reorg_safe.py` (mismo skill) implementa el patrón seguro completo:
rutas absolutas, move → verificar destino → limpiar, progreso por ítem con flush,
sweep de torrents muertos. Rellenar MOVES y correr: `ssh serverhogar 'python3 -' < reorg_safe.py`.
