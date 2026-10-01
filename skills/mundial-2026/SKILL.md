---
name: mundial-2026
description: Consulta datos del Mundial FIFA 2026 en tiempo real. Partidos, resultados, posiciones, brackets, equipos. Cron diario con resumen.
platforms: [linux]
scripts:
  - mundial.py: Script principal con funciones de consulta y formateo
  - daily_briefing.py: Script para el cron diario (no_agent=true)
---

# 🌍 Mundial 2026 — Guía de uso

## APIs

Fuente: `https://wheniskickoff.com/data/v1/`

| Endpoint | Descripción |
|---|---|
| `/matches.json` | 104 partidos: fecha, equipos, scores, venue, fase |
| `/teams.json` | 48 equipos: código, nombre, bandera, grupo, ranking FIFA |
| `/groups.json` | 12 grupos: letra + códigos de equipos |

Sin API key, CORS habilitado, actualizado en vivo.

## Comandos disponibles

| Comando | Output |
|---|---|
| `/mundial` | Resumen general del día actual |
| `/mundial hoy` | Partidos de HOY (hora BRT) |
| `/mundial ayer` | Resultados de ayer |
| `/mundial grupos` | Tabla de posiciones TODOS los grupos |
| `/mundial grupo A` | Tabla del grupo específico |
| `/mundial eq Argentina` | Partidos de Argentina |
| `/mundial proximos` | Próximos 10 partidos |
| `/mundial brackets` | Diagrama de eliminatorias |
| `/mundial resumen` | Briefing completo del día (como el cron) |

## Formatos

- **Horas:** siempre en BRT (UTC-3)
- **Idioma:** español latino neutro
- **Banderas:** emoji flags antes del nombre del equipo
- **Scores:** `🏴 Argentina 2-1 Nigeria 🇳🇬`

## Scripts

Los scripts viven en `~/.hermes/scripts/` — el cron los llama con `no_agent=True`.

Para invocar desde el agente:

```python
from hermes_tools import terminal
result = terminal("python3 ~/.hermes/scripts/mundial.py --hoy")
```

## Pitfalls

- La API no tiene scores en vivo (solo FINISHED o None). Para partidos EN VIVO no hay data streaming.
- `status=None` significa "no ha empezado aún" (puede ser UPCOMING o LIVE sin scores todavía)
- Las fechas están en UTC. El script convierte a BRT.
- Los grupos 1-12 se llaman A-L (12 grupos × 4 equipos = 48)
- Fase eliminatoria: octavos (28 jun - 3 jul), cuartos (4-7 jul), semis (8-11 jul), final (19 jul)
