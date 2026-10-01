# OmniRoute Latency & Efficiency Reference (August 2026)

This reference outlines the current performance hierarchy of OmniRoute models, combos, and routing strategies to help select the most efficient option.

## 1. Ultra-Fast Models (Latency < 1s)
When speed is the primary driver, prefer these direct models over dynamic `auto/*` routing. They are free, stable, and have low latency:

*   **`antigravity/claude-sonnet-4-6-high`** (p50: **~0.03s**) - Outstanding for aggregation or super fast single-turn prompts.
*   **`antigravity/claude-opus-4-6-thinking-high`** (p50: **~0.81s**) - Reasoning reference.
*   **`antigravity/gemini-2.5-flash-thinking`** (p50: **~0.92s**) - Quick reasoning.
*   **`kiro/deepseek-3.2`** (p50: **~0.91s**).
*   **`kiro/qwen3-coder-next`** (p50: **~0.95s**).

## 2. Dynamic Routing Strategies (`auto/*` Aliases)
If using dynamic LKGP scoring, understand that latency varies dramatically across aliases:

| Alias | p50 Latency | Recommendation |
| :--- | :--- | :--- |
| `auto/best-fast` | **~3.8s** | Use for standard executor agents. |
| `auto/reasoning` | **~3.9s - 4.8s** | Use for complex reasoning. Fastest reasoning strategy. |
| `auto/best-reasoning`| **~8.1s** | **AVOID**. 2x slower than `auto/reasoning` with high variance. |
| `auto/best-free` | **>30s (Timeout)** | **AVOID**. High rate of failures. |
| `auto/coding` | **>45s (Timeout)** | **AVOID** for interactive sessions. |
| `auto/chat` | **>60s (Timeout)** | **AVOID** for interactive sessions. |

*Warning on `reasoning` aliases:* They consume significant output token budget on thinking steps. Always set `max_tokens >= 200` to prevent empty outputs.

## 3. Recommended MoA (Mixture of Agents) Architectural Strategy
To build high-performance MoA presets:
1.  **Reference Models (Parallel):** Use fast models like `antigravity/gemini-3.6-flash-medium` or `deepseek-v4-flash-free`.
2.  **Aggregator (Single-thread):** Use `antigravity/claude-sonnet-4-6-high` or official DeepSeek API (`deepseek-v4-flash` via `deepseek` provider). Avoid `opencode-go` as aggregator.
