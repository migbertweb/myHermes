---
name: agenda
description: >-
  Sistema de agenda y tareas diarias con persistencia SQLite, notificaciones
  Telegram (cron 15 min antes) y widget Quickshell para Hyprland/CachyOS.
  Gestionado via Telegram conmigo (Hermes), visible en la laptop.
domain: productivity
triggers:
  - "agenda agrega|tarea|crea|nueva"
  - "agenda hoy|hoy|dia|daily"
  - "agenda mueve|reagenda|reprograma"
  - "agenda completa|hecho|terminado|done"
  - "agenda lista|todas|pendientes"
---

# Agenda — Sistema de Tareas Diarias

## Arquitectura

```
SERVER (Hermes, 192.168.1.8)
├── tasks.db (SQLite) — persistencia central
├── Lógica CRUD gestionada por Hermes en Telegram
├── Cronjob: notificación 15 min antes de cada tarea → Telegram
└── API HTTP liviana (Express) ──→ LAPTOP

LAPTOP (CachyOS, Hyprland, Quickshell)
└── Widget QML ←─ fetch API → próxima tarea visible en escritorio
```

## Stack

- **DB**: SQLite (`~/.hermes/agenda/tasks.db`)
- **Backend**: Python stdlib (`http.server` + `sqlite3`) — sin dependencias externas
- **API**: Puerto 9120, systemd user service (`agenda-api.service`)
- **Notificaciones**: Cronjob Hermes cada 2 min (`no_agent=True`) con script `~/.hermes/scripts/agenda-check-notify.py`
- **Widget**: Quickshell QML que consume API REST
- **Delivery**: Telegram (notificaciones + comandos)

## Schema SQLite

```sql
CREATE TABLE tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  date TEXT NOT NULL,          -- 'YYYY-MM-DD'
  time TEXT NOT NULL,          -- 'HH:MM'
  done INTEGER DEFAULT 0,      -- 0=pendiente, 1=completada
  priority INTEGER DEFAULT 0,  -- 0=normal, 1=alta, 2=urgente
  notes TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now')),
  notified INTEGER DEFAULT 0   -- 0=no notificado, 1=ya notificado
);
```

## Comandos Telegram (Hermes)

### Crear tarea
> agenda agrega <título> <HH:MM>
> agenda nueva revisar servidor 10:00
> agenda tarea comprar pan 15:30 alta

### Ver día
> agenda hoy
> agenda 2026-07-25

### Reprogramar
> agenda mueve <id> <HH:MM>
> agenda mueve 3 14:00

### Completar
> agenda completa <id>
> agenda hecho 3

### Listar pendientes
> agenda lista
> agenda todas

### Eliminar
> agenda borra <id>

## Cron de Notificaciones

Cronjob que corre cada 1-2 minutos en Hermes:
- Lee `tasks.db` donde `date=today AND done=0 AND notified=0`
- Calcula si faltan ~15 min para cada tarea (`time - now ≈ 15 min`)
- Envía notificación a Telegram: `"⏰ <título> arranca en 15 min"`
- Marca `notified=1`

## Widget Quickshell (laptop)

Widget QML que:
- Hace GET a `http://192.168.1.8:<puerto>/api/today`
- Muestra próxima tarea + siguientes 2 pendientes
- Se actualiza cada 30s
- Diseño oscuro, mínimo, que pegue con Hyprland

### API endpoints

| Método | Ruta | Respuesta |
|--------|------|-----------|
| GET | `/api/today` | Tareas del día (pendientes primero) |
| GET | `/api/next` | Próxima tarea no completada |
| GET | `/api/tasks` | Tareas por fecha (`?date=YYYY-MM-DD`) |
| GET | `/api/tasks/<id>` | Tarea específica |
| GET | `/api/stats` | Estadísticas del día |
| PATCH | `/api/tasks/<id>/done` | Marcar completada |
| PATCH | `/api/tasks/<id>/move` | Reprogramar (body: `{"time": "HH:MM"}`) |
| GET | `/health` | Healthcheck |

## Implementación

### Server (192.168.1.8)

**Script principal:** `~/.hermes/agenda/agenda.py`
- CRUD completo (add, list, done, move, delete)
- API HTTP en puerto 9120 (Python stdlib, sin dependencias)
- Notificaciones: `python3 agenda.py notify`

**Servicio systemd:** `~/.config/systemd/user/agenda-api.service`
- `systemctl --user start/stop/restart agenda-api.service`
- Arranca sola al iniciar sesión

**Cron de notificaciones:** `agenda-check-notify.py` en `~/.hermes/scripts/`
- Corre cada 2 min (`no_agent=True`) via cronjob Hermes
- Detecta tareas a 15 min de su hora, envía notificación Telegram
- Silenciosa si no hay tareas que notificar

### Widget Quickshell (laptop — pendiente)

Widget QML que:
- Hace GET a `http://192.168.1.8:9120/api/today`
- Muestra próxima tarea + siguientes 2 pendientes
- Se actualiza cada 30s
- Diseño oscuro, mínimo, que pegue con Hyprland
