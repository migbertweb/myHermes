# USB-C PD (ucsi-source-psy) Wakeup

## Symptom

System enters deep sleep and wakes up immediately. `systemd-suspend.service` shows:
```
Failed to put system to sleep. System resumed again: Device or resource busy
```

Kernel logs show no specific wakeup source. The `ucsi-source-psy` devices don't appear in `/proc/acpi/wakeup` but show up in `/sys/class/wakeup/`.

## Identification

```bash
# Check event counts to find devices generating wakeups
grep . /sys/class/wakeup/*/event_count | sort -t: -k2 -rn

# Map wakeupN to the actual device name
for w in /sys/class/wakeup/wakeup*; do
  name=$(cat $w/name 2>/dev/null)
  ev=$(cat $w/event_count 2>/dev/null)
  echo "$(basename $w): $name ($ev events)"
done
```

Look for entries like:
- `ucsi-source-psy-USBC000:00N` — USB-C Power Delivery source
- `AC` — AC adapter plug/unplug events

## Fix Options

### Runtime disable (lost on reboot)
```bash
sudo sh -c 'echo disabled > /sys/devices/platform/USBC000:00/power_supply/ucsi-source-psy-USBC000:001/power/wakeup'
sudo sh -c 'echo disabled > /sys/devices/platform/USBC000:00/power_supply/ucsi-source-psy-USBC000:002/power/wakeup'
```

### Persistent via systemd service at boot
```ini
[Unit]
Description=Disable USB-C PD (ucsi-source-psy) wakeup sources
After=sysinit.target

[Service]
Type=oneshot
ExecStart=sh -c 'echo disabled > /sys/devices/platform/USBC000:00/power_supply/ucsi-source-psy-USBC000:001/power/wakeup; echo disabled > /sys/devices/platform/USBC000:00/power_supply/ucsi-source-psy-USBC000:002/power/wakeup'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

## Additional Wakeup Sources

After disabling ucsi-source-psy, if wakeup persists check:

1. **XHC (USB xHCI controller)** in `/proc/acpi/wakeup`: `echo XHC > /proc/acpi/wakeup` toggles it
2. **LID (lid switch)**: Also toggled via `/proc/acpi/wakeup` — only disable if lid events are spurious
3. **AC adapter** (`/sys/class/wakeup/wakeup28`): May need power/wakeup disabled
4. **RP05/RP09/RP11 (PCIe ports)**: If S4-enabled, can wake from suspend on some firmware
