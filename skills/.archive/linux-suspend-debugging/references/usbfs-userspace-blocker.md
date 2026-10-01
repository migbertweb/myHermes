# `usbfs` Userspace Device Blocking Suspend

Real-world case on CachyOS/Arch (2026-07-26). A fingerprint reader (Synaptics `06cb:009a`) on `usb1-port9` blocked both `deep` and `s2idle` suspend.

## Symptom

`systemctl suspend` returns to prompt immediately. Journal shows:

```
jul 26 17:45:13 kernel: usb usb1-port9: device 1-9 not suspended yet
jul 26 17:45:14 kernel: usb usb1: PM: dpm_run_callback(): usb_dev_suspend returns -16
jul 26 17:45:14 kernel: usb usb1: PM: failed to suspend async: error -16
jul 26 17:45:14 kernel: PM: Some devices failed to suspend, or early wake event detected
jul 26 17:45:15 kernel: PM: suspend entry (s2idle)
jul 26 17:45:15 kernel: usb usb1-port9: device 1-9 not suspended yet
jul 26 17:45:15 kernel: usb usb1: PM: dpm_run_callback(): usb_dev_suspend returns -16
jul 26 17:45:15 kernel: PM: suspend exit
```

Key signals:
- Repeated `device N-N not suspended yet` for the same port
- Error `-16` (`-EBUSY`) on `usb_dev_suspend`
- Same error in both `deep` and `s2idle` — not a sleep-state issue

## Root Cause

The device was using **`usbfs`** driver — raw userspace access via libusb. The daemon (`open-fprintd`) held the device open and the kernel couldn't suspend the USB controller while it was claimed.

### Nuance: python-validity + power/control=on

On Synaptics readers (e.g. ThinkPad T480, `06cb:009a`), `python-validity` is a **userspace kernel driver** that:
1. Talks to the fingerprint sensor via libusb (`usbfs`)
2. Keeps the device at `power/control=on` (never auto-suspend)
3. The USB bus sees the port as always-active → `-EBUSY (-16)` on `dpm_run_callback`

Even with `open-fprintd` stopped, `python3-validity.service` can re-claim the device (auto-restart loop in systemd). The device stays at `power/control=on` because `python-validity` never releases the libusb handle. This means **stopping the service alone may not work** — see Option C below.

**USB topology:**
```
Bus 001 Port 009: Dev 006, Driver=usbfs
  ID 06cb:009a Synaptics Metallica MIS Touch Fingerprint Reader
```

Detection:
```bash
lsusb -t                    # shows driver=usbfs
cat /sys/bus/usb/devices/1-9/driver  # → "usb" (usbfs internal)
```

## Culprit Process

`open-fprintd.service` — running as root, using Python with libusb bindings:

```
root 13833 /usr/bin/python3 /usr/lib/open-fprintd/open-fprintd --debug
```

**Note:** libusb-based daemons do NOT show up in `lsof /dev/bus/usb/001/006` because they open the device via libusb's internal handle, not by opening the `/dev/bus/usb/` node directly. Use `ps aux | grep -i fprint` or `systemctl status open-fprintd.service` instead.

## Quick Test

```bash
sudo systemctl stop open-fprintd.service
systemctl suspend           # should work now
```

## Permanent Fix

### Option A: systemd-sleep hook (service stays installed)

Create `/usr/lib/systemd/system-sleep/fprintd-suspend` (executable, root-owned, no extension):

```bash
#!/bin/bash
case $1/$2 in
  pre/*)
    systemctl stop open-fprintd.service 2>/dev/null || true
    systemctl stop python3-validity.service 2>/dev/null || true
    ;;
  post/*)
    systemctl start open-fprintd.service 2>/dev/null || true
    systemctl start python3-validity.service 2>/dev/null || true
    ;;
esac
```

```bash
sudo chmod 755 /usr/lib/systemd/system-sleep/fprintd-suspend
```

### Option B: Mask the service (prevents restart)

If the service auto-restarts (`Restart=always` in unit), stopping alone is not enough:

```bash
sudo systemctl mask open-fprintd.service
sudo systemctl mask python3-validity.service
```

### Option C: Remove packages entirely (nuclear — works when others don't)

On Synaptics readers (T480, `06cb:009a`), `python-validity` is a **low-level USB driver** that activates and claims the sensor via libusb. Even with the service stopped, the kernel module and device state keep `power/control=on`, preventing USB bus suspend. Removing the entire stack is the definitive fix:

```bash
sudo pacman -Rns python-validity open-fprintd fprintd-clients-git libfprint python-pyusb
```

This also removes `python3-validity-suspend-hotfix.service` and udev rules that may conflict with other suspend fixes.

**Trade-off:** You lose fingerprint login entirely. Restore by reinstalling the packages (`sudo pacman -S python-validity open-fprintd`).

## Other Potential libusb Daemons

| Daemon | Device | Detection |
|--------|--------|-----------|
| `open-fprintd` | Fingerprint readers | `ps aux \| grep fprint` |
| `fprintd` | Fingerprint readers (older) | `systemctl status fprintd` |
| libusb-based HID tools | Custom input devices | `lsusb -t \| grep usbfs` |
