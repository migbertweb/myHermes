---
name: gaming-peripheral-linux
description: Config gaming mice on Arch + Hyprland. Buttons, DPI, remap.
---

# Gaming Peripheral Configuration on Linux

## When to use
- User has a gaming mouse/keyboard with extra buttons not working in Hyprland
- User needs to configure DPI, sensitivity, or button mapping
- User asks about configuring a non-standard HID device on Wayland
- Brand has no Linux app but has Windows software

## Step 0: Prerequisites

- You must be in the `input` group to read `/dev/input/event*` without sudo:
  ```bash
  groups | grep input           # check membership
  sudo usermod -aG input $USER  # add if missing (log out & back in)
  ```

## Step 1: Identify the device

Find the exact USB device and event nodes:

```bash
# Overview of input devices
libinput list-devices

# Detailed kernel device info — shows ALL interfaces of a multi-interface peripheral
cat /proc/bus/input/devices | grep -A 20 -i "mouse\\|pointer\\|receiver" | head -60

# USB vendor/product ID
lsusb | grep -i -E "mouse|receiver|gaming"
```

The kernel assigns separate event devices for different functions of the same peripheral. Look for these:
- **Mouse** interface — standard pointer events (eventN, mouseN)
- **Consumer Control** — media keys, sometimes extra buttons
- **System Control** — power/sleep, sometimes extra buttons
- **Keyboard** — if the device also has a keyboard or extra keyboard-style buttons

### Quick diagnostic: read sysfs capabilities

Before pressing a single button, check what events a device supports by reading its KEY bitmask:

```bash
cat /sys/class/input/event6/device/capabilities/key
# Example output: `70000 0 0 0 0`
# = bits 16-18 → BTN_LEFT (272), BTN_RIGHT (273), BTN_MIDDLE (274) only
# If BTN_SIDE (275) / BTN_EXTRA (276) bits are absent, the device cannot generate them.
#
# Compare all interfaces:
#   event6 (mouse):   `70000 0 0 0 0`                          → 3 standard buttons only
#   event7 (consumer): `733eff 0 0 483ffff17aff32d ...`         → many media/consumer keys
#   event8 (system):  `c000 10000000000000 0`                   → power/sleep only
# The device with the richest bitmap is where extra buttons route.
```

## Step 2: Identify button codes

On Wayland (Hyprland), use `wev`:

```bash
# General — shows all Wayland input events
wev

# On a specific event device
wev /dev/input/event7

# IMPORTANT: do NOT pipe wev to `head` — it will miss live events
```

If `wev` shows nothing on the main mouse node, try the Consumer Control or System Control event nodes instead.

Fallback: `evtest` (needs input group or sudo):

```bash
# Shows capabilities then WAITS for events. Do NOT pipe to `head -N` —
# head causes evtest to exit after N lines (capabilities only) without
# capturing any button presses.
evtest /dev/input/event7
# Press buttons → events appear. Ctrl+C to stop.
```

### Standard mouse button codes

| Button | Code | hyprland bind |
|--------|------|---------------|
| LMB | 272 | `mouse:272` |
| RMB | 273 | `mouse:273` |
| Middle/Wheel click | 274 | `mouse:274` |
| Side/Back | 275 | `mouse:275` |
| Extra/Forward | 276 | `mouse:276` |
| BTN_3–BTN_9 | 277–283 | `mouse:277` etc. |
| Wheel up | — | `mouse_up` |
| Wheel down | — | `mouse_down` |

## Step 3: Bind extra buttons in Hyprland

Add to `~/.config/hypr/hyprland.conf` (or the sourced binds file):

```ini
# Simple exec
bind = , mouse:275, exec, playerctl previous
bind = , mouse:276, exec, playerctl next

# Workspace navigation
bind = , mouse:275, workspace, e-1
bind = , mouse:276, workspace, e+1

# Hold-to-resize (bindm)
bindm = , mouse:275, resizewindow
bindm = , mouse:276, movewindow

# With modifier
bind = SUPER, mouse:275, exec, kitty
```

For DMS-based configs (common on DankMatterShell setups), the binds file may be at:

```
~/.config/hypr/dms/binds.conf
```

Apply changes:

```bash
hyprctl reload
```

## Step 4: DPI and sensitivity

