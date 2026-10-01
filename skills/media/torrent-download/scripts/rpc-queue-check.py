#!/usr/bin/env python3
"""
Transmission RPC queue diagnostic script.

Queries transmission-daemon via its HTTP RPC API and prints each torrent's
real status, metadata progress, peer connectivity, and queue position.

The CLI command `transmission-remote -l` collapses several internal states
into "Idle", making it impossible to distinguish:
  - "downloading with no peers" (stuck, occupying a queue slot)
  - "waiting for a queue slot" (DownloadWait, would start if a slot freed)
  - "seeding/completed with no activity"

This script shows the actual RPC status codes so you can diagnose queue clogs.

Usage:
  python3 rpc-queue-check.py
"""

import urllib.request, urllib.error, json, re
from collections import Counter

RPC_URL = "http://127.0.0.1:9091/transmission/rpc"

def rpc_call(method, args=None):
    payload = json.dumps({"method": method, "arguments": args or {}}).encode()
    req = urllib.request.Request(
        RPC_URL, data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 409:
            body = e.read().decode()
            m = re.search(r"X-Transmission-Session-Id:\s*([a-zA-Z0-9]+)", body)
            if not m:
                raise RuntimeError("Could not extract session ID")
            sid = m.group(1)
            req2 = urllib.request.Request(
                RPC_URL, data=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Transmission-Session-Id": sid,
                }
            )
            resp2 = urllib.request.urlopen(req2)
            return json.loads(resp2.read())
        raise

STATUS_NAMES = {
    0: "Stopped", 1: "CheckWait", 2: "Checking",
    3: "DownloadWait", 4: "Downloading", 5: "SeedWait",
    6: "Seeding", 7: "Isolated",
}

# --- Fetch data ---
data = rpc_call("torrent-get", {
    "fields": [
        "id", "name", "status", "percentDone", "rateDownload",
        "rateUpload", "errorString", "queuePosition",
        "peersConnected", "metadataPercentDone",
    ]
})
session = rpc_call("session-get")

# --- Print torrent table ---
print(f"{'ID':>3} {'Status':15s} {'Done':>6} {'Meta':>5} {'Down':>8} {'Peers':>5} {'QueuePos':>4}  Name")
print("-" * 90)
for t in sorted(data["arguments"]["torrents"], key=lambda x: x["id"]):
    st = STATUS_NAMES.get(t["status"], f"?{t['status']}")
    done = f"{t['percentDone']*100:.0f}%"
    meta = f"{t.get('metadataPercentDone', 0)*100:.0f}%"
    down = f"{t['rateDownload']/1024:.0f}K"
    peers = t["peersConnected"]
    qpos = t.get("queuePosition", "?")
    name = t.get("name", "")[:55]
    err = t.get("errorString", "")
    marker = " ◀ STUCK" if (t["status"] == 4 and t["rateDownload"] == 0 and t["peersConnected"] == 0 and t.get("metadataPercentDone", 0) == 0) else ""
    print(f"{t['id']:3d} {st:15s} {done:>6} {meta:>5} {down:>8} {peers:>5} {qpos:>4}  {name}{marker}")

# --- Summary ---
print(f"\nTotal: {len(data['arguments']['torrents'])} torrents")
c = Counter(t["status"] for t in data["arguments"]["torrents"])
for st_code, cnt in sorted(c.items()):
    print(f"  {STATUS_NAMES.get(st_code, '?'+str(st_code))}: {cnt}")

# Highlight stuck torrents
stuck = [
    t for t in data["arguments"]["torrents"]
    if t["status"] == 4 and t["rateDownload"] == 0
    and t["peersConnected"] == 0
    and t.get("metadataPercentDone", 0) == 0
]
if stuck:
    print(f"\n⚠️  {len(stuck)} stuck torrent(s) occupying download queue slots (Status=Downloading, 0 peers, 0 metadata):")
    for t in stuck:
        print(f"     ID {t['id']}: {t.get('name', '?')[:60]}")
    print("   → Remove or stop them to free queue slots")

# --- Session info ---
s = session["arguments"]
print(f"\nQueue settings:")
print(f"  download-queue-size:    {s.get('download-queue-size', '?')}")
print(f"  download-queue-enabled: {s.get('download-queue-enabled', '?')}")
print(f"  queue-stalled-minutes:  {s.get('queue-stalled-minutes', '?')}")
print(f"  speed-limit-down:       {s.get('speed-limit-down', '?')} KB/s (enabled: {s.get('speed-limit-down-enabled', '?')})")
