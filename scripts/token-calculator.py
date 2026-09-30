#!/usr/bin/env python3
"""
Token Cost Calculator — Fullstack DevOps
Estima consumo diario de tokens y costo segun modelo.

Uso: python3 token-calculator.py [--fast]
  --fast: usa defaults sin preguntar
"""

import os, sys, json, math
from datetime import datetime

# ── Precios verificados (USD por 1M tokens, input / output) ──────────────
PRECIOS = {
    "hy3-free":              (0.00, 0.00),
    "deepseek-v4-flash-free":(0.00, 0.00),
    "deepseek-v4-flash":     (0.14, 0.28),
    "deepseek-v3.2":         (0.50, 1.00),
    "gemini-2.5-flash":      (0.15, 0.60),
    "claude-sonnet-4":       (3.00, 15.00),
    "claude-opus-4.5":       (15.00, 75.00),
    "gpt-4.1":               (2.00, 8.00),
}

# ── Categorias de actividad ─────────────────────────────────────────────
CATEGORIAS = [
    # (nombre, input_default, output_default, peso_diario_default, desc)
    ("Generar codigo (feature/funcion)",      5500, 800,  8,
     "Contexto + spec → implementacion"),
    ("Debug / fix error",                     8000, 1200, 5,
     "Stacktrace + codigo → diagnostico + fix"),
    ("Code review",                           8000, 900,  3,
     "Diff + archivo → sugerencias"),
    ("Refactor",                              7000, 1200, 3,
     "Archivo completo → codigo reescrito"),
    ("Tests (escribir/debuggear)",            4000, 800,  4,
     "Fuente → archivo de test"),
    ("Docker / docker-compose",               2000, 500,  2,
     "Descripcion → config"),
    ("CI/CD pipeline (GH Actions)",           3000, 800,  2,
     "Requisitos → YAML"),
    ("Terraform / IaC",                       4000, 1000, 2,
     "Arquitectura → HCL"),
    ("Manifiestos K8s",                       3000, 700,  2,
     "Servicio descrito → YAML"),
    ("Analisis de logs / incidentes",         12000, 1500, 1,
     "Logs extensos + contexto → diagnostico"),
    ("Documentacion / README",                4000, 1200, 3,
     "Codigo → docs"),
    ("Discusion de arquitectura",             7000, 1500, 3,
     "Requisitos → diseno"),
    ("Descripcion de PR",                     2000, 400,  3,
     "Resumen diff → descripcion"),
    ("Consulta rapida / duda simple",         2000, 200,  10,
     "Contexto minimo → respuesta breve"),
]

# Factor de acumulacion de contexto en sesiones largas
# Una sesion de 20 mensajes NO es 20x un mensaje, el contexto crece
CTX_MULTIPLIER = lambda n: 1.0 + 0.08 * (min(n, 25) - 1)  # ~3x en 25 msgs

def formatear_usd(c):
    if c == 0:
        return "$0.00"
    if c < 0.01:
        return f"${c:.4f}"
    if c < 100:
        return f"${c:.2f}"
    return f"${c:,.2f}"

def input_int(prompt, default):
    try:
        v = input(f"  {prompt} [{default}]: ")
        return int(v) if v.strip() else default
    except:
        return default

def input_float(prompt, default):
    try:
        v = input(f"  {prompt} [{default}]: ")
        return float(v) if v.strip() else default
    except:
        return default

def input_yn(prompt, default=True):
    v = input(f"  {prompt} {'(Y/n)' if default else '(y/N)'}: ").strip().lower()
    if not v:
        return default
    return v in ('y','yes','s','sim')

# ── Recoleccion de parametros ────────────────────────────────────────────
def recoger_parametros(fast=False):
    if fast:
        actividades = [(n, t_in, t_out, w) for n, t_in, t_out, w, _ in CATEGORIAS]
        return actividades, 22, 0.60, 15, True

    print("=" * 78)
    print("  CALCULADOR DE TOKENS — Fullstack Developer con DevOps")
    print("  Estima consumo diario segun actividad y compara costos por modelo")
    print("=" * 78)

    print("\n>>> Perfil de uso diario (Enter para usar default) <<<\n")

    actividades = []
    for nombre, t_in, t_out, weight, desc in CATEGORIAS:
        d = input_int(f"Cuantas veces/dia \"{nombre}\"?", weight)
        if d > 0:
            actividades.append((nombre, t_in, t_out, d))
        print(f"    ~{nombre.lower()}")

    dias_mes = input_int("Dias laborales al mes?", 22)
    cache_pct = input_float("Cache hit rate (%)? [OpenRouter estima 60-80% para MoE]", 60)
    msgs_por_sesion = input_int("Mensajes promedio por sesion?", 15)

    pagado = input_yn("Incluir modelos de pago en la tabla?", True)
    incluir_pago = pagado

    return actividades, dias_mes, cache_pct / 100, msgs_por_sesion, incluir_pago


