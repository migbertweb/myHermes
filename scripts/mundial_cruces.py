#!/usr/bin/env python3
"""
Calcula los cruces reales del Mundial 2026.
V2: asignación correcta de terceros lugares (cada equipo una vez).
"""
import json
from urllib.request import urlopen

BASE = "https://wheniskickoff.com/data/v1"
BRT = -3  # offset from UTC

def fetch(url):
    return json.loads(urlopen(url, timeout=10).read())

def calc():
    matches = fetch(f"{BASE}/matches.json")["data"]
    teams_data = fetch(f"{BASE}/teams.json")["data"]
    
    team_info = {t["code"]: {"name": t["name"], "flag": t.get("flag", ""), "group": t.get("group", "")}
                 for t in teams_data}
    
    standings = {}
    for code, info in team_info.items():
        standings[code] = {"pts": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "gd": 0,
                           "name": info["name"], "flag": info["flag"],
                           "group": info["group"], "code": code}
    
    for m in matches:
        if m.get("status") != "FINISHED": continue
        h, a = m["home"], m["away"]
        hs, aws = m.get("score_home"), m.get("score_away")
        if hs is None or aws is None: continue
        if h not in standings or a not in standings: continue
        standings[h]["gf"] += hs; standings[h]["ga"] += aws
        standings[a]["gf"] += aws; standings[a]["ga"] += hs
        standings[h]["gd"] = standings[h]["gf"] - standings[h]["ga"]
        standings[a]["gd"] = standings[a]["gf"] - standings[a]["ga"]
        if hs > aws: standings[h]["pts"] += 3; standings[h]["w"] += 1; standings[a]["l"] += 1
        elif hs < aws: standings[a]["pts"] += 3; standings[a]["w"] += 1; standings[h]["l"] += 1
        else: standings[h]["pts"] += 1; standings[a]["pts"] += 1; standings[h]["d"] += 1; standings[a]["d"] += 1
    
    # Group sorted teams
    groups = {}
    for code, s in standings.items():
        g = s["group"]
        groups.setdefault(g, []).append(s)
    for g in groups:
        groups[g].sort(key=lambda x: (-x["pts"], -x["gd"], -x["gf"]))
    
    winners = {}
    runners = {}
    third_pool = []  # all third places
    for g, teams in sorted(groups.items()):
        if teams: winners[g] = teams[0]
        if len(teams) >= 2: runners[g] = teams[1]
        if len(teams) >= 3:
            t = teams[2]; t["_group"] = g; third_pool.append(t)
    
    # Rank and take top 8
    third_pool.sort(key=lambda x: (-x["pts"], -x["gd"], -x["gf"]))
    top_third = third_pool[:8]
    
    # Third place assignment MATRIX (FIFA 2026 official):
    # Each qualifying third-place group maps to which match it goes to
    # Based on FIFA knockout match schedule document
    
    # The 8 third-place matchups and which groups they draw from:
    third_slots = [
        (["A","B","C","D","F"], 1, "3ABCDF"),
        (["C","D","F","G","H"], 2, "3CDFGH"),
        (["B","E","F","I","J"], 7, "3BEFIJ"),
        (["A","E","H","I","J"], 8, "3AEHIJ"),
        (["C","E","F","H","I"], 11, "3CEFHI"),
        (["E","H","I","J","K"], 12, "3EHIJK"),
        (["E","F","G","I","J"], 15, "3EFGIJ"),
        (["D","E","I","J","L"], 16, "3DEIJL"),
    ]
    
    # Assign third-place teams to slots: constraint-based greedy
    # Slots with FEWER qualifying groups get FIRST PICK
    available_thirds = {t["_group"]: t for t in top_third}
    third_assignment = {sn: None for _, sn, _ in third_slots}
    
    # Count how many slots each TEAM appears in (lower = more restricted)
    team_slot_count = {}
    for g in available_thirds:
        count = 0
        for cgs, _, _ in third_slots:
            if g in cgs:
                count += 1
        team_slot_count[g] = count
    
    # Assign most restricted teams first
    restricted_order = sorted(available_thirds.keys(), key=lambda g: team_slot_count[g])
    used = set()
    
    for team_group in restricted_order:
        # Find all slots this team can go to (that still have qualifying groups)
        candidates = [(cgs, sn) for cgs, sn, _ in third_slots if team_group in cgs]
        # Among those, find slots that still need a team and have available candidates
        viable = []
        for cgs, sn in candidates:
            if third_assignment[sn] is not None:
                continue
            others = [g for g in cgs if g in available_thirds and g not in used]
            if not others:
                continue
            viable.append((sn, len(others)))
        if not viable:
            continue
        # Pick the slot with FEWEST remaining candidates (most constrained)
        viable.sort(key=lambda x: x[1])
        best_slot = viable[0][0]
        third_assignment[best_slot] = available_thirds[team_group]
        used.add(team_group)
    
    # Fill remaining slots with best available
    for cgs, sn, _ in third_slots:
        if third_assignment[sn] is not None:
            continue
        candidates = [g for g in cgs if g in available_thirds and g not in used]
        if not candidates:
            continue
        best = max(candidates, key=lambda g: (available_thirds[g]["pts"], available_thirds[g]["gd"]))
        third_assignment[sn] = available_thirds[best]
        used.add(best)
    
    # Build matchups
    # Pairing matrix: (match_num, home_type, home_group(s), away_type, away_group(s))
    pairings = [
        (1, "1", ["E"], "3", ["A","B","C","D","F"]),
        (2, "1", ["I"], "3", ["C","D","F","G","H"]),
        (3, "2", ["A"], "2", ["B"]),
        (4, "1", ["F"], "2", ["C"]),
        (5, "2", ["K"], "2", ["L"]),
        (6, "1", ["H"], "2", ["J"]),
        (7, "1", ["D"], "3", ["B","E","F","I","J"]),
        (8, "1", ["G"], "3", ["A","E","H","I","J"]),
        (9, "1", ["C"], "2", ["F"]),
        (10, "2", ["E"], "2", ["I"]),
        (11, "1", ["A"], "3", ["C","E","F","H","I"]),
        (12, "1", ["L"], "3", ["E","H","I","J","K"]),
        (13, "1", ["J"], "2", ["H"]),
        (14, "2", ["D"], "2", ["G"]),
        (15, "1", ["B"], "3", ["E","F","G","I","J"]),
        (16, "1", ["K"], "3", ["D","E","I","J","L"]),
    ]
    
    def get_team(ttype, groups, slot_num):
        if ttype == "1":
            g = groups[0]
            return winners[g] if g in winners else None
        elif ttype == "2":
            g = groups[0]
            return runners[g] if g in runners else None
        elif ttype == "3":
            return third_assignment.get(slot_num)
        return None
    
    third_used = set()
    results = []
    for num, htype, hgroups, atype, agroups in pairings:
        home = get_team(htype, hgroups, num)
        away = get_team(atype, agroups, num)
        
        def fmt(t):
            if t: return f"{t['flag']} {t['name']}"
            return "TBD"
        
        results.append({
            "match_num": num,
            "home": home, "away": away,
            "home_str": fmt(home), "away_str": fmt(away),
        })
    
    return groups, winners, runners, top_third, third_assignment, results

