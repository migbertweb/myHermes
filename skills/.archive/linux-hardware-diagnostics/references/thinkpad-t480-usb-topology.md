# ThinkPad T480 — USB Topology Reference

## Laptop: Lenovo ThinkPad T480 (20L6S3U003)

## USB Controllers

| PCI Address | Controller | Chipset | Buses | Physical Ports |
|---|---|---|---|---|
| `00:14.0` | Intel Sunrise Point-LP USB 3.0 xHCI | 8086:9d2f | Bus 001 (USB2, 12 ports) + Bus 002 (USB3, 6 ports) | USB-A 2.0 + USB-A 3.0 |
| `3c:00.0` | Intel JHL6240 Thunderbolt 3 USB 3.1 (Alpine Ridge LP) | 8086:15c1 | Bus 003 (USB2, 2 ports) + Bus 004 (USB3, 2 ports) | USB-C (x2) |

## Physical Port Layout

### Left Side
- **USB-C / Thunderbolt 3** — nearest to HDMI port. Type-C port0 in sysfs. Combines Bus 003 port 1 (USB2 lane) + Bus 004 port 1 (USB3 lane).
- **USB-C (data+charge only, no Thunderbolt)** — second from left. Type-C port1 in sysfs. Combines Bus 003 port 2 (USB2 lane) + Bus 004 port 2 (USB3 lane).
- **USB-A 3.0 (always-on charging marked with ⚡)** — leftmost USB-A port. On Bus 001 + Bus 002 of the Intel controller.
- **USB-A 3.0** — next to the always-on port. On Bus 001 + Bus 002 of the Intel controller.

### Right Side
- **USB-A 2.0** — near the Ethernet port. On Bus 001 of the Intel controller only (USB 2.0 only, no superspeed pair).

## Internal Devices (Bus 001)

| Port | Device | Driver |
|---|---|---|
| `1-7` | Bluetooth (Intel 8087:0a2b) | btusb |
| `1-8` | Camera (Bison 5986:2113) | uvcvideo |
| `1-9` | Fingerprint reader (Synaptics 06cb:009a) | [none] |

## Typical External Hub Topology (USB-C port)

When a USB-C hub is plugged into the left USB-C (port0):

```
Bus 003 (USB2) / Bus 004 (USB3) — Type-C port0
  └── External Hub (QinHeng 1a86:809d, 6 ports)
       ├── Port 1: Generic storage / pendrive
       ├── Port 2: Secondary hub (Huasheng 214b:7250, 4 ports)
       │    └── Port 1: ESP32 JTAG (303a:1001)
       ├── Port 3: (empty)
       ├── Port 4: Mouse receiver (Maxxter/Telink 248a:fa02)
       ├── Port 5: USB LAN (QinHeng 1a86:5394)
       └── Port 6: (empty)
```

## Diagnostic Commands for This Model

```bash
# Show both controllers
lspci | grep -i usb

# Show Type-C port mapping
ls -la /sys/class/typec/

# Check Type-C port details
for p in /sys/class/typec/*/; do
  echo "=== $(basename $p) ==="
  cat "$p/data_role" 2>/dev/null
  cat "$p/power_role" 2>/dev/null
  cat "$p/usb_power_delivery" 2>/dev/null
done
```

## Known Quirks

- **USB-C port0** (Thunderbolt) and **port1** (data-only) are NOT interchangeable for Thunderbolt devices — only port0 supports Thunderbolt.
- The **USB-A always-on port** stays powered when the laptop is off (useful for charging). If it stops working entirely, check for a BIOS setting ("Always On USB").
- The **fingerprint reader** (1-9) may show multiple `reset full-speed USB device` entries in dmesg — harmless, it's a known quirk of the Synaptics MIS sensor on this chipset.
- Internal Bluetooth and Camera share the Intel controller bus with external USB-A ports. If an external device causes over-current, it can take down the internal devices too.