# ── Calculo principal ───────────────────────────────────────────────────
def calcular(actividades, dias_mes, cache_rate, msgs_por_sesion):
    total_in = 0
    total_out = 0
    detalle = []

    for nombre, t_in, t_out, veces in actividades:
        # costo efectivo por interaccion considerando acumulacion de ctx
        mult = CTX_MULTIPLIER(msgs_por_sesion)
        tokens_in = int(t_in * mult) if t_in > 0 else 0
        tokens_out = t_out
        daily_in = tokens_in * veces
        daily_out = tokens_out * veces

        total_in += daily_in
        total_out += daily_out

        detalle.append({
            "nombre": nombre,
            "veces": veces,
            "t_in_prompt": tokens_in,
            "t_out_prompt": tokens_out,
            "daily_in": daily_in,
            "daily_out": daily_out,
        })

    # cache reduce tokens facturables (context cache)
    cache_efectivo = min(cache_rate, 0.85)  # max 85%
    total_in_facturable = int(total_in * (1 - cache_efectivo))

    return {
        "total_daily_in": total_in,
        "total_daily_out": total_out,
        "total_daily_in_facturable": total_in_facturable,
        "total_daily_out_facturable": total_out,
        "detalle": detalle,
        "dias_mes": dias_mes,
        "cache_rate": cache_efectivo,
    }


