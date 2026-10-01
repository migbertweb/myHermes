---
name: linux-suspend-debugging
description: "Use when Linux suspend fails. Checks logs, wakeup, freeze."
version: 1.6.0
author: Migbert
---

# Linux Suspend Debugging

Systematic approach to diagnosing why a Linux machine won't suspend (or wakes up immediately). Covers Arch, CachyOS, and systemd-based distros.

## References

- `references/diagnosis-flow.md` — Full diagnostic procedure: what logs to check, what each error means, and the two-part problem pattern (freeze failure + immediate wakeup).
- `references/usb-c-pd-wakeup.md` — USB-C PD (ucsi-source-psy) wakeup: identifying via event_count, runtime and persistent fixes, and additional wakeup sources to check.
- `references/usbfs-userspace-blocker.md` — libusb/usbfs userspace daemon (e.g. fingerprint reader) blocking suspend with `-EBUSY`.
- **NEW** Section D: PCIe Root Port / Thunderbolt Controller Wakeup — included inline in SKILL.md (no separate ref file).

## When to Use

- `systemctl suspend` does nothing, returns instantly, or the system wakes up right after
- Journal shows `Failed to put system to sleep. System resumed again: Device or resource busy`
- `systemd-suspend.service` exits with status 1/FAILURE
- `Freezing user space processes failed` in kernel logs
- Laptop doesn't sleep when lid is closed

## Diagnostic Flow (Quick Start)

### 1. Check system power capabilities

```bash
cat /sys/power/state          # available sleep states (freeze, mem, disk)
cat /sys/power/mem_sleep      # which mem variant is default (s2idle vs deep)
cat /sys/power/disk           # hibernate modes
```

### 2. Check suspend logs

```bash
# Last boot's suspend attempts
journalctl --boot=-1 -g 'suspend|PM:.*error|PM:.*fail|wakeup'

# systemd-sleep service status
journalctl -u systemd-suspend.service -u systemd-hibernate.service -u systemd-sleep.service

# Live boot
journalctl -g 'refusing to freeze'
```

### 2.5 Enable verbose device suspend logs

If the error is `Failed to put system to sleep. System resumed again: Device or resource busy` but kernel logs don't say which device, enable PM debug messages:

```bash
echo 1 | sudo tee /sys/power/pm_debug_messages
```

Then re-run suspend. The next attempt will log *which specific device* returned `-EBUSY` (-16), e.g.:

```
usb usb1: PM: dpm_run_callback(): usb_dev_suspend returns -16
usb usb1: PM: failed to suspend async: error -16
PM: Some devices failed to suspend, or early wake event detected
```

Without this, the kernel only says `PM: Some devices failed to suspend` with no device name. Check `/sys/power/pm_print_times`, `pm_print_state`, and `pm_trace` as alternatives if the kernel supports them.

### 3. Identify root cause

#### A. Process Freeze Failure

The kernel logs which process refuses to freeze (check with `-B5 -A5` context around `refusing to freeze`):

```
task:<name> state:D stack:0 pid:<N> ...
Call Trace:
  fuse_statfs → __fuse_simple_request → schedule
```

- **state:D** = uninterruptible sleep (disk/IO wait). These tasks **cannot freeze**.
- Common culprits: FUSE mounts (rclone, sshfs), NFS/CIFS network mounts, stuck NFS locks.
- The kernel waits 20s, then gives up.

**Fix:** Stop the offending service BEFORE suspend via a systemd-sleep hook.

#### B. Immediate Wakeup

Check wakeup sources:

```bash
# ACPI wakeup devices and their S-state
cat /proc/acpi/wakeup

# Wakeup event counts (non-zero = this device has triggered wake)
grep . /sys/class/wakeup/*/event_count | sort -t: -k2 -rn

# USB device wakeup
for f in /sys/bus/usb/devices/*/power/wakeup; do
  dev=$(echo $f | cut -d/ -f6)
  echo "$dev => $(cat $f 2>/dev/null)"
done
```

**Mapping wakeupN to device names:**
```bash
for w in /sys/class/wakeup/wakeup*; do
  name=$(cat $w/name 2>/dev/null)
  ev=$(cat $w/event_count 2>/dev/null)
  echo "$(basename $w): $name ($ev events)"
done | sort
```

**Fix options (in order of precision):**
1. **udev rule** per device: disable wakeup for a specific USB vendor:product
2. **Manual disable**: `echo disabled > /sys/bus/usb/devices/<id>/power/wakeup`
3. **Disable entire controller**: echo `XHC` > /proc/acpi/wakeup (disables all USB wake)

