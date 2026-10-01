# OmniRoute Gateway Health Probe (Docker)

This probe performs a deep health check on an OmniRoute gateway running in Docker, verifying process status, resource usage, provider connectivity, and recent traffic logs.

## 1. Process & Container Status
- **Docker Status:** `docker ps` to check if container is `Up` and `healthy`.
- **Inspect State:** `docker inspect omniroute --format='{{json .State}}'` to check for `OOMKilled` or restart loops.
- **Resources:** `docker stats omniroute --no-stream` for real-time CPU/MEM.

## 2. Provider Connectivity Audit
OmniRoute stores its configuration in a SQLite DB. Since the container often lacks the `sqlite3` binary, use a `node` one-liner with `better-sqlite3` (built into OmniRoute) to query the state:

```bash
docker exec omniroute node -e "
const Database = require('better-sqlite3');
const db = new Database('/app/data/storage.sqlite', { readonly: true });
const connections = db.prepare('SELECT provider, name, test_status, is_active, last_error FROM provider_connections').all();
connections.forEach(c => console.log(\`- \${c.provider} (\${c.name}): status=\${c.test_status}, active=\${c.is_active}, err=\${c.last_error || 'none'}\`));
"
```

## 3. Traffic & Log Analysis
- **Live Logs:** `docker logs --tail 50 omniroute` to spot `AUTH` failures or `COMBO` routing errors.
- **Call History:** Query the `call_logs` table to verify successful completions (HTTP 200) and latencies.

```bash
docker exec omniroute node -e "
const Database = require('better-sqlite3');
const db = new Database('/app/data/storage.sqlite', { readonly: true });
const recent = db.prepare('SELECT provider, requested_model, status, duration, timestamp FROM call_logs ORDER BY id DESC LIMIT 5').all();
console.log(recent);
"
```

## 4. Common Failure Signals
- **Health check timeout:** `Health check exceeded timeout (5s)` in `docker inspect` usually indicates high CPU load or deadlock.
- **Provider Error:** `status=error` in `provider_connections` indicates an API key issue or upstream outage.
- **Auth Failures:** `session_key=... has no available affinity target` in logs often means the session has expired or the account is locked.