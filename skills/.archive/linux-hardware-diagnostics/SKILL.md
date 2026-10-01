---
name: linux-hardware-diagnostics
description: "Diagnose undetected USB/hardware devices on Linux."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [hardware, usb, diagnostics, troubleshooting, linux, kernel]
    related_skills: [systematic-debugging]
---

# Linux Hardware Diagnostics

## When to Use

Use when a hardware device (USB pendrive, external disk, peripheral, PCI device) is not visible in the system, not detected, or not working as expected after connecting.

## Diagnostic Pipeline: USB Device Not Detected

Follow these steps in order. Stop when you have enough evidence to identify the issue.

### 1. Check if the device appears at the USB level

```bash
lsusb
```

- **Device present?** → Note vendor/product ID, bus, and device number
- **Not present?** → Hardware problem — dead device, bad cable, dead port, or USB controller issue

### 2. Check kernel messages for USB/storage events

```bash
sudo dmesg | grep -i -E 'usb|sd[a-z]|mmc|nvme'
```

What to look for:
- `New USB device found` — device enumerated, vendor/product shown
- `USB disconnect` — device disconnected (physical, power, or electrical)
- `sdX: sdc1 sdc2` — partitions detected successfully
- `No Caching mode page found` — common and harmless
- `reset high-speed USB device` — device reconnected or port reset
- **No USB messages at all** → device was never seen by the USB controller

### 3. Check block devices

```bash
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,LABEL,MODEL,TRAN
```

- Is the device listed as a `disk`? What size shows? (**0B** = no media or not responding)
- Are there partitions? If no partitions despite known data → device was detected but couldn't read the media

### 4. Check USB topology

```bash
lsusb -t
```

Shows the USB tree: which port each device is on, speed (480M = USB 2.0, 5000M = USB 3.0), and driver. Use this to identify port conflicts or unavailable ports.

### 5. Check device nodes

```bash
ls -la /dev/sd*
```

- Device in `lsusb` but **no `/dev/sdX` node** → driver didn't bind (missing module, device rejected)
- Device node exists but reports **0B** → media detection failure

### 6. Check USB power management

```bash
cat /sys/bus/usb/devices/*/power/control
```

- `auto` → device can be suspended by kernel (power-save)
- `on` → always powered
- Some ports with power-save enabled may prevent enumeration of certain devices

### 7. Port isolation test

- Try a **different physical USB port**, preferably on a different bus
- Try a **different known-good device** in the same port (isolates port vs device fault)
- Use a **direct port**, not through a hub
- Reset the USB storage subsystem: `sudo modprobe -r usb_storage && sudo modprobe usb_storage`

### 8. Diagnosing Physical Port Failure (Dead in All OSes)

When a specific physical USB port works in no OS (Linux, Windows, etc.), the issue is **hardware**, not software configuration. No software command can permanently disable a USB port across OS reboots.

**Confirm it's the port, not the device:**
```bash
# Test a known-good device in the suspect port
# Test the suspect device in a known-good port
```

**Check port status in sysfs:**
```bash
# All USB controllers should show authorized=1
cat /sys/bus/usb/devices/usb*/authorized

# Check power management state
for f in /sys/bus/usb/devices/*/power/control; do echo "$f => $(cat $f)"; done

# Look for explicitly disabled ports (should return nothing)
grep -r "" /sys/bus/usb/devices/usb*/port*disabled 2>/dev/null
```

**Check kernel for port-specific errors:**
```bash
sudo dmesg | grep -i -E 'usb|xhci|over.current|disabled|fail|error'
```

Red flags in dmesg:
- `over-current` — electrical short or PTC fuse tripped
- `port disabled` — controller disabled the port due to fault
- `reset high-speed USB device number N` repeated 5+ times — power/contact instability
- `USB disconnect, device number N` immediately after connect — insufficient power

**Map physical ports to topology:**

1. Identify USB controllers: `lspci | grep -i usb`
2. List buses and port count: `lsusb -t`
3. Find Type-C port binding: `ls -la /sys/class/typec/` — each Type-C port pairs a USB 2.0 lane and a USB 3.x lane from possibly different controllers
4. Check which physical ports are Type-C vs USB-A: Type-C ports appear under the Thunderbolt/USB-C controller; USB-A ports appear under the main xHCI controller

