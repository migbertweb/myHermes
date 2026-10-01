---
name: hermes-usage-analysis
description: Workflow for analyzing model usage and costs using internal state and dumps.
---

# Hermes Usage & Cost Analysis

This skill provides a deterministic workflow for analyzing the agent's actual token consumption and cost projections by querying the internal SQLite state and analyzing request dumps.

## Workflow

### 1. High-Level Volume Analysis (Hermes internal)

Two complementary data sources exist:

#### A. SQLite state.db (aggregate estimates)
Query `~/.hermes/state.db` to get the total historical and recent token usage.
- **Table:** `sessions`
- **Key Columns:** `input_tokens`, `output_tokens`, `cache_read_tokens`, `estimated_cost_usd`, `actual_cost_usd`.
- **Timeframe:** Use `started_at > strftime('%s', 'now', '-30 days')` for monthly trends.
- **Limitation:** `estimated_cost_usd` is an estimate based on model pricing, not actual billed amounts.

#### B. Hermes billing CSV exports (ground truth) ⭐
When available, these CSV exports from Hermes' Deepseek billing backend provide exact per-day, per-model token counts and actual billed costs. More accurate than `state.db` estimates.

Look for CSV files in `~/Escritorio/usage_data_*/` (exported by Hermes):
- **`amount-<range>.csv`** — per-model, per-day breakdown with columns: `utc_date`, `model`, `type` (input_cache_hit_tokens, input_cache_miss_tokens, output_tokens, request_count), `price` (per-token), `amount` (token count).
- **`cost-<range>.csv`** — per-model, per-day aggregated cost with columns: `utc_date`, `model`, `cost`, `currency`.

These files contain the exact billed amounts, not estimates. Use them as primary source when doing cost projections.

#### Data sources at a glance

| Source | Accuracy | Granularity | Availability |
|--------|----------|-------------|-------------|
| `state.db` | Estimated (~90%) | Per-session | Always |
| Billing CSVs | Exact | Per-day / per-model | Only if Hermes exports them |
| Request dumps | Exact | Per-request | Debug captures only |

### 2. Projecting costs at a DIFFERENT provider's pricing

When evaluating a provider switch (e.g. from Hermes-provisioned DeepSeek to your own DeepSeek direct key), `state.db` and billing CSVs reflect the OLD provider's pricing. You must recalculate:

**Formula:**
```
monthly_cost = (input_hit_tokens/mo × provider_hit_price)
             + (input_miss_tokens/mo × provider_miss_price)
             + (output_tokens/mo × provider_output_price)
```

**Cache hit ratio:**
```
hit_ratio = cache_hit_tokens / (cache_hit_tokens + cache_miss_tokens)
```

**Apply to new provider's cache pricing:**
- If the new provider has its own cache system (e.g. DeepSeek direct at 75% off), use the NEW hit/miss prices with the SAME hit ratio from the billing CSV.
- ⚠️ **Critical:** Hermes-provisioned DeepSeek keys have negotiated cache pricing (observed: $0.0028/M for flash) that is **NOT** available via DeepSeek direct ($0.035/M — 12.5x more expensive). Always verify the new provider's actual cache pricing, not the Hermes rate.

### 3. Deep Dive via Request Dumps
When specific request patterns or "per-call" costs are needed, analyze the JSON files in `~/.hermes/sessions/request_dump_*.json`.
- **Pattern:** `request_dump_<session_id>_<timestamp>_<id>.json`
- **Content:** The `request.body` contains the exact prompt, messages, and tool definitions sent to the provider.
- **Estimation:** If token counts are missing from the dump, estimate input tokens using a ~4 chars per token ratio for mixed English/Spanish content.

### 4. Cost Projection & Provider Comparison
Compare actual usage volume against provider pricing.

**Workflow for a provider-switch analysis:**

1. Gather billing CSVs (preferred) or query `state.db` for the last ~7-14 days of usage
2. Calculate daily averages: requests/day, input tokens/day (split by hit/miss), output tokens/day
3. Monthly projection: multiply by 30
4. Apply target provider's pricing to the projected volume (see formula above)
5. Run a low-volume benchmark (3 requests) on each provider to compare latency and actual token counts — these may differ significantly from the billing data due to system prompt overhead
6. Compare against subscription alternatives (e.g. OpenCode Go at $10/mo fixed)

> **Reference:** `references/provider-switch-cost-analysis.md` — detailed walkthrough with real data from a DeepSeek-direct-vs-OpenCode-Go analysis, including the Hermes cache price trap and volume estimation pitfalls.

## Pitfalls & Lessons
- **Dump Files $\\neq$ All Calls:** Request dumps often only contain failed requests or specific debug captures. Always trust the billing CSVs for total volume and dumps for request structure.
- **Character-to-Token Ratio:** Estimation is rough. For precise costs, always check if the provider's response (recorded in `state.db`) has the exact `usage` field.
- **DB Schema:** `sessions` is the source of truth for aggregate billing; `messages` is for content.
- **Benchmark vs Real Volume mismatch:** A benchmark test with a single minimal prompt (~50 tokens) gives a completely different token-per-request ratio than real Hermes usage (~75,000 tokens/request including system prompt, tool schemas, and conversation history). Always use billing CSV or `state.db` data for volume estimates, not benchmark results.
- **Hermes cache pricing is special:** The cache hit prices you see in billing CSVs are negotiated rates unique to Hermes infrastructure. Do NOT assume DeepSeek direct or any other provider offers the same rates.
- **Subscription vs pay-per-use:** At ~4,900 requests/month, OpenCode Go's $10 fixed plan can be cheaper than DeepSeek direct ($15-25/mo estimated). Run the numbers before switching providers.
- **Pre-audit the config before projecting costs:** A config may have silent cost leaks (MoA preset not active, fallback on paid provider, auxiliary tasks on paid model) that inflate the real usage volume beyond what you expect. See `model-provider-setup` skill → section "8a. Config Audit: Detecting Cost Leaks" for the checklist.

## Related Scripts
- `scripts/analyze_usage.py`: Python script to aggregate and project costs from state.db.

## Related References
- `references/provider-switch-cost-analysis.md`: Real-world walkthrough of comparing Hermes-provisioned DeepSeek vs DeepSeek direct vs OpenCode Go subscription. Includes the Hermes cache pricing trap, volume estimation from billing CSVs, and the decision matrix.
