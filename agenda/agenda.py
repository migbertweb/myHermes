#!/usr/bin/env python3
"""
Agenda — sistema de tareas diarias.
SQLite persistente + HTTP API para widget Quickshell + CLI.

Modos de uso:
  python3 agenda.py add "titulo" 10:00                  # crear tarea
  python3 agenda.py today                                # tareas de hoy
  python3 agenda.py list                                 # todas pendientes
  python3 agenda.py done <id>                            # completar
  python3 agenda.py move <id> HH:MM                      # reprogramar
  python3 agenda.py delete <id>                          # eliminar
  python3 agenda.py api                                  # servidor HTTP
  python3 agenda.py notify                               # notificaciones pendientes
"""

import sqlite3
import sys
import os
import json
import time
from datetime import datetime, date
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "tasks.db")
API_PORT = 9120

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    done INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    notified INTEGER DEFAULT 0
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def today_str():
    return date.today().isoformat()


# ─── CRUD ────────────────────────────────────────────────────────

def add(title, time_str, priority=0, notes="", date_str=None):
    d = date_str or today_str()
    conn = get_db()
    conn.execute(
        "INSERT INTO tasks (title, date, time, priority, notes) VALUES (?, ?, ?, ?, ?)",
        (title, d, time_str, priority, notes),
    )
    conn.commit()
    tid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"✔ Tarea #{tid} creada: {title} — {d} {time_str}")
    return tid


def list_tasks(date_str=None, only_done=None):
    conn = get_db()
    d = date_str or today_str()
    q = "SELECT * FROM tasks WHERE date = ?"
    params = [d]
    if only_done is not None:
        q += " AND done = ?"
        params.append(1 if only_done else 0)
    q += " ORDER BY time ASC, priority DESC, id ASC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def show_today():
    rows = list_tasks()
    if not rows:
        print(f"📭 Sin tareas para hoy ({today_str()})")
        return
    print(f"📋 Agenda — {today_str()}\n")
    for t in rows:
        status = "✅" if t["done"] else "⬜"
        prio = " 🔴" if t["priority"] >= 2 else " 🟡" if t["priority"] >= 1 else ""
        print(f"  {status} #{t['id']:02d} {t['time']}  {t['title']}{prio}")


