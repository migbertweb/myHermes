# Suspend Diagnosis Flow

Step-by-step from this session's real-world case on CachyOS/Arch.

## The Two-Part Problem Pattern

This case exhibited **both** issues simultaneously. Suspend won't work until both are fixed.

### Step 1 — Check suspend service logs

```bash
journalctl -u systemd-suspend.service --boot=-1
```

Typical output when both problems are active:
```
systemd-sleep[PID]: Performing sleep operation 'suspend'...
systemd-sleep[PID]: Failed to freeze unit 'user.slice': Connection timed out
systemd-sleep[PID]: Failed to put system to sleep. System resumed again: Device or resource busy
systemd[1]: systemd-suspend.service: Main process exited, code=exited, status=1/FAILURE
systemd[1]: suspend.target: Job suspend.target/start failed with result 'dependency'
```

### Step 2 — Find the offending process

The kernel message is cryptic by itself:
```
Freezing user space processes failed after 20.00x seconds (1 tasks refusing to freeze, wq_busy=0):
```

Get the full context — the task name is on the **next lines**:
```bash
journalctl --boot=-1 -o short-monotonic | grep -B5 -A10 'refusing to freeze'
```

Look for:
```
task:dgop state:D stack:0 pid:163773 ...
Call Trace:
  fuse_statfs → __fuse_simple_request → schedule
```

- `state:D` = uninterruptible sleep (disk I/O wait)
- `dgop` = FUSE daemon process (rclone's Google Drive mount)
- `fuse_statfs` = a `statfs` call on the FUSE mount was in-flight when the network went down

### Step 3 — Check power capabilities

```bash
cat /sys/power/state
# freeze mem disk

cat /sys/power/mem_sleep
# s2idle [deep]
```

- `s2idle` = shallow sleep (CPUs idle, RAM powered)
- `deep` = S3 suspend-to-RAM (what we want)

### Step 4 — Find wakeup sources

```bash
cat /proc/acpi/wakeup
grep . /sys/class/wakeup/*/event_count | sort -t: -k2 -rn
```

Non-zero event counts mean those devices triggered wake events. In this case:
- `wakeup59`: `ucsi-source-psy-USBC000:001` (USB-C PD) — 4 events
- `wakeup57`: `ucsi-source-psy-USBC000:002` (USB-C PD) — 1 event  
- `wakeup28`: `AC` (power adapter) — 1 event

Also check USB device wakeup:
```bash
for f in /sys/bus/usb/devices/*/power/wakeup; do
  dev=$(echo $f | cut -d/ -f6)
  echo "$dev => $(cat $f 2>/dev/null)"
done
```

### Step 5 — Identify the USB device

Find which USB device has `enabled` wakeup:
```bash
cat /sys/bus/usb/devices/1-4.4/product
# "Wireless Receiver"
cat /sys/bus/usb/devices/1-4.4/manufacturer  
# "Telink"
```

Match it to lsusb (`ID 248a:fa02 Maxxter Wireless Receiver`). This is the wireless mouse/keyboard receiver.

### Step 6 — Apply fixes

**A. systemd-sleep hook** for the FUSE process:
- `/usr/lib/systemd/system-sleep/rclone-suspend`
- Stops rclone-gdrive.service and lazy-unmounts before freeze
- Restarts after resume
- Must be `chmod 755`, owned by root, no file extension

**B. udev rule** for USB wakeup:
- `/etc/udev/rules.d/99-disable-wakeup.rules`
- Disables wakeup on the Telink/Maxxter receiver (`248a:fa02`)
- Apply to already-connected device: `sudo sh -c 'echo disabled > /sys/bus/usb/devices/1-4.4/power/wakeup'`

## Key Commands Reference

| Command | Purpose |
|---------|---------|
| `journalctl -u systemd-suspend.service --boot=-1` | Main error log |
| `journalctl -g 'refusing to freeze' -B5 -A5` | Find the D-state task |
| `cat /proc/acpi/wakeup` | ACPI wakeup devices |
| `grep . /sys/class/wakeup/*/event_count \| sort -t: -k2 -rn` | Wakeup event counters |
| `cat /sys/bus/usb/devices/*/product` | USB device names |
| `cat /sys/bus/usb/devices/*/power/wakeup` | USB wakeup status |
| `echo disabled \| sudo tee /sys/.../power/wakeup` | Disable wakeup (may hang — use `sudo sh -c` instead) |