# ── SHOW ──
if __name__ == "__main__":
    groups, winners, runners, top_third, third_assignment, matchups = calc()
    
    # Al usar BRT:
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%b/%Y %H:%M")
    
    print(f"🌍 **Mundial 2026 — Cruces calculados al {now} BRT**")
    print()
    
    # Groups
    for g_letter in sorted(groups.keys()):
        teams = sorted(groups[g_letter], key=lambda x: (-x["pts"], -x["gd"], -x["gf"]))
        statuses = ["🏆", "✅", "🔹", "❌"]
        third_grps = {t["_group"] for t in top_third}
        print(f"**Grupo {g_letter}**")
        for i, t in enumerate(teams):
            st = statuses[i] if i < len(statuses) else "❌"
            if i == 2 and t["_group"] in third_grps: st = "🔹"
            if i >= 2 and t.get("_group", "") not in third_grps: st = "❌"
            print(f"  {st} {t['flag']} {t['name']:25s} {t['pts']}pts GD:{t['gd']:+d}")
        print()
    
    # Mejores terceros
    print("🔸 **8 mejores terceros**")
    for i, t in enumerate(top_third):
        print(f"  {i+1}. {t['flag']} {t['name']:25s} (Grupo {t['_group']}) {t['pts']}pts GD:{t['gd']:+d}")
    print()
    
    # Last 32
    print("🏆 **LAST 32 — Partidos**")
    print()
    for m in matchups:
        print(f"  **Match {m['match_num']:2d}:** {m['home_str']:30s} vs **{m['away_str']}")
    print()
    
    # Show matches with known teams vs TBD
    known = [m for m in matchups if m['home'] and m['away']]
    unknown = [m for m in matchups if not m['home'] or not m['away']]
    print(f"✅ {len(known)}/16 cruces definidos")
    if unknown:
        print(f"⏳ {len(unknown)} cruces con TBD (tercer lugar sin asignar)")