### Hardware DPI (real)
Most gaming mice have a **physical DPI cycle button** — press it to cycle through preset levels stored in the mouse firmware. Works regardless of OS.

### libratbag/piper (for supported mice)

```bash
sudo pacman -S libratbag piper
ratbagctl list
piper    # GUI
```

Check device support at: https://github.com/libratbag/libratbag

### Software sensitivity (not real DPI, but adjusts cursor speed)

In Hyprland `input {}` block:

```ini
input {
    sensitivity = 0.6      # -1.0 to 1.0
    accel_profile = flat   # flat | adaptive | custom
}
```

### Pre-configure on Windows
DPI settings are stored in the mouse firmware. Connect to Windows once, set DPI with the brand's app, and it persists when plugged back into Linux.

## Step 5: HWDB remapping (advanced HID-level)

For buttons that the kernel misidentifies or produce wrong keycodes:

1. Run `sudo evtest /dev/input/eventX` and note the `MSC_SCAN` value when pressing the button
2. Create `/etc/udev/hwdb.d/71-mouse-remap.hwdb`:
   ```
   evdev:input:bVVVVpPPPP*
     KEYBOARD_KEY_90003=btn_side
   ```
   (Use `bVVVVpPPPP` from `cat /proc/bus/input/devices` — e.g. `b248a` is vendor, `pfa02` is product)
3. Apply:
   ```bash
   sudo systemd-hwdb update
   sudo udevadm trigger
   ```

## Pitfalls
- **Telink/Maxxter chipset** (vendor 248a) — common in cheap gaming mice. **NOT supported by libratbag.** DPI must be hardware-button or pre-configured on Windows.
- **CRITICAL: wireless vs wired mode** — Telink/Maxxter mice have different USB IDs for each mode:
  - **Wireless** (`248a:fa02`): side buttons produce **ZERO events** on all input interfaces. The mouse event KEY bitmap is `70000` (only BTN_LEFT/RIGHT/MIDDLE). Side buttons are firmware-only DPI switches. No remapping possible.
  - **Wired** (`248a:fb01`): side buttons **DO work** as BTN_SIDE (275) and BTN_EXTRA (276). The mouse event KEY bitmap is `1f0000` (includes BTN_SIDE/EXTRA). Test with `evtest /dev/input/event19` (or whichever event the wired mouse gets).
- Extra buttons on **wireless** mice often route through **Consumer Control** / **System Control** interfaces, not the main mouse device. If `wev` on the mouse event shows nothing, try other event nodes.
- **Quick check**: read the sysfs KEY bitmap. If the mouse event's bitmap only has `70000` (3 buttons), it physically cannot generate BTN_SIDE/EXTRA — the extra buttons must be on another device.
- **Some cheap gaming mice have side buttons that are purely firmware DPI-cycling switches** — they produce ZERO events on any Linux input device. The button only cycles through DPI presets stored in the mouse's onboard memory. No amount of remapping will work; the button is literally not connected to the HID report descriptor as a key.
  - To confirm: test ALL event devices from the receiver (mouse, consumer control, system control, keyboard) with evtest. If none produce events when pressing the side button, it's firmware-only.
- **evtest piped to `head -N`, `grep`, or `tail` will NOT capture live button presses** — `head`/`grep` causes evtest to exit after N lines (capabilities), so it never waits for live events. Run evtest bare, or use `stdbuf -oL evtest | grep ...` for buffering control.
- `sudo evtest` requires password + TTY. User must be in the `input` group for non-sudo access.
- After editing binds: `hyprctl reload` — no restart needed.
- **DMS-sourced configs** (DankMatterShell) store binds in `./dms/binds.conf` alongside other sourced files (layout.conf, cursor.conf, etc.). Find them with `ls ~/.config/hypr/dms/`.
- Software sensitivity (`input.sensitivity`) is NOT real DPI — post-processing multiplier.

## Verification
- Press bound button → expected action fires
- `wev` shows the event with expected code
- `hyprctl reload` exits with no errors
- `libinput list-devices` shows the device

## References
- Hyprland Binds wiki: https://wiki.hypr.land/0.42.0/Configuring/Binds
- libratbag supported devices: https://github.com/libratbag/libratbag
- Linux hwdb docs: `man systemd-hwdb`
