#!/usr/bin/env python3
"""
🌍 Mundial 2026 — Datos de eliminatorias desde FIFA.com
Fuente: https://www.fifa.com/pt/tournaments/mens/worldcup/canadamexicousa2026
Extraído por browser tool. Última actualización: 2026-07-01 23:15 BRT
"""

# ── Traducción de nombres a español ─────────────────────────
TEAM_ES = {
    # Last 32 / Eliminatorias
    "South Africa": "Sudáfrica",
    "Canada": "Canadá",
    "Belgium": "Bélgica",
    "Senegal": "Senegal",
    "England": "Inglaterra",
    "Congo DR": "R. D. Congo",
    "Mexico": "México",
    "Ecuador": "Ecuador",
    "France": "Francia",
    "Sweden": "Suecia",
    "Ivory Coast": "Costa de Marfil",
    "Norway": "Noruega",
    "Netherlands": "Países Bajos",
    "Morocco": "Marruecos",
    "Germany": "Alemania",
    "Paraguay": "Paraguay",
    "Brazil": "Brasil",
    "Japan": "Japón",
    "USA": "EE. UU.",
    "Bosnia-Herzegovina": "Bosnia y Herzegovina",
    "Spain": "España",
    "Austria": "Austria",
    "Portugal": "Portugal",
    "Croatia": "Croacia",
    "Switzerland": "Suiza",
    "Algeria": "Argelia",
    "Australia": "Australia",
    "Egypt": "Egipto",
    "Argentina": "Argentina",
    "Cape Verde Islands": "Cabo Verde",
    "Colombia": "Colombia",
    "Ghana": "Ghana",
    # Grupos adicionales
    "South Korea": "Corea del Sur",
    "Czechia": "República Checa",
    "Qatar": "Catar",
    "Scotland": "Escocia",
    "Haiti": "Haití",
    "United States": "Estados Unidos",
    "Turkey": "Turquía",
    "Curaçao": "Curazao",
    "Tunisia": "Túnez",
    "Iran": "Irán",
    "New Zealand": "Nueva Zelanda",
    "Uruguay": "Uruguay",
    "Saudi Arabia": "Arabia Saudita",
    "Iraq": "Irak",
    "Jordan": "Jordania",
    "Uzbekistan": "Uzbekistán",
    "Panama": "Panamá",
}

def name_es(name_en):
    """Traduce nombre de equipo a español. Si no está en el mapa, devuelve el original."""
    return TEAM_ES.get(name_en, name_en)

# Last 32 — emparejamientos extraídos del carrusel de FIFA.com
LAST_32 = [
    # (match_num, home, score_h, score_a, away, status, notes)
    # Status: "finished", "live", "upcoming"
    (73, "South Africa", 0, 1, "Canada", "finished", "Jun 28"),
    (74, "Belgium", 3, 2, "Senegal", "finished", "Jun 28"),
    (75, "England", 2, 1, "Congo DR", "finished", "Jun 28"),
    (76, "Mexico", 2, 0, "Ecuador", "finished", "Jul 1"),
    (77, "France", 3, 0, "Sweden", "finished", "Jul 1"),
    (78, "Ivory Coast", 1, 2, "Norway", "finished", "Jul 1"),
    (79, "Netherlands", 2, 2, "Morocco", "finished", "Morocco won 3-2 on penalties"),
    (80, "Germany", 3, 3, "Paraguay", "finished", "Jul 1, Paraguay won 4-3 on penalties"),
    (81, "Brazil", 2, 1, "Japan", "finished", "Jul 1"),
    (82, "USA", None, None, "Bosnia-Herzegovina", "live", "Jul 1, Em andamento"),
    # Los siguientes aún no se han jugado (horario BRT):
    (83, "Spain", None, None, "Austria", "upcoming", "Jul 2, 16:00 BRT"),
    (84, "Portugal", None, None, "Croatia", "upcoming", "Jul 2, 20:00 BRT"),
    (85, "Switzerland", None, None, "Algeria", "upcoming", "Jul 3, 00:00 BRT"),
    (86, "Australia", None, None, "Egypt", "upcoming", "Jul 3, 15:00 BRT"),
    (87, "Argentina", None, None, "Cape Verde Islands", "upcoming", "Jul 3, 19:00 BRT"),
    (88, "Colombia", None, None, "Ghana", "upcoming", "Jul 3, 22:30 BRT"),
]

