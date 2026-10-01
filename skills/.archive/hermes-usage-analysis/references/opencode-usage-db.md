# OpenCode local usage DB + subscription-limit projection

Verified 2026-08-16: estimating real LLM usage against the OpenCode Go subscription
($5 first month, $10/mo; caps $12/5h, $30/week, $60/month) using local session data.

## Data sources (laptop, `~/.local/share/opencode/`)

| Source | What it gives |
|--------|---------------|
| `opencode.db` (SQLite) | Per-session ground truth: model, token breakdown, time |
| `auth.json` | Which providers have credentials configured (reveals if a subscription is actually wired up) |
| `~/.config/opencode/opencode.json` | Provider/model config (baseURL, apiKey via {env:...}) |

### opencode.db schema (SQLite)
- Table `session`: columns `model` (JSON string), `tokens_input`, `tokens_cache_read`,
  `tokens_cache_write`, `tokens_output`, `tokens_reasoning`, `cost`, `time_created`
  (epoch **milliseconds** — divide by 1000 for unixepoch), `title`, `directory`.
- **`model` is a JSON blob**, e.g. `{"id":"deepseek-v4-flash-free","providerID":"opencode","variant":"medium"}`.
  Parse it to group by `providerID` — `providerID:"opencode"` is the **free Zen tier**, NOT the Go
  subscription. Go models appear as `opencode-go/<model-id>`.
- `cost` was 0.0 for every row observed — do not trust it; compute cost from tokens × price.

### Key queries
```sql
-- per-model aggregates (parse model JSON in python)
SELECT model, COUNT(*), SUM(tokens_input), SUM(tokens_cache_read),
       SUM(tokens_cache_write), SUM(tokens_output), SUM(tokens_reasoning)
FROM session WHERE model IS NOT NULL AND model != '' GROUP BY model;

-- monthly volume
SELECT strftime('%Y-%m', time_created/1000, 'unixepoch') m, COUNT(*)
FROM session GROUP BY m ORDER BY m DESC;
```
Average per session per model → builds the user's real request profile.

## Projection method (limits are dollar-valued, NOT per-request)

The official Go request-count table assumes LIGHT requests (~700 input / 52k cache-read /
150 output tokens). Real agent sessions (this user: ~184k input + ~4.5M cache-read + ~18.5k
output "heavy", ~49k/216k/5.6k "light") are 10–260x heavier, so the request table does NOT
apply. Correct method:

1. Build per-session token profile from the DB (heavy + light averages).
2. `cost/session = (in×p_in + cacheR×p_cacheR + cacheW×p_cacheW + out×p_out) / 1e6` with the
   subscription's per-1M prices (off-peak for DeepSeek: peak is 01:00–04:00 and 06:00–10:00 UTC).
3. Holgura = dollar cap ÷ cost/session. Caps are account-wide dollars.
4. **"Uso incluido" column matters**: models listed with $15 included (Grok 4.5, GPT 5.6 Luna,
   GLM-5.3, Kimi K3, MiMo-V2.5-Pro, Qwen3.8 Max, DeepSeek V4 Pro/Flash) have ~1/4 the monthly
   budget of the $60 models (GLM-5.1/5.2, Kimi K2.x, MiMo-V2.5, MiniMax, Qwen3.7 Plus, Hy3).

## Results for this user's profile (cache-heavy coding-agent sessions)

| Model | $/heavy session | Heavy sessions/mo (cap) |
|-------|-----------------|-------------------------|
| MiMo-V2.5 | 0.043 | ~1,380 ($60) |
| DeepSeek V4 Flash (off-peak) | 0.084 | ~180 ($15) |
| Hy3 | 0.194 | ~310 ($60) |
| MiniMax M3 | 0.347 | ~173 ($60) |
| GPT 5.6 Luna | 0.374 | ~40 ($15) |
| Kimi K2.7 Code | 1.103 | ~54 ($60) |
| Grok 4.5 / Kimi K3 / Qwen3.8 Max | 1.8–3.9 | ~4–33 (quota traps) |

Winner for this user: DeepSeek V4 Flash (their daily model, near-free cache reads, off-peak
discounts); MiMo-V2.5 as unlimited fallback; Hy3/MiniMax M3 for quality with slack. Premium
models are quota traps for heavy sessions.

## Scope correction (user preference)
When the user asks "estimate my usage with <plan X>" they mean their WHOLE workload across
ALL providers, projected against X's limits — not just the usage already logged under X.
Do the projection from the general per-session profile, not from X-specific rows.