#### C. `usbfs` Userspace Device (libusb) Blocking Suspend

A USB device using the **`usbfs`** driver (raw libusb userspace access) blocks suspend even when wakeup is disabled. The kernel returns `-EBUSY` (`-16`) because the userspace daemon hasn't released the device.

**Symptom in kernel log:**
```
usb usb1-port9: device 1-9 not suspended yet
usb usb1: PM: dpm_run_callback(): usb_dev_suspend returns -16
usb usb1: PM: failed to suspend async: error -16
PM: Some devices failed to suspend, or early wake event detected
```

This fires for **both** `deep` and `s2idle` — the device simply won't yield.

**Common culprits:**
- **Fingerprint readers** — `open-fprintd`, `fprintd` (Synaptics, Elan, etc.)
- Any daemon using raw libusb: biometric scanners, custom HID tools, 3D printers

**Detection:**
```bash
# 1. Identify the device — match the port number from the error
lsusb -t | grep -B2 "Port 009"
cat /sys/bus/usb/devices/<N>/driver  # should show 'usb' (usbfs)

# 2. Find the daemon — libusb daemons don't show in lsof /dev/bus/usb/*
ps aux | grep -iE "fprint|open-fprint|libusb|fingerprint"
systemctl list-units --all | grep -iE "fprint|finger"

# 3. Confirm by stopping the service and trying suspend
sudo systemctl stop open-fprintd.service
systemctl suspend
```

**Fix:** systemd-sleep hook — stop the daemon `pre/`, restart `post/`.

#### D. PCIe Root Port / Thunderbolt Controller Wakeup

Un PCIe root port conectado a un **Thunderbolt controller** (común en laptops Intel con USB-C/Thunderbolt) puede despertar el sistema inmediatamente desde S3 **incluso cuando XHC (USB controller) tiene wakeup disabled**. El controlador Thunderbolt está en su propia jerarquía PCIe y puede emitir un PME (PCI Power Management Event) que bypasea la configuración ACPI de XHC.

**Síntoma clave:** Suspend funciona en Windows pero no en Linux → drivers de Windows gestionan D3cold en el Thunderbolt; Linux lo deja activo.

**Detección:**

```bash
# 1. PCI devices con wakeup y power control
for d in /sys/bus/pci/devices/*/power/wakeup; do
  echo "$d: $(cat $d 2>/dev/null)"
done

for d in /sys/bus/pci/devices/*/power/control; do
  echo "$d: $(cat $d 2>/dev/null)"
done

# Buscar devices con control=on + wakeup=enabled simultáneamente

# 2. Identificar qué hardware está en esas direcciones PCI
lspci -vnn | grep -E '<address>'

# 3. ACPI wakeup — buscar RP (Root Ports) enabled
cat /proc/acpi/wakeup | grep '^RP'

# 4. mapear wakeupN a nombre de dispositivo
for w in /sys/class/wakeup/wakeup*; do
  name=$(cat $w/name 2>/dev/null)
  ev=$(cat $w/event_count 2>/dev/null)
  echo "$(basename $w): $name ($ev events)"
done | sort
```

**Sospechosos frecuentes en Intel Kaby Lake / Sunrise Point-LP (ThinkPad T480):**

| ACPI | PCI address | Dispositivo |
|------|-------------|-------------|
| RP09 | 00:1d.0 → 04:00.0 | Thunderbolt 3 Alpine Ridge LP (JHL6240) bridge |
| — | 04:00.0 | Thunderbolt 3 bridge (downstream) — **wakeup=enabled** afecta S3 |
| — | **06:00.0** | **Thunderbolt NHI** (Non-Host Interface) — si wakeup=enabled, despierta al instante desde S3 |
| — | **3c:00.0** | **Thunderbolt USB 3.1 controller** — error `xHC error in resume, USBSTS 0x401` al despertar; puede tener `power/control=on` |
| RP11 | 00:1d.2 | WiFi root port (PME desde la NIC) |
| RP05 | 00:1c.4 | NVMe root port (menos común, S4) |

Las RP suelen aparecer como `S4 *enabled` en `/proc/acpi/wakeup`, pero el sysfs PCI las tiene `wakeup=enabled` a nivel de runtime, lo que sí afecta S3.

**Diagnóstico de Thunderbolt como wake source:**

