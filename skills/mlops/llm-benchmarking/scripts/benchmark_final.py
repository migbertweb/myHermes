#!/usr/bin/env python3
"""Benchmark opencode-go vs deepseek (directo) for deepseek-v4-flash model."""

import os
import time
import json
import urllib.request
import urllib.error

PROMPT = """Escribe exactamente 3 líneas sobre la teoría de la relatividad de Einstein en español, explicado para niños de 10 años. No agregues introducciones ni despedidas, solo las 3 líneas."""
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; Hermes-Benchmark/1.0)",
}

def call_api(url, api_key, model):
    """Call chat completion API and return timing + usage."""
    base = url.rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    full_url = f"{base}/chat/completions"

    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 300,
        "temperature": 0.7,
        "stream": False,
    }).encode("utf-8")

    headers = dict(HEADERS)
    headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(full_url, data=body, headers=headers, method="POST")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=90) as resp:
        raw = resp.read()
    elapsed = time.time() - t0

    data = json.loads(raw)
    usage = data.get("usage", {})
    content = data["choices"][0]["message"]["content"] if data.get("choices") else ""
    finish = data["choices"][0].get("finish_reason", "?") if data.get("choices") else "?"

    return {
        "time_s": round(elapsed, 3),
        "input_tokens": usage.get("prompt_tokens", "?"),
        "output_tokens": usage.get("completion_tokens", "?"),
        "total_tokens": usage.get("total_tokens", "?"),
        "content": content,
        "finish_reason": finish,
        "model_reported": data.get("model", "?"),
        "cost": usage.get("cost", 0),
    }


PROVIDERS = [
    {
        "label": "opencode-go",
        "url": "https://opencode.ai/zen/go",
        "env_key": "OPENCODE_GO_API_KEY",
        "model": "deepseek-v4-flash",
        "desc": "Suscripción $10/mes (vía opencode.ai)",
    },
    {
        "label": "deepseek (directo)",
        "url": "https://api.deepseek.com",
        "env_key": "DEEPSEEK_API_KEY",
        "model": "deepseek-chat",
        "desc": "Pay-as-you-go (api.deepseek.com)",
    },
]

# Get API keys from environment
for p in PROVIDERS:
    p["api_key"] = os.environ.get(p["env_key"], "")

print("=" * 72)
print("  B E N C H M A R K :  opencode-go  vs  deepseek (directo)")
print("  Modelo: deepseek-v4-flash")
print(f"  3 corridas secuenciales por proveedor")
print("=" * 72)

results = []

for p in PROVIDERS:
    if not p["api_key"]:
        print(f"\n❌ {p['label']}: No API key (${p['env_key']})")
        continue

    print(f"\n📡 {p['label']} — {p['desc']}")
    print(f"   Modelo en API: {p['model']}")
    print("-" * 60)

    times = []
    in_toks = []
    out_toks = []
    contents = []
    models_seen = set()

    for i in range(3):
        try:
            r = call_api(p["url"], p["api_key"], p["model"])
            times.append(r["time_s"])
            in_toks.append(r["input_tokens"])
            out_toks.append(r["output_tokens"])
            contents.append(r["content"])
            models_seen.add(r["model_reported"])
            print(f"  Run {i+1}: ✅ {r['time_s']:>7.3f}s · {r['input_tokens']} in → {r['output_tokens']} out · razón: {r['finish_reason']}")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode(errors="replace")[:200]
            print(f"  Run {i+1}: ❌ HTTP {e.code}: {err_body[:100]}")
        except urllib.error.URLError as e:
            print(f"  Run {i+1}: ❌ Connection: {e.reason}")
        except Exception as e:
            print(f"  Run {i+1}: ❌ {e}")

        time.sleep(0.3)

    if times:
        avg = sum(times) / len(times)
        avg_in = sum(int(t) for t in in_toks if isinstance(t, int)) // max(len([t for t in in_toks if isinstance(t, int)]), 1)
        avg_out = sum(int(t) for t in out_toks if isinstance(t, int)) // max(len([t for t in out_toks if isinstance(t, int)]), 1)
        results.append({
            "label": p["label"],
            "avg_time": round(avg, 3),
            "min_time": round(min(times), 3),
            "max_time": round(max(times), 3),
            "avg_in": avg_in,
            "avg_out": avg_out,
            "sample": contents[0][:100].replace("\n", " | ") if contents else "",
            "models": models_seen,
        })
        print(f"\n  → Promedio: {avg:.3f}s  (min {min(times):.3f}s / max {max(times):.3f}s)")
        print(f"  → Tokens: ~{avg_in} in / ~{avg_out} out por consulta")

# ── Final Results ──
print("\n" + "=" * 72)
print("  R E S U L T A D O S   F I N A L E S")
print("=" * 72)
print(f"{'PROVEEDOR':<22} {'PROMEDIO':<12} {'MÍN':<10} {'MÁX':<10} {'TOK IN':<8} {'TOK OUT':<8}")
print("-" * 72)
for r in results:
    print(f"{r['label']:<22} {r['avg_time']:<10.3f}s {r['min_time']:<8.3f}s {r['max_time']:<8.3f}s {r['avg_in']:<8} {r['avg_out']:<8}")
    print(f"{r['sample'][:85]}")
print("=" * 72)

# Cost & value comparison
if len(results) >= 2:
    print("\n💰 COMPARATIVA DE COSTO/BENEFICIO")
    print("-" * 72)
    r1, r2 = results[0], results[1]
    print(f"{'opencode-go':<22} ${10}/mes fijo (sin costo por consulta adicional)")
    print(f"  · {r1['avg_time']}s promedio por consulta")
    print(f"{'deepseek (directo)':<22} $0.27/M input | $1.10/M output")
    cost_per_query = (r2['avg_in'] / 1_000_000 * 0.27) + (r2['avg_out'] / 1_000_000 * 1.10)
    print(f"  · {r2['avg_time']}s promedio por consulta")
    print(f"  · ~${cost_per_query:.6f} por consulta (a precio oficial)")
    queries_for_10 = 10.0 / cost_per_query if cost_per_query > 0 else float('inf')
    print(f"  · Con $10 pagas ~{int(queries_for_10):,} consultas como esta")

    # Speed comparison
    t1, t2 = r1["avg_time"], r2["avg_time"]
    if t1 < t2:
        faster, slower = r1["label"], r2["label"]
        pct = (t2 - t1) / t2 * 100
    else:
        faster, slower = r2["label"], r2["label"]
        pct = (t1 - t2) / t1 * 100
    print(f"\n⚡ VELOCIDAD: {faster} es ~{pct:.0f}% más rápido que {slower}")

    # Which is better for your usage
    print(f"\n💡 RECOMENDACIÓN:")
    print(f"  • opencode-go: mejor si haces >{int(queries_for_10):,} consultas/mes")
    print(f"  • deepseek directo: mejor si haces <{int(queries_for_10):,} consultas/mes")
    print("  (considerando solo el costo económico, no latencia)")
print("=" * 72)