**Common hardware failures:**

| Symptom | Likely Cause |
|---------|-------------|
| Port dead in all OSes, no dmesg events at all | Bent pin inside port, solder fracture, open circuit |
| Port dead, no dmesg, but other ports on same controller work | Individual port failure (pin/PTC/trace) |
| Device detected then immediately disconnects | PTC fuse tripped (over-current protection), insufficient power |
| Type-C port dead for USB 2.0 devices but 3.0 works (or vice versa) | One of the two differential pairs failed — common on physically damaged Type-C ports |
| Intermittent connection, works when cable held at angle | Solder crack on connector joint |

**Physical inspection (last resort):**
- Shine a light inside the USB port and look for bent/broken pins
- A bent pin inside the port can short VBus to ground, tripping over-current protection
- For Type-C: inspect inside both sides of the receptacle — the tongue can break

**Power drain reset:**
```bash
# Discharge residual capacitance in USB controller
# 1. Shut down
# 2. Unplug AC power
# 3. Remove battery (if removable)
# 4. Hold power button 30s
# 5. Reconnect power and boot
```
This fully discharges the USB controller's capacitors, which can clear stuck fault states on some hardware.

## Interpretation of Findings

| Symptom | Likely Cause |
|---------|-------------|
| Not in `lsusb`, no dmesg events | Dead device, dead port, no power, bad cable |
| In `lsusb`, no kernel storage events | Driver issue, unsupported device, USB controller fault |
| In `lsusb`, detected as `sdX` but 0B | Media read failure, bad flash, unsupported filesystem |
| Detection followed by `USB disconnect` within seconds | Loose connection, power starvation, device fault |
| Multiple `reset high-speed USB` events | Port power instability, hub issue |
| Works on one port but not another | Port-specific failure or bus issue |

## Common Fixes

- **Reseat** — unplug and wait 3 seconds (drains residual power) before reconnecting
- **Different port** — especially a different bus (USB 2.0 vs USB 3.0)
- **Direct connection** — avoid USB hubs for diagnostics
- **Reload storage driver** — `sudo modprobe -r usb_storage && sudo modprobe usb_storage`
- **Hard reboot** — if the USB controller is in a bad state (rare)

## Reference Files

- `references/usb-diagnostic-example.md` — walkthrough of a pendrive that disappeared after disconnect
- `references/thinkpad-t480-usb-topology.md` — complete USB port mapping for Lenovo ThinkPad T480 (useful as a template for any laptop USB topology analysis)

## Pitfalls

- **Always verify with `lsusb` first** — do not assume detection just because the device is plugged in
- **USB 3.0 ports may not detect USB 1.1/2.0 devices** — try a USB 2.0 port for legacy or low-power devices
- **Powered hubs** — if a device draws more current than the hub provides, it will disconnect repeatedly
- **USB-C to USB-A adapters** — some are charge-only (no data lines)
- **`dmesg` buffer can roll** on long-running systems — use `sudo dmesg -T` for timestamps, or `sudo dmesg -c` to clear the buffer before plugging the device for a clean capture
- **Identify port conflicts** — check `lsusb -t` to see if the expected physical port is already occupied by another device (e.g., mouse dongle took the port after a disconnect)
- **Cross-OS testing isolates hardware vs software** — if a USB port fails in Windows too, no Linux driver tweak, kernel module reload, or config change will fix it. The port is physically damaged or the controller has a hardware fault.
- **USB-C port failure can be partial** — a Type-C port has separate USB 2.0 (D+/D-) and USB 3.0/4.0 (SSTX/SSRX) signal pairs. Physical damage can knock out one but not the other. Test with both a USB 2.0 device (mouse, keyboard) and a USB 3.0 device (external SSD) to assess scope.
- **A hub plugged into a failing port can appear healthy** — if an external hub is connected to a marginal port, the hub itself may enumerate but devices plugged into it may disconnect randomly. Remove all hubs and test directly.