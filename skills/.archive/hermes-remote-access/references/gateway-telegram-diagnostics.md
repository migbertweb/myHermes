# Gateway / Telegram Diagnostics Reference

Known-good signal signatures and common pitfalls from a real deployment
(Session 2026-06-02, user migbert on CachyOS laptop, piro on Ubuntu 24.04 server).

## Check Gateway Service

```bash
ssh piro@server "systemctl --user status hermes-gateway"
```

**Known-good output:**

```
● hermes-gateway.service - Hermes Agent Gateway - Messaging Platform Integration
     Loaded: loaded (/home/piro/.config/systemd/user/hermes-gateway.service; enabled; preset: enabled)
     Active: active (running) since Mon 2026-06-01 00:36:47 UTC; 2 days ago
   Main PID: 14620 (hermes)
```

## Verify Bot Token

```bash
ssh piro@server 'TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2-); curl -s --connect-timeout 10 "https://api.telegram.org/bot${TOKEN}/getMe"'
```

**Known-good response:**

```json
{"ok":true,"result":{"id":8335653216,"is_bot":true,"first_name":"Viernes_HermesBot","username":"mihermesserver_bot","can_join_groups":true,"can_read_all_group_messages":true,...}}
```

**Bad token response:** `{"ok":false,"error_code":404,"description":"Not Found"}`

## Logs: Network Blip (Transient)

```bash
ssh piro@server "journalctl --user -u hermes-gateway --since '1 hour ago' --no-pager"
```

**Transient (safe to ignore):**

```
WARNING gateway.platforms.telegram_network: [Telegram] Primary api.telegram.org connection failed (); trying fallback IPs 149.154.166.110
```

This appears once, then silence. Fallback IP works. Only worry if it repeats every polling cycle.

## Check Message Delivery

```bash
ssh piro@server "python3 -m json.tool ~/.hermes/sessions/sessions.json 2>/dev/null"
```

**Key fields to inspect:**

- `"platform": "telegram"` — confirms Telegram origin
- `"updated_at"` — recent timestamp = gateway processed message
- `"origin"` → `"message_id"` — last message ID consumed
- `"display_name"` — user's Telegram display name
- `"session_key"` — format: `agent:main:telegram:dm:<chat_id>`

## Channel Directory Freshness

```bash
ssh piro@server "cat ~/.hermes/channel_directory.json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(\"Updated:\", d.get(\"updated_at\")); print(\"Telegram channels:\", len(d.get(\"platforms\",{}).get(\"telegram\",[])))'"
```

If `updated_at` is minutes old, gateway is alive.

## Session Isolation

Telegram messages DO NOT route to the active CLI session on another machine. They create a new session on the server where the gateway runs. To confirm, look for a separate session in `sessions.json` with `"platform": "telegram"`.

```
Telegram msg ──► gateway (server) ──► new server session (ID: 20260601_013800_...)
CLI (laptop)  ─────────────────────► different session
```

## Common Pitfalls

| Symptom | Root Cause |
|---|---|
| `Permission denied (publickey,password)` | Wrong SSH user (server user is `piro`, not laptop user `migbert`) |
| `getUpdates` returns `[]` | Normal — gateway long polling consumed all updates already. Check `sessions.json` instead |
| Gateway shows `Active: active (running)` but no messages arrive | Check `journalctl` for network errors; bot token may be invalid |
| `NetworkError` in logs but ping to api.telegram.org works | Usually transient IPv4/IPv6 or DNS issue; gateway auto-fallsback |