# ── Reporte ─────────────────────────────────────────────────────────────
def reportar(resultados, incluir_pago=True):
    d = resultados
    total_dia_tokens = d["total_daily_in"] + d["total_daily_out"]
    total_dia_fact = d["total_daily_in_facturable"] + d["total_daily_out_facturable"]

    print("\n" + "=" * 78)
    print("  RESUMEN DIARIO DE TOKENS")
    print("=" * 78)

    print(f"\n  {'Actividad':<35s} {'#/dia':>6s} {'Tok.in':>9s} {'Tok.out':>9s} {'Total/d':>9s}")
    print("  " + "-"*70)
    for act in d["detalle"]:
        t = act["daily_in"] + act["daily_out"]
        print(f"  {act['nombre']:<35s} {act['veces']:>6d} {act['daily_in']:>9,d} {act['daily_out']:>9,d} {t:>9,d}")
    print("  " + "-"*70)
    print(f"  {'TOTAL BRUTO (sin cache)':<35s} {'':>6s} {d['total_daily_in']:>9,d} {d['total_daily_out']:>9,d} {total_dia_tokens:>9,d}")
    print(f"  {'TOTAL FACTURABLE (con cache)':<35s} {'':>6s} {d['total_daily_in_facturable']:>9,d} {d['total_daily_out_facturable']:>9,d} {total_dia_fact:>9,d}")

    # NOTA: redondeo a entero para la tabla
    cache_pct = round(d["cache_rate"] * 100)
    print(f"\n  Cache: {cache_pct}% de tokens input NO facturados gracia a context caching")
    print(f"  Context multiplier: {CTX_MULTIPLIER(15):.2f}x en sesiones de ~15 mensajes")

    # ── Comparativa de costos ────────────────────────────────────────
    print("\n" + "=" * 78)
    print("  PROYECCION DE COSTOS POR MODELO")
    print("=" * 78)

    modelos = list(PRECIOS.items())
    if not incluir_pago:
        modelos = [(n,p) for n,p in modelos if p == (0.0, 0.0)]

    print(f"\n  {'Modelo':<30s} {'/dia':>10s} {'/mes':>10s} {'/año':>12s} {'Tipo':>12s}")
    print("  " + "-"*74)

    for nombre, (pin, pout) in modelos:
        costo_dia = (d["total_daily_in_facturable"] / 1e6 * pin +
                     d["total_daily_out_facturable"] / 1e6 * pout)
        costo_mes = costo_dia * d["dias_mes"]
        costo_anual = costo_mes * 12
        tipo = "FREE" if pin == 0 and pout == 0 else "pago"
        print(f"  {nombre:<30s} {formatear_usd(costo_dia):>10s} {formatear_usd(costo_mes):>10s} {formatear_usd(costo_anual):>12s} {tipo:>12s}")

    # ── Reality check ─────────────────────────────────────────────────
    print("\n" + "=" * 78)
    print("  REALITY CHECK")
    print("=" * 78)
    print(f"\n  Un dev fullstack pasa ~2-4h/dia interactuando con AI coding tools.")
    print(f"  Esto equivale a ~{total_dia_fact:,d} tokens facturables/dia")
    print(f"  con cache al {cache_pct}% y ~{d['dias_mes']}d/mes laborales.")
    print(f"\n  Si usas solo FREE tiers (hy3-free o deepseek-v4-flash-free):")
    print(f"  → Costo: $0.00")
    print(f"  → Pero atencion: los free tiers tienen rate limits (tipicamente")
    print(f"    10-60 req/minuto, contexto limitado) y no son SLA.")
    print(f"\n  Para uso profesional sin interrupciones, deepseek-v4-flash")
    print(f"  a ${PRECIOS['deepseek-v4-flash'][0]}/${PRECIOS['deepseek-v4-flash'][1]} por M")
    print(f"  es el piso de pago mas bajo con decente calidad/velocidad.")

    # ── Comparativa cache ON/OFF ─────────────────────────────────────
    # cache SOLO afecta tokens de input, no output
    sin_cache_in = d["total_daily_in"] if d["cache_rate"] >= 1 else int(d["total_daily_in"] / (1 - d["cache_rate"]))
    pin, pout = PRECIOS["deepseek-v4-flash"]
    costo_sin = (sin_cache_in / 1e6 * pin +
                 d["total_daily_out_facturable"] / 1e6 * pout)
    costo_con = (d["total_daily_in_facturable"] / 1e6 * pin +
                 d["total_daily_out_facturable"] / 1e6 * pout)
    print(f"  Sin cache: {formatear_usd(costo_sin)}/dia  →  {formatear_usd(costo_sin * d['dias_mes'])}/mes")
    print(f"  Con cache ({cache_pct}%): {formatear_usd(costo_con)}/dia  →  {formatear_usd(costo_con * d['dias_mes'])}/mes")
    ahorro = (costo_sin - costo_con) / costo_sin * 100 if costo_sin > 0 else 0
    print(f"  Ahorro por context caching: {ahorro:.0f}%")

    # ── Conclusion ────────────────────────────────────────────────────
    print("\n" + "=" * 78)
    print("  CONCLUSION")
    print("=" * 78)

    # Hallar el modelo mas barato de pago que no sea $0
    pagos = [(n, p) for n, p in PRECIOS.items() if p != (0, 0)]
    pagos_por_costo = []
    for n, p in pagos:
        cd = (d["total_daily_in_facturable"] / 1e6 * p[0] +
              d["total_daily_out_facturable"] / 1e6 * p[1])
        pagos_por_costo.append((cd, n, p))
    pagos_por_costo.sort()

    print(f"\n  Tu perfil genera ~{total_dia_fact:,d} tokens facturables/dia.")
    print(f"  Opciones recomendadas (mejor relacion costo/calidad):")
    print(f"    1. hy3-free — $0 (ideal para tareas de razonamiento complejo)")
    print(f"    2. deepseek-v4-flash-free — $0 (rapido, 1M contexto)")
    print(f"    3. deepseek-v4-flash — pago mas economico con buen rendimiento")

    if pagos_por_costo:
        mejor_pago = pagos_por_costo[0]
        print(f"\n  Modelo de pago mas barato: {mejor_pago[1]}")
        print(f"    → {formatear_usd(mejor_pago[0])}/dia  |  {formatear_usd(mejor_pago[0]*d['dias_mes'])}/mes")

    print("\n" + "=" * 78)

def main():
    fast = "--fast" in sys.argv

    print()
    actividades, dias_mes, cache_rate, msgs_por_sesion, incluir_pago = recoger_parametros(fast)

    if not actividades:
        print("  No ingresaste ninguna actividad. Usando defaults...")
        actividades = [(n, t_in, t_out, w) for n, t_in, t_out, w, _ in CATEGORIAS]
        dias_mes = 22
        cache_rate = 0.60
        msgs_por_sesion = 15
        incluir_pago = True

    res = calcular(actividades, dias_mes, cache_rate, msgs_por_sesion)
    reportar(res, incluir_pago)

if __name__ == "__main__":
    main()
