#!/usr/bin/env python3
"""
🌍 Mundial 2026 — Hermes Agent script
Fuente: https://wheniskickoff.com/data/v1/
Uso: python3 ~/.hermes/scripts/mundial.py [comando] [args]
"""

import sys, os, json
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen

# Importar datos FIFA para eliminatorias
FIFA_DIR = os.path.dirname(os.path.abspath(__file__))
fifa_data = __import__("mundial_fifa")
from mundial_fifa import name_es

BASE = "https://wheniskickoff.com/data/v1"
CACHE_DIR = "/tmp/.mundial-cache"
CACHE_TTL = 300  # 5 min
BRT = timezone(timedelta(hours=-3))

# ── helpers ──────────────────────────────────────────

def _fetch(endpoint):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = f"{CACHE_DIR}/{endpoint.replace('/', '_')}.json"
    now = datetime.now().timestamp()
    if os.path.exists(path) and now - os.path.getmtime(path) < CACHE_TTL:
        with open(path) as f:
            return json.load(f)
    url = f"{BASE}/{endpoint}"
    data = json.loads(urlopen(url, timeout=10).read())
    with open(path, "w") as f:
        json.dump(data, f)
    return data

def load_matches():
    return _fetch("matches.json")["data"]

def load_teams():
    return _fetch("teams.json")["data"]

def load_groups():
    return _fetch("groups.json")["data"]

def flag(code):
    """Get flag emoji for team code from teams cache."""
    teams = load_teams()
    for t in teams:
        if t["code"] == code:
            return t.get("flag", "")
    return ""

def team_name(code):
    teams = load_teams()
    for t in teams:
        if t["code"] == code:
            return name_es(t["name"])
    return code

def format_match(m, show_date=False):
    """Format a single match as Telegram line."""
    f_home = flag(m["home"]) if "home" in m else ""
    f_away = flag(m["away"]) if "away" in m else ""
    
    # Knockout matches use label instead of home_name/away_name
    if "home_name" in m:
        home_n = m["home_name"]
        away_n = m["away_name"]
    elif "label" in m:
        # label = "Winner A vs Runner B" — show the label
        home_n = m["label"]
        away_n = ""
        f_home = ""
        f_away = ""
    else:
        # Fallback: derive from team code
        home_n = team_name(m.get("home", ""))
        away_n = team_name(m.get("away", ""))
    
    if m.get("status") == "FINISHED":
        score = f"**{m['score_home']}-{m['score_away']}**"
        if away_n:
            line = f"{f_home} {home_n} {score} {away_n} {f_away}"
        else:
            line = f"{home_n} — {score}"
    else:
        # Parse time to BRT
        try:
            dt = datetime.fromisoformat(m["datetime_utc"].replace("Z", "+00:00"))
            dt_brt = dt.astimezone(BRT)
            hora = dt_brt.strftime("%H:%M")
        except:
            hora = m["time_utc"]
        if away_n:
            line = f"{f_home} {home_n} vs {away_n} {f_away}  ·  {hora} BRT"
        else:
            line = f"{home_n}  ·  {hora} BRT"
    
    if show_date:
        try:
            dt = datetime.fromisoformat(m["datetime_utc"].replace("Z", "+00:00"))
            dt_brt = dt.astimezone(BRT)
            fecha = dt_brt.strftime("%a %d/%b").replace(".", "")
        except:
            fecha = m["date"]
        line = f"📅 {fecha}  |  {line}"
    return line

# ── comandos ─────────────────────────────────────────

def cmd_hoy():
    """Partidos de hoy (desde FIFA)."""
    from datetime import date
    today_dow = date.today().strftime("%a").lower()
    today_num = date.today().day
    
    # Filter FIFA matches for today
    hoy = []
    for m in fifa_data.LAST_32:
        num, home, sh, sa, away, status, notes = m
        if notes:
            # Parse "Jul 2, 16:00" format
            parts = notes.replace("BRT", "").split(",")[0].strip().lower()
            # Check if day matches
            for part in parts.split():
                if part.isdigit() and int(part) == today_num:
                    hoy.append(m)
                    break
    
    if not hoy:
        # Fallback to API
        today = datetime.now(BRT).strftime("%Y-%m-%d")
        matches = load_matches()
        hoy = [m for m in matches if m["date"] == today]
        if not hoy:
            return "📭 No hay partidos programados para hoy."
        lines = ["⚽ **Partidos de hoy**", ""]
        for m in sorted(hoy, key=lambda x: x.get("time_utc", "")):
            lines.append(format_match(m))
        fin = sum(1 for m in hoy if m.get("status") == "FINISHED")
        if fin:
            lines.append("")
            lines.append(f"✅ {fin}/{len(hoy)} finalizados")
        return "\n".join(lines)
    
    lines = ["⚽ **Partidos de HOY**\n"]
    for m in hoy:
        num, home, sh, sa, away, status, notes = m
        home_es = name_es(home)
        away_es = name_es(away)
        if status == "finished":
            line = f"  ✅ {home_es} **{sh}**-**{sa}** {away_es}"
            if notes and len(notes) > 12: line += f" ({notes})"
        elif status == "live":
            line = f"  🔴 {home_es} vs {away_es} **EN VIVO**"
        else:
            time_part = notes.replace("BRT", "").strip() if notes else ""
            line = f"  ⏳ {home_es} vs {away_es}  ·  {time_part}"
        lines.append(line)
    lines.append("")
    lines.append(f"📊 {sum(1 for m in hoy if m[5]=='finished')}/{len(hoy)} finalizados · "
                 f"{sum(1 for m in hoy if m[5]=='live')} en vivo")
    return "\n".join(lines)