```bash
# Verificar wakeup en la jerarquía completa del Thunderbolt
for pci in /sys/bus/pci/devices/0000:04:00.0 \
           /sys/bus/pci/devices/0000:06:00.0 \
           /sys/bus/pci/devices/0000:3c:00.0; do
  echo "$pci/wakeup: $(cat $pci/power/wakeup 2>/dev/null)"
  echo "$pci/control: $(cat $pci/power/control 2>/dev/null)"
done

# Ver el error típico al despertar (no causa, pero confirma TBT involucrado)
sudo journalctl -b -k --no-pager | grep "xHC error in resume, USBSTS 0x401"
```

**Fix inmediato (prueba):**

```bash
# Toggle ACPI wakeup (echo del mismo nombre togglea)
echo RP09 | sudo tee /proc/acpi/wakeup
echo RP11 | sudo tee /proc/acpi/wakeup

# Deshabilitar PCI wakeup — cubrir TODA la jerarquía Thunderbolt
for pci in 0000:00:1d.0 0000:04:00.0 0000:06:00.0 0000:3c:00.0; do
  echo disabled | sudo tee /sys/bus/pci/devices/$pci/power/wakeup
done
```

**Fix persistente:** systemd service que ejecuta los comandos anteriores en cada boot, o udev rule para ATTR{power/wakeup} sobre la ruta PCI.

**Relación con USB `power/control=on`:** Múltiples dispositivos USB con `power/control = on` (mouse receiver, USB ethernet, ESP32) mantienen el subsistema USB activo, lo que a su vez permite que el TBT controller sensé actividad y dispare un wake event. No siempre es la causa raíz, pero contribuye.

---

#### E. USB Device `power/control = on` Blocking Suspend

A USB device with `power/control` set to `on` forces the kernel to keep the device fully powered. When the suspend cycle tries to transition the USB bus, the driver refuses because the device is locked in an active power state, returning `-EBUSY`.

**Symptom in kernel log (identical to libusb case):**
```
usb usb1: PM: dpm_run_callback(): usb_dev_suspend.llvm.4760064312927422089 returns -16
usb usb1: PM: failed to suspend async: error -16
PM: Some devices failed to suspend, or early wake event detected
```

Like the usbfs case, this fires for **both** `deep` and `s2idle` — it's a device-level lock, not state-dependent.

**Detection:**
```bash
# List ALL USB devices with their power/control status (catches nested paths)
for d in /sys/bus/usb/devices/*/power/control; do
  dev=$(echo $d | cut -d/ -f6)
  echo "$dev => $(cat $d 2>/dev/null)"
done | sort -t: -k2

# Devices showing "on" are blocking suspend (want "auto").
# Some devices nest deeper than usb1/*/ — e.g. 1-4.2.3, 1-4.4, 1-4.5 — 
# so use /*/ not usb1/*/ to catch the full tree.
```

**Common culprits set to `on`:**
- **Mass storage devices** (USB disks, pendrives) — userspace tools or kernel config often pin them `on`
- **Bluetooth adapters** — some btusb implementations force active power
- **Fingerprint readers** — driver holds the device active

**Immediate fix:**
```bash
echo auto > /sys/bus/usb/devices/usb1/<N>/power/control
```

**Persistent fix — udev rule at `/etc/udev/rules.d/99-suspend-fix.rules`:**
```udev
ACTION=="add", SUBSYSTEM=="usb", KERNEL=="1-1", ATTR{power/control}="auto"
ACTION=="add", SUBSYSTEM=="usb", KERNEL=="1-7", ATTR{power/control}="auto"
```
Replace `KERNEL` with the specific USB port path that's problematic. Then reload:
```bash
sudo udevadm control --reload-rules
```

**Verification:**
```bash
cat /sys/bus/usb/devices/usb1/<N>/power/control  # should show "auto"
systemctl suspend
```

#### F. xHCI Controller Refusing to Suspend (root hub `-EBUSY`)

When every debug step passes (devices deauthorized, wakeup disabled, no process freeze) but `usb usb1` / `usb usb2` still returns `-EBUSY` (`-16`) on `dpm_run_callback(): usb_dev_suspend` — the **xHCI controller itself** can't enter a low-power state. This typically manifests even **after** setting all `power/control` to `auto`, deauthorizing devices, and disabling wakeup.

**Common scenarios:**
- Intel Sunrise Point-LP (Kaby Lake/7th gen PCH) — a well-known chipset issue
- The controller has `runtime_suspended_time: 0` — has **never** runtime-suspended since boot
- Suspend works on Windows because the Intel driver manages D3cold properly

**Diagnosis:**

