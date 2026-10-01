---
name: tuya-device-management
description: Use when managing Tuya devices. Local scan and control.
tags: [iot, tuya, tinytuya, home-automation]
---

# Tuya Device Management

Workflow for discovering and controlling Tuya smart devices using the `tinytuya` Python library in a local network environment.

## Standard Workflow
1. **Network Scan**: Use `tinytuya.deviceScan()` to find devices and their current local IP addresses.
2. **Verification**: Confirm the device ID and version match the known configuration.
3. **Control**: Use `tinytuya.OutletDevice` (or appropriate device class) to send commands.

## Troubleshooting & Pitfalls

### Network Error 901 (Unable to Connect)
**Symptom**: Device is detected via UDP scan and responds to ICMP pings, but TCP connection attempts (status/control) fail with error `901`.
**Cause**: Often happens after a router change or gateway update. The device's network stack enters an inconsistent state where it responds to low-level network probes but rejects control sockets.
**Solution**: Perform a **Physical Power-Cycle**. Unplug the device from the wall outlet, wait 5 seconds, and plug it back in. This resets the network stack and clears hung sockets.

### IP Address Drift
Devices often change IPs after a router reboot. Always perform a fresh scan before updating control scripts to avoid hardcoding stale IPs.

## Technical References
- **Default Port**: 6668 (TCP)
- **Scan Method**: UDP Broadcast
- **Required Data**: Local IP, Device ID, Local Key, Version.