def cmd_ayer():
    """Resultados de ayer."""
    today = datetime.now(BRT)
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    matches = load_matches()
    ayer = [m for m in matches if m["date"] == yesterday and m.get("status") == "FINISHED"]
    
    if not ayer:
        return "📭 No hubo partidos ayer (o no tengo data)."
    
    lines = ["📊 **Resultados de ayer**", ""]
    for m in sorted(ayer, key=lambda x: x.get("time_utc", "")):
        lines.append(format_match(m))
    return "\n".join(lines)

def cmd_grupos(g=None):
    """Tabla de posiciones."""
    matches = load_matches()
    teams = load_teams()
    groups = load_groups()
    
    # Calculate standings from finished matches
    # Pts: win=3, draw=1, loss=0
    standings = {}
    for t in teams:
        standings[t["code"]] = {"pts": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "gd": 0, "name": t["name"], "flag": t.get("flag", "")}
    
    for m in matches:
        if m.get("status") != "FINISHED":
            continue
        h, a = m["home"], m["away"]
        hs, aws = m["score_home"], m["score_away"]
        if hs is None or aws is None:
            continue
        standings[h]["gf"] += hs
        standings[h]["ga"] += aws
        standings[a]["gf"] += aws
        standings[a]["ga"] += hs
        standings[h]["gd"] = standings[h]["gf"] - standings[h]["ga"]
        standings[a]["gd"] = standings[a]["gf"] - standings[a]["ga"]
        if hs > aws:
            standings[h]["pts"] += 3
            standings[h]["w"] += 1
            standings[a]["l"] += 1
        elif hs < aws:
            standings[a]["pts"] += 3
            standings[a]["w"] += 1
            standings[h]["l"] += 1
        else:
            standings[h]["pts"] += 1
            standings[a]["pts"] += 1
            standings[h]["d"] += 1
            standings[a]["d"] += 1
    
    groups_data = groups if groups else []
    if g:
        groups_data = [x for x in groups_data if x["group"] == g.upper()]
    
    lines = []
    for grp in groups_data:
        gl = grp["group"]
        gteams = grp["teams"]
        ranked = sorted(gteams, key=lambda c: (-standings[c]["pts"], -standings[c]["gd"], -standings[c]["gf"]))
        lines.append(f"🏆 **Grupo {gl}**")
        lines.append(f"```")
        lines.append(f"{'':4s} {'PJ':>3} {'G':>3} {'E':>3} {'P':>3} {'GF':>3} {'GC':>3} {'SG':>4} {'PT':>3}")
        for code in ranked:
            s = standings[code]
            pj = s["w"] + s["d"] + s["l"]
            lines.append(f"{s['flag']} {code:<4s} {pj:3d} {s['w']:3d} {s['d']:3d} {s['l']:3d} {s['gf']:3d} {s['ga']:3d} {s['gd']:+4d} {s['pts']:3d}")
        lines.append("```")
        lines.append("")
    
    return "\n".join(lines).strip()

def cmd_equipo(nombre):
    """Partidos de un equipo."""
    matches = load_matches()
    nombre_l = nombre.lower()
    eq_matches = [m for m in matches if nombre_l in m.get("home_name", "").lower() or nombre_l in m.get("away_name", "").lower()]

    if not eq_matches:
        return f"❓ No encontré partidos del equipo '{nombre}'."

    # Get team name from first match that has it
    tname = nombre.title()
    for m in eq_matches:
        if nombre_l in m.get("home_name", "").lower():
            tname = m["home_name"]
            break
        if nombre_l in m.get("away_name", "").lower():
            tname = m["away_name"]
            break

    lines = [f"⚽ **Partidos de {tname}**", ""]
    
    for m in sorted(eq_matches, key=lambda x: x["datetime_utc"]):
        icon = "✅" if m.get("status") == "FINISHED" else "⏳"
        lines.append(f"{icon} {format_match(m, show_date=True)}")
    
    return "\n".join(lines)