```bash
# Check if xHCI has EVER runtime-suspended
cat /sys/bus/pci/devices/0000:00:14.0/power/runtime_suspended_time
# If 0 — controller has never entered runtime suspend

# Confirm the xHCI controller PCI address
lspci | grep -i 'xhci\|USB.*Controller' | head -5
```

**Fix technique: PCI driver unbind/rebind**

If the `xhci_hcd` and `xhci_pci` modules are **built into the kernel** (`modprobe -r xhci_pci` returns `FATAL: Module xhci_pci is builtin`), you cannot remove them. Instead, **unbind the driver from the PCI device** before suspend:

```bash
# Pre-suspend: unbind xhci_hcd from the PCI device
echo -n "0000:00:14.0" > /sys/bus/pci/drivers/xhci_hcd/unbind

# Post-resume: rebind to restore USB devices
echo -n "0000:00:14.0" > /sys/bus/pci/drivers/xhci_hcd/bind
```

This physically removes the USB controller (Buses 001 and 002 disappear) before the kernel tries to suspend devices, and restores it on resume. The Thunderbolt USB controller (if present on the same PCI tree) has its own xHCI device and is NOT affected.

**Verification:**

```bash
# Before unbind — buses 001 and 002 present
lsusb -t

# After unbind — only Thunderbolt USB buses remain
lsusb -t
# Expected: Bus 003, Bus 004 still there; Bus 001, Bus 002 gone

# After rebind — everything back
lsusb -t
```

**Permanent fix: systemd-sleep hook:**

Create `/usr/lib/systemd/system-sleep/xhci-suspend-fix` (executable, no extension):

```bash
#!/bin/bash
# Fix xHCI controller suspend on Intel Sunrise Point-LP
# Unbinds the xhci_hcd driver before suspend, rebinds after resume

XHCI_PCI="0000:00:14.0"
DRIVER="/sys/bus/pci/drivers/xhci_hcd"

case "$1" in
    pre)
        if [ -f "$DRIVER/unbind" ]; then
            echo -n "$XHCI_PCI" > "$DRIVER/unbind" 2>/dev/null
        fi
        ;;
    post)
        if [ -f "$DRIVER/bind" ]; then
            echo -n "$XHCI_PCI" > "$DRIVER/bind" 2>/dev/null
        fi
        ;;
esac
```

**Alternative: force D3hot via setpci** (works but less clean):

```bash
# Check current power state
lspci -s 00:14.0 -vv | grep "Status: D"

# Force D3hot — disconnects USB devices
setpci -s 00:14.0 CAP_PM+4.w=0x03

# Restore to D0 on resume
setpci -s 00:14.0 CAP_PM+4.w=0x00
```

Prefer the unbind/rebind method since it triggers proper driver re-initialization on resume, while `setpci` leaves the driver unaware of the power state change.

**When to use this fix:**
- `modprobe -r xhci_pci` is unavailable (module built-in)
- `pm_debug_messages` confirms the blocker is the root hub (`usb1`, `usb2`), NOT a specific child device
- Devices have already been set to `auto` for `power/control` and deauthorization didn't help
- The controller shows `runtime_suspended_time: 0` (never suspended)

### Confirmed Working Fix: ThinkPad T480

The T480 (Sunrise Point-LP / Kaby Lake) has a **compound** suspend problem requiring fixes at both the USB device layer and the PCIe/Thunderbolt layer:

| Layer | Symptom | Fix |
|-------|---------|-----|
| USB device | `usb usb1: dpm_run_callback() returns -16 (EBUSY)` | Remove fingerprint stack (`python-validity` + `open-fprintd`) — see `usbfs-userspace-blocker.md` Option C |
| PCIe / Thunderbolt | `ACPI: PM: Waking up from S3` immediately + `xHC error in resume, USBSTS 0x401` | Disable XHC ACPI wakeup + udev rule for Intel xHCI PCI device |

**The three-part fix that works:**

```bash
# 1. Remove fingerprint packages (kills the -EBUSY blocker)
sudo pacman -Rns python-validity open-fprintd fprintd-clients-git libfprint python-pyusb

# 2. Disable XHC wakeup at ACPI level (toggle: echo same name toggles)
echo XHC | sudo tee /proc/acpi/wakeup

# 3. Persist via udev — /etc/udev/rules.d/99-disable-wakeup.rules
# ACTION==\"add\", SUBSYSTEM==\"pci\", ATTRS{class}==\"0x0c0330\", ATTR{power/wakeup}=\"disabled\"
```

After all three, `systemctl suspend` enters `deep` S3 and stays there until LID open or power button. Verify with `cat /proc/acpi/wakeup | grep XHC` → `XHC S3 *disabled`.

