#!/usr/bin/env python3
"""
check_fit.py — Verifica si descripciones OWM caben en display 240x240
con fuente 8x13 a escala 1 y 2 (18px/char y 9px/char).

USO: python3 scripts/check_fit.py

CONTEXTO:
    DeskMate ESP32-C3 + ST7789 240x240
    Fuente 8x13 bitmap, dos escalas:
      - scale 2 (temp): 18px/char, max 13 chars en 240px
      - scale 1 (desc):  9px/char, max 26 chars en 240px

HISTORIAL:
    v2 — 2026-06-07: Nueva sección 'nunca caben' y análisis por prefijo.
"""
FONT8_WIDTH = 8
LCD_WIDTH = 240

def tw(text, scale):
    return len(text) * (FONT8_WIDTH * scale + scale) - scale

# Descripciones OWM reales (lang=es) — ASCII sin acentos
OWM = {}

for c, d in [
    (200,"tormenta electrica con lluvia ligera"),
    (201,"tormenta electrica con lluvia"),
    (202,"tormenta electrica con lluvia intensa"),
    (210,"tormenta electrica ligera"),
    (211,"tormenta electrica"),
    (212,"tormenta electrica intensa"),
    (221,"tormenta electrica irregular"),
    (230,"tormenta electrica con llovizna ligera"),
    (231,"tormenta electrica con llovizna"),
    (232,"tormenta electrica con llovizna intensa"),
    (300,"llovizna de intensidad ligera"),
    (301,"llovizna"),
    (302,"llovizna de intensidad intensa"),
    (310,"llovizna de intensidad ligera"),
    (311,"llovizna"),
    (312,"llovizna de intensidad intensa"),
    (313,"chubascos de lluvia y llovizna"),
    (314,"chubascos de lluvia y llovizna intensa"),
    (321,"chubascos de llovizna"),
    (500,"lluvia ligera"),
    (501,"lluvia moderada"),
    (502,"lluvia intensa"),
    (503,"lluvia muy intensa"),
    (504,"lluvia extrema"),
    (511,"lluvia helada"),
    (520,"lluvia intensa de corta duracion"),
    (521,"chubascos de lluvia"),
    (522,"chubascos de lluvia intensa"),
    (531,"chubascos de lluvia irregular"),
    (600,"nevada ligera"),
    (601,"nieve"),
    (602,"nevada intensa"),
    (611,"aguanieve"),
    (612,"aguanieve ligera"),
    (613,"aguanieve intensa"),
    (615,"lluvia y nieve"),
    (616,"lluvia y nieve"),
    (620,"nevada ligera de corta duracion"),
    (621,"chubascos de nieve"),
    (622,"chubascos de nieve intensa"),
    (701,"niebla"),
    (711,"humo"),
    (721,"calina"),
    (731,"polvo en suspension"),
    (741,"niebla"),
    (751,"arena"),
    (761,"polvo"),
    (762,"ceniza volcanica"),
    (771,"turbonada"),
    (781,"tornado"),
    (800,"cielo claro"),
    (801,"algo de nubes"),
    (802,"nubes dispersas"),
    (803,"muy nuboso"),
    (804,"nubes"),
]:
    OWM[c] = d

MAX_S2 = LCD_WIDTH // (FONT8_WIDTH * 2 + 2)  # 13
MAX_S1 = LCD_WIDTH // (FONT8_WIDTH + 1)       # 26
items = sorted(OWM.items(), key=lambda x: len(x[1]), reverse=True)

print("=" * 72)
print("DESKMATE — TEST DE AJUSTE DE TEXTO (fuente 8x13)")
print(f"Display: {LCD_WIDTH}x240")
print(f"Scale 2 (temp): max {MAX_S2} chars | Scale 1 (desc): max {MAX_S1} chars")
print("=" * 72)