def cmd_proximos(n=10):
    """Próximos N partidos."""
    matches = load_matches()
    today = datetime.now(BRT).strftime("%Y-%m-%d")
    upcoming = [m for m in matches if m.get("status") != "FINISHED" and m["date"] >= today]
    upcoming.sort(key=lambda x: x["datetime_utc"])
    
    if not upcoming:
        return "🏆 ¡El mundial terminó!"
    
    lines = ["🔮 **Próximos partidos**", ""]
    for m in upcoming[:n]:
        lines.append(format_match(m, show_date=True))
    return "\n".join(lines)

def cmd_brackets():
    """Diagrama de eliminatorias desde FIFA.com."""
    return fifa_data.format_last32()

def cmd_resumen():
    """Briefing completo del día con datos FIFA."""
    today = datetime.now(BRT)
    today_s = today.strftime("%Y-%m-%d")
    yesterday_s = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    matches = load_matches()
    fifa_last32 = fifa_data.LAST_32
    
    # Partidos de ayer (de la API de grupos)
    ayer = [m for m in matches if m["date"] == yesterday_s and m.get("status") == "FINISHED"]
    
    # Partidos de HOY desde FIFA Last 32
    # Determinar fecha por match_num o por hora
    # Mapa: match_num -> fecha estimada BRT
    # Simplificado: partidos que coinciden con hoy
    today_brt = today.strftime("%d/%b").lower()
    hoy_fifa = []
    for m in fifa_last32:
        num, home, sh, sa, away, status, notes = m
        if notes:
            time_str = notes
            # Check if the match date matches today
            if today_brt in time_str.lower():
                hoy_fifa.append(m)
    
    lines = [f"🌍 **Resumen Mundial — {today.strftime('%d/%b/%Y')}**", ""]
    
    # Ayer (grupos o Last 32)
    yesterday_fifa = [m for m in fifa_last32 if m[5] == "finished" and m[0] <= 81]  # matches 73-81 are Jun 28-Jul 1
    # Filter to yesterday's matches by checking if they were played yesterday
    # Simplification: show all finished Last 32 matches
    if yesterday_fifa:
        fin_last32 = [m for m in fifa_last32 if m[5] == "finished" or m[5] == "live"]
        lines.append("📊 **Resultados Last 32 (eliminatorias)**")
        for m in fin_last32:
            num, home, sh, sa, away, status, notes = m
            home_es = name_es(home)
            away_es = name_es(away)
            if status == "finished":
                line = f"  ✅ {home_es} **{sh}**-**{sa}** {away_es}"
                if notes: line += f" ({notes})"
            else:
                line = f"  🔴 {home_es} vs {away_es} **EN VIVO**"
            lines.append(line)
        lines.append("")
    
    # Partidos de HOY en Last 32
    if hoy_fifa:
        lines.append("⚽ **Partidos de hoy**")
        for m in hoy_fifa:
            num, home, sh, sa, away, status, notes = m
            home_es = name_es(home)
            away_es = name_es(away)
            if status == "upcoming":
                time_part = notes.replace("BRT", "").strip() if notes else ""
                lines.append(f"  {home_es} vs {away_es}  ·  {time_part}")
        lines.append("")
    
    # Proximos destacados
    upcoming = [m for m in fifa_last32 if m[5] == "upcoming"]
    if upcoming:
        lines.append("🔮 **Próximos partidos Last 32**")
        for m in upcoming:
            num, home, sh, sa, away, status, notes = m
            home_es = name_es(home)
            away_es = name_es(away)
            time_part = notes.replace("BRT", "").strip() if notes else ""
            lines.append(f"  {home_es} vs {away_es}  ·  {time_part}")
        lines.append("")
    
    # Grupos: líderes
    lines.append("🏆 **Líderes de grupo**")
    for g, teams in sorted(fifa_data.GROUPS_FINAL.items()):
        winner = name_es(teams[0][0])
        runner = name_es(teams[1][0])
        lines.append(f"  Grupo {g}: {winner}, {runner}")
    
    return "\n".join(lines)

# ── main ─────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        print("""🌍 Mundial 2026 — Comandos:
  hoy             Partidos de hoy
  ayer            Resultados de ayer
  grupos [letra]  Tabla de posiciones (ej: grupos A, grupos)
  equipo <nom>    Partidos de un equipo (ej: equipo Argentina)
  proximos [N]    Próximos N partidos (default 10)
  brackets        Diagrama de eliminatorias
  resumen         Briefing completo del día""")
    elif args[0] == "hoy":
        print(cmd_hoy())
    elif args[0] == "ayer":
        print(cmd_ayer())
    elif args[0] == "grupos":
        print(cmd_grupos(args[1] if len(args) > 1 else None))
    elif args[0] in ("equipo", "eq"):
        print(cmd_equipo(" ".join(args[1:])))
    elif args[0] == "proximos":
        n = int(args[1]) if len(args) > 1 and args[1].isdigit() else 10
        print(cmd_proximos(n))
    elif args[0] == "brackets":
        print(cmd_brackets())
    elif args[0] == "resumen":
        print(cmd_resumen())
    else:
        print(f"❓ Comando desconocido: {args[0]}")
