# Provider Switch Cost Analysis (Real-World Walkthrough)

This reference documents the methodology used to evaluate switching from Hermes-provisioned DeepSeek (with negotiated cache pricing) to DeepSeek direct (api.deepseek.com, standard pricing), and comparing it against OpenCode Go's $10/mo subscription.

## Context

The user was paying for OpenCode Go ($10/mo fixed) and considering switching to DeepSeek direct (pay-per-use) for their primary LLM provider after running a latency benchmark.

### The Trap: Hermes Cache Pricing is Not Standard

The Hermes billing CSV showed cache hit pricing of **$0.0028/M tokens** for DeepSeek V4 Flash. This is a **negotiated rate** unique to Hermes infrastructure. DeepSeek direct's official cache hit pricing is **$0.035/M** (75% off the $0.14/M miss price) — **12.5x more expensive**.

**If you assume the Hermes cache price carries over to DeepSeek direct, your cost projection will be off by a factor of 12.5x on cache-hit input tokens.**

## Data Sources Used

### 1. Hermes Usage Tracking CSVs

Exported by Hermes to `~/Escritorio/usage_data_<range>/`:

**`amount-<range>.csv`** — per-model, per-day breakdown:
```
utc_date,model,type,price,amount
20260711,deepseek-v4-flash,input_cache_hit_tokens,0.0000000028,4403200
20260711,deepseek-v4-flash,input_cache_miss_tokens,0.00000014,264708
20260711,deepseek-v4-flash,request_count,,111
20260711,deepseek-v4-flash,output_tokens,0.00000028,52660
```

**`cost-<range>.csv`** — aggregated cost per day:
```
utc_date,model,cost
20260711,deepseek-v4-flash,0.06413288
```

### 2. Monthly Summary CSV

Created by querying `state.db` via the `consumo_tokens` workflow:

```
mes,sesiones,tokens_input,tokens_output,tokens_cache_read,total_tokens,costo_estimado_usd
2026-06,28,1460641,104855,10720128,12285624,0.0
2026-07,45,14447164,928647,76882755,92258566,2.20
```

### 3. Provider Benchmark

A standalone benchmark script runs 3 requests per provider with a standard prompt to compare:
- Latency (seconds per request)
- Token counts (input, output)
- Finish reason (stop vs length — OpenCode Go truncated at 300 tokens)
- Model reported by API

## Step-by-Step Cost Analysis

### Step 1: Calculate Daily Volume from Billing CSVs

Using the `amount-<range>.csv` data (exact, not estimated):

```python
# Example: 2 days of data (Jul 11-12, 2026)
ds_req = 47 + 111 + 168          # 326 requests
ds_in_hit = 3519360 + 4403200 + 15209856   # 23,132,416
ds_in_miss = 248101 + 264708 + 797161       # 1,309,970
ds_out = 20042 + 52660 + 94914              # 167,616

hit_ratio = ds_in_hit / (ds_in_hit + ds_in_miss)
req_dia = ds_req / 2             # 163/day
in_dia = (ds_in_hit + ds_in_miss) / 2  # 12.2M/day
out_dia = ds_out / 2             # 83.8K/day
```

### Step 2: Project Monthly Volume

Multiply daily averages by 30:
- Requests: 163 × 30 = **4,890/mes**
- Input: 12.2M × 30 = **367M tokens/mes**
- Output: 83.8K × 30 = **2.5M tokens/mes**

### Step 3: Apply Target Provider Pricing

**DeepSeek direct standard pricing:**
- Input cache hit: $0.035/M
- Input cache miss: $0.14/M
- Output: $0.28/M

**Calculate for different cache hit scenarios:**

```python
DS_HIT = 0.035   # $/M
DS_MISS = 0.14   # $/M
DS_OUT = 0.28    # $/M

for hit_ratio in [0.95, 0.70, 0.00]:
    cost = (in_dia*30*hit_ratio)/1e6*DS_HIT \
         + (in_dia*30*(1-hit_ratio))/1e6*DS_MISS \
         + (out_dia*30)/1e6*DS_OUT
```

| Scenario | Hit ratio | Monthly cost | vs $10 plan |
|----------|-----------|-------------|-------------|
| Optimistic | 95% | **$15.46** | $5.46 more |
| Moderate | 70% | **$25.09** | $15.09 more |
| Pessimistic | 0% | **$52.03** | $42.03 more |

### Step 4: Compare Against Subscription

OpenCode Go = $10/mo fixed. At this volume (~4,900 req/mo), the subscription is **cheaper** than DeepSeek direct in all cache scenarios.

The break-even point: only if daily volume drops significantly or cache hit ratio exceeds 95% would DeepSeek direct undercut the $10 plan.

### Step 5: Benchmark for Qualitative Comparison

Beyond cost, run a small benchmark to compare user experience:

```bash
python3 /path/to/benchmark_providers.py
```

| Metric | OpenCode Go | DeepSeek direct |
|--------|------------|-----------------|
| Avg latency | 3.72s | **2.05s** (45% faster) |
| Output limit | **300 tokens** (truncated) | Natural completion |
| Input/report | 129 tok (inflated) | 50 tok (clean) |

## Key Lessons

1. **Billing CSVs over state.db** — the CSV exports contain exact billed amounts, not estimates. Prefer them when available.

2. **Cache pricing is provider-specific** — never assume one provider's cache pricing applies to another. Hermes' negotiated rates are unique.

3. **Benchmark tokens ≠ real usage** — a benchmark with a minimal prompt gives ~50 input tokens/request. Real Hermes usage averages ~75,000 input tokens/request (includes system prompt, tool schemas, conversation history, subagent calls).

4. **Requests are nested** — each user message to Hermes triggers multiple API calls (tool calls, subagents, internal reasoning). 163 API requests/day does not mean 163 user interactions.

5. **Subscription can beat pay-per-use at scale** — at moderate-to-heavy Hermes usage, a fixed $10/mo plan can be cheaper than pay-per-use, even with a "cheap" provider like DeepSeek.

## Decision Matrix

| Volume (req/mo) | DeepSeek direct est. | Better choice |
|----------------|---------------------|---------------|
| < 1,000 | $3-5/mo | DeepSeek direct |
| 1,000 - 3,000 | $5-15/mo | DeepSeek direct |
| **3,000 - 10,000** | **$10-30/mo** | **OpenCode Go ($10 fixed)** |
| > 10,000 | $20-60+/mo | OpenCode Go ($10 fixed) |
