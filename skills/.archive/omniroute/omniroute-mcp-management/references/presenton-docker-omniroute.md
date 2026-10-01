# Presenton (Docker) → OmniRoute gateway — worked example (2026-08-23)

## Goal

Run the self-hosted AI presentation generator [presenton/presenton](https://github.com/presenton/presenton)
(ghcr.io/presenton/presenton:latest, Apache-2.0, ~2.5 GB image) on the CachyOS laptop, using the
local OmniRoute gateway as the LLM provider — no local models, no API keys in plaintext.

## Working docker run

```bash
source ~/.hermes/.env   # exports OMNIROUTE_API_KEY
mkdir -p ~/presenton/app_data
docker rm -f presenton 2>/dev/null

docker run -d --name presenton \
  --network host \
  -e LLM="custom" \
  -e CUSTOM_LLM_URL="http://localhost:20128/v1" \
  -e CUSTOM_LLM_API_KEY="${OMNIROUTE_API_KEY}" \
  -e CUSTOM_MODEL="Agenticus" \
  -e CAN_CHANGE_KEYS="true" \
  -e DISABLE_ANONYMOUS_TRACKING="true" \
  -e MEM0_ENABLED="false" \
  -v "$HOME/presenton/app_data:/app_data" \
  ghcr.io/presenton/presenton:latest
```

Access: `http://localhost:80` (port 80, because `--network host` means the container's nginx binds
host port 80 directly — the `5001:80` mapping from the README does NOT apply in host-netns mode;
the container's internal banner may still print `http://127.0.0.1:5001`, ignore it).

## Why `--network host` and not `-p 5001:80` + host.docker.internal

First attempt used the README's `-p 5001:80` plus `--add-host=host.docker.internal:host-gateway`
and `CUSTOM_LLM_URL=http://host.docker.internal:20128/v1`. It failed with **connection timed out**
from inside the container. Diagnosis:

- `ss -tlnp` showed omniroute listening on `0.0.0.0:20128` (all interfaces) — so bind was not the issue.
- But from the HOST itself, `curl http://172.17.0.1:20128/v1/models` AND `curl http://192.168.1.18:20128/v1/models`
  both returned HTTP 000, while `curl http://localhost:20128/v1/models` returned 200.
- Conclusion: host firewall (Arch/CachyOS nftables/iptables, no sudo available) answers only on
  loopback. No host-netns trick with docker0/LAN IPs would work without touching the firewall.

Fix: `--network host` — container shares the host network namespace, so `localhost:20128` works
directly. Verified from inside the container:

```bash
docker exec presenton curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $CUSTOM_LLM_API_KEY" http://localhost:20128/v1/models   # → 200
```

Note: `wget` is NOT in the image; `curl` is. `host.docker.internal` did resolve (to 172.17.0.1)
via the --add-host entry, but the firewall still blocked it.

## OmniRoute specifics learned

- `GET http://localhost:20128/v1/models` with `Authorization: Bearer $OMNIROUTE_API_KEY` returns
  ~2176 models: combo names (`Agenticus`), provider-prefixed ids (`kiro/*`, `oc/*`,
  `opencode-zen/*`, `antigravity/*`), and `auto/*` routing aliases (`auto/best-free`,
  `auto/coding:free`, `auto/cheap`, `auto/best-chat`, `auto/best-coding`, …).
- First curl to `/v1/models` right after the gateway is up may return HTTP 000 / time out
  (cold start); retry succeeds with 200. Don't conclude the gateway is down on the first attempt.
- `CUSTOM_MODEL=Agenticus` = the user's default combo (top of stack uses free models:
  opencode-zen / kiro / ollama-cloud) — cost-conscious default for external apps.

## Presenton env vars that matter

- `LLM=custom` → OpenAI-compatible endpoint path.
- `CUSTOM_LLM_URL` / `CUSTOM_LLM_API_KEY` / `CUSTOM_MODEL` → endpoint + key + model.
- `CAN_CHANGE_KEYS=true` → provider/model switchable from the UI (Settings).
- `MEM0_ENABLED=false` → skip presentation-memory service (defaults to a local Ollama-compatible
  endpoint that doesn't exist here); avoids log noise and startup waits.
- `DISABLE_ANONYMOUS_TRACKING=true` → telemetry off.
- First boot: create the admin account manually in the browser (user preference — never invent
  default credentials). Alternative: `AUTH_USERNAME` / `AUTH_PASSWORD` env vars for unattended.

## Lifecycle

```bash
docker stop presenton && docker start presenton   # restart
docker logs presenton --tail 50                   # logs (banner: Mode production, v0.9.7-beta)
docker rm -f presenton                            # remove (data persists in ~/presenton/app_data)
```
