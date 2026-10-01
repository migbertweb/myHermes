# Tuya Device Discovery & Troubleshooting Guide

## Why IPs go stale

Tuya smart plugs on DHCP can change IPs after router reboot, power outage, or lease renewal. The `tinytuya wizard` cloud data (`devices.json`) includes the device ID and local key but may have **stale or public IPs** — the local LAN IP must be discovered via UDP broadcast.

## Discovery Methodology

### Method 1: Quick scan (18 seconds)

```bash
ssh serverhogar
/home/piro/.tuya-venv/bin/python3 -c "
import tinytuya
devices = tinytuya.deviceScan()
for ip, info in devices.items():
    print(f'{ip}: {info[\"gwId\"]} v{info[\"version\"]}')
"
```

Only finds devices that broadcast on UDP ports 6666/6667/7000. Silent devices (not broadcasting) won't appear.

### Method 2: Brute-force IP + version matrix

When a device is in `devices.json` but not found by scan, try its ID/key with different IPs and protocol versions.

### Method 3: Cloud data check

The cloud API (`tuya-raw.json`) shows online/offline status but only public IPs, not LAN IPs.

## SSH Quoting Pitfall

**Tuya local keys contain backticks** (e.g. `!5fV~`:v7+i@@nIL`). Backticks are interpreted as command substitution by bash even inside `<<'EOF'` heredocs in some shells.

**Never inline a Tuya key in a bash command passed over SSH.** Always:

1. Write the script locally with `write_file` (bypasses shell escaping)
2. Copy to server: `scp /tmp/script.py serverhogar:/tmp/`
3. Run on server via the tuya venv

Or encode the script in base64 and decode on the server side.

## Protocol Version Troubleshooting

| Symptom | Likely cause |
|---------|-------------|
| `Error: "Check device key or version"` / `Err: "914"` | Wrong protocol version in script |
| Timeout (silent hang) | Wrong IP or device not reachable |
| `Error: 'dps'` | Device reachable (ping) but app layer hung — needs physical power cycle |

### Version detection

- Older Tuya devices (pre-2020): v3.1
- Most common: v3.3
- Newer devices: v3.4 or v3.5
- If unsure, start with 3.3 then try 3.4, 3.5, 3.1

An unresponsive device (exit 124 / timeout) with the wrong version gives no response at all (the connection silently fails). A `914` error means you connected but the key/version is wrong.

## Tinytuya useful params

```python
d.set_socketPersistent(False)   # avoid hanging connections
d.set_socketTimeout(seconds)    # faster failure (default is long)
```

## Scan results reference (28/jun/2026)

| Device | LAN IP | Version | Status |
|--------|--------|---------|--------|
| TV cuarto | 192.168.1.2 | 3.3 | Responds to broadcast |
| TV sala | NOT FOUND | 3.5 (assumed) | Silent on UDP |
| Tramontina | N/A (IPv6 only) | 3.1 | No LAN broadcast |
