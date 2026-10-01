# OmniRoute Chat Admission Semaphore — diagnosis reference

## Symptom

Hermes fails with repeated `HTTP 503: Structurally heavy chat request capacity is busy; retry shortly.`
across ALL models (primary AND fallback), while the OmniRoute gateway itself responds fine to
light requests (`/health` dashboard HTML loads, simple chat completions work at ~3-5ms).

Typical trigger: kanban task or MoA run with full toolset (bfl, browser, file, terminal, 107 MCP
omniroute tools, ...) overlapping another heavy request. All retries fail because the slot stays
held for the full retry window (~20s).

## Root cause

Source: `<npm-global>/lib/node_modules/omniroute/src/shared/middleware/chatBodyAdmission.ts`

OmniRoute guards against memory amplification from large chat bodies with a **process-local
admission semaphore** for "structurally heavy" requests:

| Env var | Default | Meaning |
|---|---|---|
| `OMNIROUTE_CHAT_MAX_HEAVY_IN_FLIGHT` | 1 | Max concurrent heavy requests (single slot!) |
| `OMNIROUTE_CHAT_HEAVY_TOOL_COUNT` | 64 | tools.length ≥ this → heavy |
| `OMNIROUTE_CHAT_HEAVY_MESSAGE_COUNT` | 200 | messages.length ≥ this → heavy |
| `OMNIROUTE_CHAT_HEAVY_ESTIMATED_TOKENS` | 32_000 | conservative structure token estimate ≥ this → heavy |
| `OMNIROUTE_CHAT_LARGE_BODY_BYTES` | 256 KiB | body ≥ this reserves a lease before parse |
| `OMNIROUTE_CHAT_HARD_MAX_BODY_BYTES` | 50 MiB | hard reject → 413 |
| `OMNIROUTE_CHAT_HARD_MAX_MESSAGES` | 800 | messages > this → 413 |

Heavy classification: `messages.length >= heavyMessages || tools.length >= heavyTools` OR the
conservative token estimator (0.25 token per ASCII char, 1 per non-ASCII, depth-capped at 12)
hits `heavyTokens` across messages+tools.

**Why Hermes always trips it:** each request carries the full toolset including ~107 `mcp_omniroute_*`
tools → `tools.length` (≥ 100) > 64 default → EVERY Hermes request is "heavy" → all compete for the
single `MAX_HEAVY_IN_FLIGHT=1` slot. Second concurrent heavy request gets 503 with `Retry-After: 1`.

The lease is held through the SSE stream lifecycle (`releaseChatAdmissionWhenDone` releases on
stream end / cancel / error), so a slow provider (local CPU model) or long MoA generation holds
the slot for the whole response — inflating the 503 window for everyone else.

## Fix (applied on laptop 2026-08-08)

Edit `~/.config/systemd/user/omniroute.service`, add to `[Service]`:

```
Environment=OMNIROUTE_CHAT_MAX_HEAVY_IN_FLIGHT=3
Environment=OMNIROUTE_CHAT_HEAVY_TOOL_COUNT=200
```

Then:

```bash
systemctl --user daemon-reload
systemctl --user restart omniroute   # ~5s downtime; in-flight requests die, next ones recover
```

With `HEAVY_TOOL_COUNT=200` normal Hermes requests are no longer classified heavy; only genuinely
giant bodies (>32k estimated tokens or >256KB) enter the semaphore, and there are now 3 slots.

## Verification

```bash
systemctl --user is-active omniroute
PID=$(pgrep -f "node .*omniroute serve" | head -1)
tr '\0' '\n' < /proc/$PID/environ | grep OMNIROUTE_CHAT   # expect MAX=3, TOOL_COUNT=200
# smoke test with tools (Bear key from ~/.hermes/.env):
curl -s -X POST http://localhost:20128/v1/chat/completions \
  -H "Authorization: Bearer $OMNIROUTE_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"dev-back","messages":[{"role":"user","content":"ping"}],
       "tools":[{"type":"function","function":{"name":"read_file","description":"read",
       "parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}}],
       "max_tokens":10}'
```

Expected: SSE stream with `[DONE]`, `x-omniroute-version` header present.

## Diagnostic shortcuts (for the next occurrence)

- `curl -s localhost:20128/health` returns the Next.js dashboard HTML, NOT JSON — don't use it as a
  health probe. Real health comes from the MCP tool `omniroute_get_health` (heap, circuit breakers,
  rate limits — all clean in this incident) or a live chat request.
- Light request OK + heavy (tools) request 503 = admission semaphore, not provider outage.
- `ps aux | grep "omniroute serve"` shows the npm process; systemd unit `omniroute.service` (user).
- `pgrep -f "node .*omniroute serve"` matches the real server PID (the bare `pgrep -f "omniroute serve"` can miss or match multiple).