def done(task_id):
    conn = get_db()
    c = conn.execute("UPDATE tasks SET done = 1 WHERE id = ? AND done = 0", (task_id,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    if affected:
        print(f"✅ Tarea #{task_id} completada")
    else:
        print(f"⚠ Tarea #{task_id} no encontrada o ya completada")


def move(task_id, new_time):
    conn = get_db()
    c = conn.execute("UPDATE tasks SET time = ?, notified = 0 WHERE id = ?", (new_time, task_id))
    conn.commit()
    affected = c.rowcount
    conn.close()
    if affected:
        print(f"🔄 Tarea #{task_id} reprogramada para {new_time}")
    else:
        print(f"⚠ Tarea #{task_id} no encontrada")


def delete(task_id):
    conn = get_db()
    c = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    if affected:
        print(f"🗑 Tarea #{task_id} eliminada")
    else:
        print(f"⚠ Tarea #{task_id} no encontrada")


# ─── Notificaciones ───────────────────────────────────────────────

def check_notifications():
    """Busca tareas de hoy cuya hora esté a ~15 min, no notificadas."""
    now = datetime.now()
    today = today_str()
    notify_window = 15  # minutos

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE date = ? AND done = 0 AND notified = 0",
        (today,),
    ).fetchall()

    pending = []
    for t in rows:
        try:
            t_dt = datetime.strptime(f"{t['date']} {t['time']}", "%Y-%m-%d %H:%M")
            diff_min = (t_dt - now).total_seconds() / 60
            if 0 <= diff_min <= notify_window:
                pending.append(dict(t))
        except ValueError:
            continue

    if pending:
        for t in pending:
            conn.execute("UPDATE tasks SET notified = 1 WHERE id = ?", (t["id"],))
        conn.commit()
        conn.close()
        # Salida JSON para que el cronjob la procese
        print(json.dumps({"notify": pending, "count": len(pending)}))
        return True

    conn.close()
    return False


def reset_notifications():
    """Reabre notificaciones para tareas no completadas (útil si se cambia el horario)."""
    conn = get_db()
    conn.execute("UPDATE tasks SET notified = 0 WHERE done = 0")
    conn.commit()
    conn.close()
    print("♻ Notificaciones reseteadas")


# ─── HTTP API ─────────────────────────────────────────────────────

class AgendaAPI(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def _html(self, text, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(text.encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        try:
            if path == "/api/today":
                rows = list_tasks()
                self._json({"date": today_str(), "tasks": rows})

            elif path == "/api/next":
                rows = list_tasks(only_done=False)
                if rows:
                    self._json({"next": rows[0], "total_pending": len(rows)})
                else:
                    self._json({"next": None, "total_pending": 0})

            elif path == "/api/tasks":
                d = params.get("date", [today_str()])[0]
                rows = list_tasks(date_str=d)
                self._json({"date": d, "tasks": rows})

            elif path == "/api/stats":
                conn = get_db()
                total = conn.execute("SELECT COUNT(*) FROM tasks WHERE date = ?", (today_str(),)).fetchone()[0]
                done_c = conn.execute("SELECT COUNT(*) FROM tasks WHERE date = ? AND done = 1", (today_str(),)).fetchone()[0]
                conn.close()
                self._json({"date": today_str(), "total": total, "completed": done_c, "pending": total - done_c})

            elif path.startswith("/api/tasks/"):
                parts = path.split("/")
                if len(parts) == 4 and parts[3].isdigit():
                    conn = get_db()
                    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (parts[3],)).fetchone()
                    conn.close()
                    if row:
                        self._json(dict(row))
                    else:
                        self._json({"error": "not found"}, 404)
                else:
                    self._json({"error": "invalid path"}, 404)

            elif path == "/health":
                self._html("ok")

            else:
                self._json({"error": "not found", "endpoints": ["/api/today", "/api/next", "/api/tasks", "/api/tasks/<id>", "/api/stats", "/health"]}, 404)

        except Exception as e:
            self._json({"error": str(e)}, 500)

    def do_PATCH(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            if path.startswith("/api/tasks/") and path.endswith("/done"):
                parts = path.split("/")
                if len(parts) == 5 and parts[3].isdigit():
                    done(parts[3])
                    self._json({"ok": True, "id": int(parts[3]), "status": "completed"})
                else:
                    self._json({"error": "invalid path"}, 404)
            elif path.startswith("/api/tasks/") and path.endswith("/move"):
                parts = path.split("/")
                if len(parts) == 5 and parts[3].isdigit():
                    content_len = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(content_len)) if content_len else {}
                    new_time = body.get("time")
                    if new_time:
                        move(parts[3], new_time)
                        self._json({"ok": True, "id": int(parts[3]), "new_time": new_time})
                    else:
                        self._json({"error": "time required"}, 400)
                else:
                    self._json({"error": "invalid path"}, 404)
            else:
                self._json({"error": "not found"}, 404)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # silencioso


def run_api():
    server = HTTPServer(("0.0.0.0", API_PORT), AgendaAPI)
    print(f"🌐 Agenda API corriendo en http://0.0.0.0:{API_PORT}")
    print(f"   Endpoints: /api/today  /api/next  /api/tasks  /api/stats  /health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹ API detenida")
        server.server_close()


# ─── CLI ──────────────────────────────────────────────────────────

def usage():
    print("Uso:")
    print("  agenda.py add <titulo> <HH:MM> [--priority 0|1|2]")
    print("  agenda.py today")
    print("  agenda.py list [--date YYYY-MM-DD]")
    print("  agenda.py done <id>")
    print("  agenda.py move <id> <HH:MM>")
    print("  agenda.py delete <id>")
    print("  agenda.py notify")
    print("  agenda.py reset-notifications")
    print("  agenda.py api")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "add" and len(sys.argv) >= 4:
        title = sys.argv[2]
        time_str = sys.argv[3]
        priority = 0
        notes = ""
        date_str = None
        i = 4
        while i < len(sys.argv):
            if sys.argv[i] == "--priority" and i + 1 < len(sys.argv):
                priority = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--date" and i + 1 < len(sys.argv):
                date_str = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--notes" and i + 1 < len(sys.argv):
                notes = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        add(title, time_str, priority, notes, date_str)

    elif cmd == "today":
        show_today()

    elif cmd == "list":
        date_str = None
        if "--date" in sys.argv:
            idx = sys.argv.index("--date")
            if idx + 1 < len(sys.argv):
                date_str = sys.argv[idx + 1]
        rows = list_tasks(date_str=date_str)
        if rows:
            d = date_str or today_str()
            print(f"📋 Tareas — {d}")
            for t in rows:
                status = "✅" if t["done"] else "⬜"
                print(f"  {status} #{t['id']:02d} {t['time']}  {t['title']}")
        else:
            print("📭 Sin tareas")

    elif cmd == "done" and len(sys.argv) >= 3:
        done(int(sys.argv[2]))

    elif cmd == "move" and len(sys.argv) >= 4:
        move(int(sys.argv[2]), sys.argv[3])

    elif cmd == "delete" and len(sys.argv) >= 3:
        delete(int(sys.argv[2]))

    elif cmd == "notify":
        check_notifications()

    elif cmd == "reset-notifications":
        reset_notifications()

    elif cmd == "api":
        run_api()

    else:
        usage()
        sys.exit(1)
