---
name: lightweight-server-monitoring
description: Procedures for deploying and optimizing lightweight monitoring and connectivity agents (Beszel, cloudflared) on resource-constrained servers (e.g., Oracle Free Tier).
tags: [monitoring, cloudflared, beszel, optimization, oracle-free-tier, resource-constrained]
---

# Lightweight Server Monitoring & Connectivity

This skill governs the deployment and resource optimization of essential "background" agents. The goal is to maintain visibility and access without starving the primary applications (like S3 storage or web apps) of RAM and CPU.

## 🛠️ Optimization Patterns

### Beszel Agent
Beszel is efficient, but can be further slimmed down to avoid unnecessary CPU cycles and I/O.

**Recommended Low-Resource Configuration:**
- `LOG_LEVEL=warn`: Reduces log I/O.
- `SKIP_GPU=true`: Essential for cloud VPS (Oracle/AWS) that lack GPUs.
- `SKIP_SYSTEMD=true`: Disable if you don't need to monitor specific systemd services.
- `DISABLE_SSH=true`: Disable if using WebSocket connections (via `HUB_URL`).

### cloudflared (Cloudflare Tunnel)
`cloudflared` can be a memory hog compared to other agents. Aggressive optimization is required for < 2GB RAM servers.

**Optimization Flags (Binary/Systemd):**
- `--loglevel warn`: Reduces verbose logging.
- `--metrics localhost:0`: Disables the metrics endpoint.
- `--management-diagnostics false`: Disables debug routes (`/debug/pprof`, `/metrics`).
- `--proxy-keepalive-connections 10`: Reduces the connection pool (default is often too high for small VPS).

**Optimization Env Vars (Docker/Dokploy):**
- `TUNNEL_LOGLEVEL=warn`
- `TUNNEL_METRICS=localhost:0`
- `TUNNEL_MANAGEMENT_DIAGNOSTICS=false`

**Resource Limits (Crucial):**
- Memory Limit: `64M`
- CPU Limit: `0.1` (10% of a core)

## ⚠️ Pitfalls & Lessons

- **OOM Spirals**: On Oracle Free Tier, `cloudflared` is a prime candidate for OOM kills if not limited. Always set hard Docker memory limits.
- **I/O Wait**: Setting `LOG_LEVEL=info` on multiple agents can lead to high I/O wait on slow cloud disks. Always prefer `warn` for background agents.
- **Networking**: When using Beszel, `network_mode: host` is typically required for accurate system metrics.

## 📖 References
- See `references/agent-env-vars.md` for a full list of Beszel and cloudflared optimization variables.