# === ANALISIS POR PREFIJO ===
print()
print(f"{'PREFIJO':<20} {'ANCHO':>6} {'LIBRE':>6} {'CHARS DESC':>10}")
print("-" * 44)
for label, prefix in [("1 digito (5C )", "5C "),
                      ("2 digitos (20C )", "20C "),
                      ("negativa (-15C )", "-15C ")]:
    pw = tw(prefix, 2)
    remaining = LCD_WIDTH - pw
    chars = int(remaining // (FONT8_WIDTH * 2 + 2))
    print(f"{label:<20} {pw:>5}px  {remaining:>4}px  {chars:>4} chars")
print(f"(Cada char a scale 2 = {FONT8_WIDTH*2+2}px)")

# === SCALE 2: TODAS LAS DESCRIPCIONES ===
print()
print("=" * 72)
print("LINEA DE TEMPERATURA — scale 2 (18px/char)")
print(f"Formato: \"{{temp}}C {{desc}}\" — ej: \"-15C tormenta...\"")
print("=" * 72)

PREFIX = "-15C "
PREFIX_LEN = len(PREFIX)
max_desc_chars = MAX_S2 - PREFIX_LEN  # 8 chars

print(f"{'COD':>4} {'DESCRIPCION':<42} {'TOTAL':>5} {'ANCHO':>6} {'CABE?':>7}  {'TRUNCADO':<20}")
print("-" * 72)

fits_count = 0
for code, desc in items:
    full = PREFIX + desc
    w = tw(full, 2)
    if w <= LCD_WIDTH:
        fits_count += 1
        fit = "SI"
    else:
        fit = "NO"

    if len(desc) > max_desc_chars:
        truncated = desc[:max_desc_chars] + ".."
    else:
        truncated = desc

    print(f"  {code:>4} {desc:<42} {len(full):>5} {w:>5}px  {'X' if w<=LCD_WIDTH else ' '} {fit:>3}  {truncated:<20}")

print()
print(f"Caben: {fits_count}/{len(OWM)} con prefijo '{PREFIX}'")
print(f"No caben: {len(OWM)-fits_count}/{len(OWM)}")

# === LAS QUE NUNCA CABEN (ni con prefijo minimo) ===
print()
print("=" * 72)
print("LAS QUE NUNCA CABEN A SCALE 2 (ni con prefijo '5C ')")
print("=" * 72)
PREFIX3 = "5C "
never_count = 0
for code, desc in items:
    if tw(PREFIX3 + desc, 2) > LCD_WIDTH:
        w = tw(PREFIX3 + desc, 2)
        exceed = w - LCD_WIDTH
        print(f"  [{code:>4}] {desc:<45} {w:>4}px (excede por {exceed:>3}px)")
        never_count += 1
print(f"\n  Total: {never_count} de {len(OWM)}")

# === SENSACION ===
print()
print("=" * 72)
print("LINEA DE SENSACION — scale 1 (9px/char)")
print(f"   'Sens: -15C'  ->  {tw('Sens: -15C', 1)}px  (max {MAX_S1} chars)")
print(f"   'Sens: -15%cC' ->  {tw('Sens: -15%cC' % chr(176), 1)}px  (con simbolo de grado)")
print("=" * 72)
print(f"  Siempre cabe: texto fijo de ~89px en 240px ✅")

# === DESCRIPCION MAS LARGA ===
print()
print("=" * 72)
print("DESCRIPCION MAS LARGA vs SOLUCIONES")
print("=" * 72)
longest = max(OWM.values(), key=len)
for code, desc in items:
    if desc == longest:
        longest_code = code
        break
print(f"[{longest_code}] \"{longest}\" ({len(longest)} chars)")

print()
print("SOLUCIONES APLICADAS EN DeskMate v2.1:")
print(f"  A) Icono ({64}px) + temp (scale 2) en misma fila — centrado dinamico")
print(f"  B) Descripcion sola debajo (scale 1 {FONT8_WIDTH+1}px/char, max {MAX_S1} chars)")
print(f"     -> '{longest[:MAX_S1]}...' cabe en 240px ✅")
print(f"  C) Simbolo de grado %cC (char 127 en fuente)" % chr(176))
print()

# === RESUMEN ===
print("=" * 72)
print("RESUMEN DE CAPACIDAD")
print("=" * 72)
print(f"  Scale 2 (temp):     {MAX_S2:>2} chars = {tw('x'*MAX_S2, 2)}px de {LCD_WIDTH}px")
print(f"  Scale 1 (desc):     {MAX_S1:>2} chars = {tw('x'*MAX_S1, 1)}px de {LCD_WIDTH}px")
print(f"  Desc mas larga:     {len(longest)} chars -> a scale 1 trunca a {MAX_S1}")
print(f"  Desc caben completas a scale 1:")
print(f"    Sin prefijo: {sum(1 for d in OWM.values() if tw(d, 1) <= LCD_WIDTH)}/{len(OWM)}")
print(f"    Con '-15C ': {fits_count}/{len(OWM)} (ver arriba)")
