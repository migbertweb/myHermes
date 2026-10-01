---
name: gaming-mouse-linux
description: "Gaming mouse config on Linux: evtest, Hyprland binds, DPI."
tags: [hyprland, wayland, mouse, gaming-mouse, dpi, evtest, wev, libratbag]
category: hardware
---

# Gaming Mouse on Linux (Hyprland/Wayland)

Use when the user needs to configure a gaming mouse on Linux (Hyprland/Wayland): extra buttons, DPI, sensitivity, or remapping.

## Detection

```bash
# Identify the mouse hardware
lsusb | grep -iE "mouse|logitech|razer|248a"

# Find event device and capabilities
cat /proc/bus/input/devices | grep -B 2 -A 10 "Telink\|Gaming Mouse\|YourMouse"

# Check libinput recognition
libinput list-devices | grep -A 15 "Telink\|YourMouse"
```

## Identify button codes

### wev (Wayland — default)
```bash
wev
# Move pointer to the wev window, press each button
# Look for: button: 275 (BTN_SIDE), button: 276 (BTN_EXTRA)
```

### evtest (low-level — when wev misses events)
```bash
# Try the mouse event device first
evtest /dev/input/eventN

# If no events, try other interfaces from the same receiver:
# Consumer Control, System Control, or extra Keyboard event
```

**Common button codes:**

| Button | Code | evtest name |
|--------|------|-------------|
| LMB | 272 | BTN_LEFT |
| RMB | 273 | BTN_RIGHT |
| Wheel click | 274 | BTN_MIDDLE |
| Side (back) | 275 | BTN_SIDE |
| Extra (forward) | 276 | BTN_EXTRA |

## Hyprland binds

Add to `~/.config/hypr/dms/binds.conf` or wherever binds are sourced:

```ini
# Simple action bind
bind = , mouse:275, exec, playerctl previous
bind = , mouse:276, exec, playerctl next

# Window management
bind = , mouse:274, killactive
bindm = , mouse:275, resizewindow

# Workspace switching
bind = , mouse:275, workspace, e-1
bind = , mouse:276, workspace, e+1
```

Reload: `hyprctl reload`

## Sensitivity & DPI

### Hardware DPI button
Most gaming mice have a physical button that cycles pre-set DPI levels stored in firmware. Works regardless of OS.

### Software sensitivity (Hyprland)
```ini
input {
    sensitivity = 0.6         # -1.0 to 1.0 (0 = default)
    accel_profile = flat      # flat = 1:1 movement (gaming)
}
```

### libratbag/piper (branded mice)
```bash
sudo pacman -S libratbag piper
ratbagctl <device> dpi set 800
piper  # GUI
```

### solaar (Logitech only)
```bash
sudo pacman -S solaar
solaar
```

## Known hardware quirks

### Telink/Maxxter generic gaming mice (248a:fa02 / 248a:fb01)
- **Wireless mode** (248a:fa02): side/extra buttons are NOT exposed to the host OS. No events in evtest/wev on any interface. Only the DPI button works.
- **Wired mode** (248a:fb01): side/extra buttons generate BTN_SIDE (275) and BTN_EXTRA (276). All five buttons work.
- No libratbag support exists for these chipsets. DPI is hardware-only.

### libratbag supported database
Check: https://github.com/libratbag/libratbag
Try: `ratbagctl list`

## Pitfalls

- **Dual-mode mice** (wireless + cable): USB ID changes between modes. Re-check `lsusb` and `cat /proc/bus/input/devices` after toggling.
- **wev vs evtest**: wev only shows compositor-level events. For buttons routed through Consumer Control or secondary keyboard interfaces, use evtest directly on the event device.
- **`input` group**: if the user can't read /dev/input/event* without sudo, add them: `sudo usermod -aG input $USER` then re-login.
- **Hyprland bind conflicts**: `mouse:272` and `mouse:273` are LMB/RMB — overriding them will break window move/resize defaults.