### 4. Fix: systemd-sleep hooks

Create a script at `/usr/lib/systemd/system-sleep/<name>` (executable, no extension):

```bash
#!/bin/bash
case $1/$2 in
  pre/*)
    systemctl --user -M migbert@ stop rclone-gdrive.service 2>/dev/null || true
    fusermount -uz /home/migbert/Gdrive 2>/dev/null || true
    ;;
  post/*)
    systemctl --user -M migbert@ start rclone-gdrive.service 2>/dev/null || true
    ;;
esac
```

Systemd runs these hooks automatically — no service enable needed.

### 5. Fix: udev wakeup rule

Permanently disable wakeup for a specific USB device:

```udev
ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="248a", ATTRS{idProduct}=="fa02", ATTR{power/wakeup}="disabled"
```

```bash
sudo udevadm control --reload-rules
sudo sh -c 'echo disabled > /sys/bus/usb/devices/1-4.4/power/wakeup'
```

## Verification

```bash
journalctl -f -u systemd-suspend.service &
systemctl suspend
```

Check for:
- No `Failed to freeze unit 'user.slice'`
- No `System resumed again: Device or resource busy`
- Exit code 0 on systemd-suspend.service

## Pitfalls

1. **⚠️ USER CONSENT FIRST**: This skill describes fixes that modify system files, ACPI settings, and boot configuration. **Do NOT apply any permanent fix without the user's explicit request.** Start with READ-ONLY diagnosis. Present findings. Let the user decide what to fix. Making unsolicited system changes will frustrate the user and you'll have to revert everything.

2. **Two-part problem**: Fixing only the freeze or only the wakeup still leaves suspend broken.

3. **sudo tee/piped commands hang with fingerprint auth**: If `sudo` has `pam_fprintd.so` (fingerprint first) in its PAM stack, piped commands like `echo value | sudo tee /sys/...` hang waiting for fingerprint input. Alternatives:
   - `printf 'password\n' | sudo -S command` — bypasses the PAM conversation
   - `sudo sh -c 'echo ... > /sys/...'` — direct shell redirection avoids tee
   - `su -c` if root password is available

4. **systemd-sleep hook**: No file extension. Must be executable. Lives in `/usr/lib/systemd/system-sleep/`.

5. **udev rule on `add`**: Only applies at connect time. For plugged devices, apply manually.

6. **FUSE + D state**: FUSE kernel threads enter D state on network loss. Hook must stop service *before* freeze.

7. **`fusermount -uz`**: Always use lazy unmount in pre-suspend hooks.

8. **Kernel context**: grep with `-B5 -A5` around `refusing to freeze` to see the offending task name.

9. **`journalctl -B`**: On some distros (Arch/CachyOS), `-B` is not a valid option. Use `grep -B5 -A5` piped from `journalctl` output instead.

10. **Wakeup event_count persists across attempts**: An event_count of 1 may be from a previous suspend attempt, not the current one. Reset by checking before AND after a fresh attempt, or use the delta.

11. **Stubborn wakeup**: On some laptops, `System resumed again: Device or resource busy` persists even after disabling USB devices, XHC, ucsi-source-psy, and AC adapter wakeup. Kernel logs `PM: suspend exit` without identifying a source. Likely **firmware ACPI issue** (embedded controller, USB-C PD controller on dock path, or chipset wake). Try BIOS update, kernel parameter `acpi_no_wakeup`, or use `s2idle` instead of `deep`.

12. **Systemd service (`WantedBy=suspend.target`) vs systemd-sleep hook**: A systemd system service with `WantedBy=suspend.target` and `ExecStart=/usr/bin/systemctl --user -M <user> stop <service>` will **fail** because root cannot authenticate to the user's manager session from a system service context. The `systemctl --user -M` approach only works from a **plain script** in `/usr/lib/systemd/system-sleep/` (systemd-sleep hooks), which run outside systemd's service manager. Do NOT create a `.service` file for pre-suspend user-command execution — use a systemd-sleep hook script instead.

12. **libusb daemons invisible to lsof**: Daemons using libusb (e.g. `open-fprintd`) don't open `/dev/bus/usb/*` nodes directly — `lsof` returns nothing. Search by process name or service name instead (`ps aux | grep -i fprint`).

13. **`-EBUSY` on both deep and s2idle**: If a `usbfs` device or a `power/control=on` device blocks suspend, the error fires for **both** sleep states — it's a device-level lock, not a power-state issue. Don't waste time switching from deep to s2idle.