# Equipos clasificados (confirmados por grupos y Last 32)
# Grupos con posiciones finales basadas en datos de wheniskickoff + FIFA
GROUPS_FINAL = {
    "A": [("Mexico", 9, +6), ("South Africa", 4, -1), ("South Korea", 3, -1), ("Czechia", 1, -4)],
    "B": [("Switzerland", 7, +4), ("Canada", 4, +5), ("Bosnia-Herzegovina", 4, -1), ("Qatar", 1, -8)],
    "C": [("Brazil", 7, +6), ("Morocco", 7, +3), ("Scotland", 3, -3), ("Haiti", 0, -6)],
    "D": [("United States", 6, +4), ("Australia", 4, 0), ("Paraguay", 4, -2), ("Turkey", 3, -2)],
    "E": [("Germany", 6, +6), ("Ivory Coast", 6, +2), ("Ecuador", 4, 0), ("Curaçao", 1, -8)],
    "F": [("Netherlands", 7, +6), ("Japan", 5, +4), ("Sweden", 4, 0), ("Tunisia", 0, -10)],
    "G": [("Belgium", 5, +4), ("Egypt", 5, +2), ("Iran", 3, 0), ("New Zealand", 1, -6)],
    "H": [("Spain", 7, +5), ("Cape Verde Islands", 3, 0), ("Uruguay", 2, -1), ("Saudi Arabia", 2, -4)],
    "I": [("France", 9, +8), ("Norway", 6, +1), ("Senegal", 3, +2), ("Iraq", 0, -11)],
    "J": [("Argentina", 6, +5), ("Austria", 3, 0), ("Algeria", 3, -2), ("Jordan", 0, -3)],
    "K": [("Colombia", 6, +3), ("Portugal", 4, +5), ("Congo DR", 1, -1), ("Uzbekistan", 0, -7)],
    "L": [("England", 4, +2), ("Ghana", 4, +1), ("Croatia", 3, -1), ("Panama", 0, -2)],
}

# Mejores 8 terceros lugares
TOP_THIRD = [
    ("Sweden", "F", 4, 0),
    ("Ecuador", "E", 4, 0),
    ("Bosnia-Herzegovina", "B", 4, -1),
    ("Paraguay", "D", 4, -2),
    ("Senegal", "I", 3, +2),
    ("Iran", "G", 3, 0),
    ("Croatia", "L", 3, -1),
    ("South Korea", "A", 3, -1),
]

def format_last32():
    """Formatea la Last 32 completa en español."""
    lines = ["🏆 **LAST 32 — Resultados**\n"]
    for m in LAST_32:
        num, home, sh, sa, away, status, notes = m
        home_es = name_es(home)
        away_es = name_es(away)
        if status == "finished":
            line = f"  ✅ {home_es} **{sh}**-**{sa}** {away_es}"
            if notes:
                line += f" ({notes})"
        elif status == "live":
            line = f"  🔴 {home_es} vs {away_es} **🔴 EN VIVO**"
        else:
            # upcoming
            line = f"  ⏳ {home_es} vs {away_es}"
            if notes:
                time_part = notes.replace("BRT", "").strip()
                line += f"  ·  {time_part}"
        lines.append(line)
    lines.append("")
    lines.append(f"📊 {sum(1 for m in LAST_32 if m[5]=='finished')}/16 finalizados · "
                 f"{sum(1 for m in LAST_32 if m[5]=='live')} en vivo · "
                 f"{sum(1 for m in LAST_32 if m[5]=='upcoming')} pendientes")
    return "\n".join(lines)

if __name__ == "__main__":
    print(format_last32())
