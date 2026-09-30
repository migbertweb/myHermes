#!/usr/bin/env python3
"""Benchmark OmniRoute auto/reasoning models — speed + output quality."""
import json
import time
import urllib.request
import urllib.error

BASE = "http://localhost:20128/v1"
PROMPT = "Razona paso a paso: Si 3 gatos cazan 3 ratones en 3 minutos, ¿cuántos gatos se necesitan para cazar 100 ratones en 100 minutos? Explica tu razonamiento en español."

PROMPT2 = "¿Cuál es el próximo número en la secuencia: 2, 6, 18, 54, ? Explica el patrón."

MODELS = [
    "auto/reasoning",
    "auto/reasoning:pro",
    "auto/pro-reasoning",
    "auto/best-reasoning",
]


def call_api(model, prompt, run_num):
    """Call OmniRoute and return metrics + response."""
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.7,
        "stream": False,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(f"{BASE}/chat/completions", data=body, headers=headers, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
        elapsed = time.time() - t0
        data = json.loads(raw)

        # Get response headers for actual provider info
        actual_provider = resp.headers.get("x-omniroute-provider", "?")
        actual_model = resp.headers.get("x-omniroute-model", "?")

        usage = data.get("usage", {})
        content = data["choices"][0]["message"]["content"] if data.get("choices") else ""
        finish = data["choices"][0].get("finish_reason", "?") if data.get("choices") else "?"

        # Quality: check if reasoning is present and answer is correct
        has_reasoning = "porque" in content.lower() or "minuto" in content.lower() or "paso" in content.lower() or "gato" in content.lower()
        correct_answer = "100" in content and ("3" in content or "tres" in content or "mismo" in content)
        response_len = len(content)
        quality_score = 0
        if "3 minuto" in content.lower() or "3 gato" in content.lower() or "misma velocidad" in content.lower():
            quality_score += 1
        if "100" in content:
            quality_score += 1
        if has_reasoning:
            quality_score += 1

        return {
            "run": run_num,
            "time_s": round(elapsed, 3),
            "input_tokens": usage.get("prompt_tokens", "?"),
            "output_tokens": usage.get("completion_tokens", "?"),
            "total_tokens": usage.get("total_tokens", "?"),
            "actual_provider": actual_provider,
            "actual_model": actual_model,
            "finish_reason": finish,
            "response_len": response_len,
            "quality_score": quality_score,
            "content_preview": content[:150].replace("\n", " | "),
        }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(errors="replace")[:300]
        return {"run": run_num, "error": f"HTTP {e.code}: {err_body[:150]}", "time_s": 0}
    except urllib.error.URLError as e:
        return {"run": run_num, "error": f"Connection: {e.reason}", "time_s": 0}
    except Exception as e:
        return {"run": run_num, "error": str(e)[:200], "time_s": 0}


def run_benchmark(prompt, label):
    print(f"\n{'='*72}")
    print(f"  PROMPT {label}")
    print(f"  {prompt[:80]}...")
    print(f"{'='*72}")

    results = {}
    for model in MODELS:
        print(f"\n📡 Modelo: {model}")
        print("-" * 60)
        runs = []
        for i in range(3):
            r = call_api(model, prompt, i + 1)
            if "error" in r:
                print(f"  Run {i+1}: ❌ {r['error']}")
            else:
                print(f"  Run {i+1}: ✅ {r['time_s']:.3f}s · {r['input_tokens']}→{r['output_tokens']} tok · provedor: {r['actual_provider']}/{r['actual_model']}")
                print(f"           calidad:{r['quality_score']}/3 · {r['content_preview'][:100]}")
            runs.append(r)
            time.sleep(0.5)

        successes = [r for r in runs if "error" not in r]
        if successes:
            times = [r["time_s"] for r in successes]
            avg_t = sum(times) / len(times)
            out_toks = [r["output_tokens"] for r in successes if isinstance(r["output_tokens"], int)]
            in_toks = [r["input_tokens"] for r in successes if isinstance(r["input_tokens"], int)]
            avg_out = sum(out_toks) // len(out_toks) if out_toks else 0
            avg_in = sum(in_toks) // len(in_toks) if in_toks else 0
            quality_scores = [r["quality_score"] for r in successes]
            avg_q = sum(quality_scores) / len(quality_scores)
            providers = set(r["actual_provider"] for r in successes)
            actual_models = set(r["actual_model"] for r in successes)

            results[model] = {
                "avg_time": round(avg_t, 3),
                "min_time": round(min(times), 3),
                "max_time": round(max(times), 3),
                "avg_in": avg_in,
                "avg_out": avg_out,
                "avg_quality": round(avg_q, 1),
                "providers": providers,
                "actual_models": actual_models,
                "avg_response_len": sum(r["response_len"] for r in successes) // len(successes),
            }
            print(f"\n  → Promedio: {avg_t:.3f}s · min {min(times):.3f}s · max {max(times):.3f}s")
            print(f"  → Tokens: ~{avg_in} in / ~{avg_out} out")
            print(f"  → Calidad: {avg_q:.1f}/3 · provedor: {providers}")

    return results


def print_results_table(all_results, label):
    print(f"\n\n{'='*80}")
    print(f"  R E S U L T A D O S   F I N A L E S  —  {label}")
    print(f"{'='*80}")
    print(f"{'MODELO':<28} {'TIEMPO':<14} {'MÍN':<10} {'MÁX':<10} {'TOK IN':<8} {'TOK OUT':<10} {'CALIDAD':<10}")
    print("-" * 80)

    sorted_results = sorted(all_results.items(), key=lambda x: (x[1]["avg_time"], -x[1]["avg_quality"]))
    best_time = sorted_results[0][1]["avg_time"] if sorted_results else 0

    for model, r in sorted_results:
        time_diff = f"+{((r['avg_time'] - best_time) / best_time * 100):.0f}%" if best_time else "-"
        print(f"{model:<28} {r['avg_time']:<8.3f}s ({time_diff:<4})  {r['min_time']:<8.3f}s {r['max_time']:<8.3f}s {r['avg_in']:<8} {r['avg_out']:<10} {r['avg_quality']:<8}/3")
        provider_str = ", ".join(r["providers"])
        model_str = ", ".join(r["actual_models"])
        print(f"{'':28} provedor: {provider_str}")
        print(f"{'':28} modelo real: {model_str}")
        print()

    print("=" * 80)
    print(f"\n🎯 MEJOR VELOCIDAD: {sorted_results[0][0]} ({sorted_results[0][1]['avg_time']:.3f}s)")
    best_quality = max(sorted_results, key=lambda x: (x[1]["avg_quality"], -x[1]["avg_time"]))
    print(f"🎯 MEJOR CALIDAD:   {best_quality[0]} ({best_quality[1]['avg_quality']}/3)")


# ═══ Run ═══
print("=" * 72)
print("  O M N I R O U T E   B E N C H M A R K  —  auto/reasoning models")
print(f"  {len(MODELS)} modelos · 3 corridas cada uno")
print("=" * 72)

results1 = run_benchmark(PROMPT, "1: Razonamiento lógico (gatos/ratones)")
results2 = run_benchmark(PROMPT2, "2: Patrón numérico (2,6,18,54)")

# Combined ranking
print(f"\n\n{'#'*80}")
print(f"  R E S U M E N   C O M B I N A D O  (ambos prompts)")
print(f"{'#'*80}")
print(f"{'MODELO':<28} {'TIEMPO AVG':<14} {'CALIDAD AVG':<14} {'VELOCIDAD':<14}")
print("-" * 70)

combined = {}
all_models = set(results1.keys()) | set(results2.keys())
for m in all_models:
    r1 = results1.get(m, {})
    r2 = results2.get(m, {})
    times = [r1.get("avg_time", 0), r2.get("avg_time", 0)]
    quals = [r1.get("avg_quality", 0), r2.get("avg_quality", 0)]
    active = sum(1 for t in times if t > 0)
    if active > 0:
        combined[m] = {
            "avg_time": round(sum(times) / active, 3),
            "avg_quality": round(sum(quals) / active, 1),
        }

for m, r in sorted(combined.items(), key=lambda x: (x[1]["avg_time"], -x[1]["avg_quality"])):
    speed = "⚡ rápidísimo" if r["avg_time"] < 10 else ("⚡ rápido" if r["avg_time"] < 20 else ("🐢 lento" if r["avg_time"] < 40 else "🐢 muy lento"))
    print(f"{m:<28} {r['avg_time']:<10.3f}s     {r['avg_quality']:<8}/3        {speed}")

print("\n" + "=" * 80)
print("  RANKING COMBINADO:")
for i, (m, r) in enumerate(sorted(combined.items(), key=lambda x: (x[1]["avg_time"], -x[1]["avg_quality"])), 1):
    print(f"  {i}. {m:<26} — {r['avg_time']:.3f}s · calidad {r['avg_quality']}/3")
print("=" * 80)
