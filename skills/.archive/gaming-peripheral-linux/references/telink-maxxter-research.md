# Telink/Maxxter Gaming Mouse (248a:fa02) — Research Notes

## Device identity
- USB: `248a:fa02 Maxxter Wireless Receiver`
- Kernel name: `Telink Wireless Receiver Mouse`
- Chipset: Telink (low-cost wireless gaming mice sold under multiple brands)
- Typical brands: Rexus Shaga V2, and generic "gaming mouse" sold via Amazon/AliExpress
- Often sold as "2.4G Wireless Gaming Mouse" with DPI button, 2 side buttons, RGB

## Linux detection
The dongle presents as **multiple input devices**:

| Kernel Name | Event | Role |
|-------------|-------|------|
| Telink Wireless Receiver Mouse | event6/mouse0 | Standard pointer, LMB/RMB/MB/wheel |
| Telink Wireless Receiver Consumer Control | event7 | Media keys + extra button routing |
| Telink Wireless Receiver System Control | event8 | Power/sleep + extra button routing |
| Telink Wireless Receiver | event9+ | Additional HID interfaces |

## libinput detection (Wayland)
```bash
libinput list-devices | grep -A 15 "Telink\|Maxxter\|Wireless Receiver"
```

Shows 3 devices:
1. **Telink Wireless Receiver Mouse** — capabilities: pointer. Scroll: button.
2. **Telink Wireless Receiver Consumer Control** — capabilities: keyboard, pointer.
3. **Telink Wireless Receiver System Control** — capabilities: keyboard.

## CRITICAL: Wireless vs Wired mode

These mice present **completely different USB IDs** depending on connection mode, with different HID report descriptors:

| Mode | USB ID | Kernel Name | Side buttons | KEY bitmap |
|------|--------|-------------|-------------|------------|
| Wireless (receiver) | `248a:fa02` | Telink Wireless Receiver Mouse | ❌ No events | `70000` (3 btn) |
| Wired (USB cable) | `248a:fb01` | Telink Wireless Gaming Mouse | ✅ YES as 275/276 | `1f0000` (5 btn) |

### Wired mode devices (248a:fb01)

When connected via USB cable, the mouse re-enumerates with a full HID descriptor:

| Kernel Name | Event | Role |
|-------------|-------|------|
| Telink Wireless Gaming Mouse | event19/mouse3 | Pointer + BTN_SIDE (275) + BTN_EXTRA (276) |
| Telink Wireless Gaming Mouse Consumer Control | event20 | Media keys |
| Telink Wireless Gaming Mouse System Control | event21 | Power/sleep |
| Telink Wireless Gaming Mouse Keyboard | event23 | Full keyboard HID interface |

The KEY bitmap on the wired mouse event is `1f0000` — bits 16-20 = BTN_LEFT (272), BTN_RIGHT (273), BTN_MIDDLE (274), BTN_SIDE (275), BTN_EXTRA (276).

### Why this happens

The wireless receiver (248a:fa02) uses a simplified HID report descriptor that only exposes the standard 3-button mouse. The side button presses are consumed entirely by the mouse firmware for DPI cycling — they never reach the USB report. In wired mode, the mouse uses a fuller descriptor that exposes all 5 buttons to the host.

### Linux configuration (Hyprland)

Only works in **wired mode**. Add to Hyprland binds:

```ini
bind = , mouse:275, workspace, e-1   # back = previous workspace
bind = , mouse:276, workspace, e+1   # forward = next workspace
```

Reload: `hyprctl reload`

## Extra button routing (wireless — for reference)

When side buttons DO route through separate interfaces (older firmware revisions), they may arrive via Consumer Control (event7) or System Control (event8), NOT through the main mouse device. Test:
```bash
wev /dev/input/event7
wev /dev/input/event8
```

But per July 2026 testing, most units now have firmware-only buttons in wireless mode with no host-side events at all.

## Button codes (wired mode confirmed)

Confirmed via evtest on Telink Wireless Gaming Mouse (event19, 248a:fb01):

| Button | Code | evtest output |
|--------|------|---------------|
| Back/Side | 275 (BTN_SIDE) | `code 275 (BTN_SIDE), value 1 / value 0` |
| Forward/Extra | 276 (BTN_EXTRA) | `code 276 (BTN_EXTRA), value 1 / value 0` |

Hyprland bind syntax: `mouse:275`, `mouse:276`

## DPI

- **libratbag/ratbagd**: NOT supported (vendor 248a not in device database)
- **Physical DPI button**: Usually present on underside or behind scroll wheel
- **Windows persistence**: DPI saved to onboard firmware, survives reboot into Linux
- **Software alternative**: Hyprland `input.sensitivity`

## CachyOS forum thread
https://discuss.cachyos.org/t/mouse-side-buttons-in-wireless-mode-not-detetcted/12907
User Oscar_M with same mouse (Rexus Shaga V2). Side buttons not detected in wireless mode via evtest. Thread had no confirmed solution — likely because buttons route through Consumer Control interface.

## Event capability bitmaps (from /sys)

Mouse (input7):
- KEY: `70000 0 0 0 0` → bits 16-18 = BTN_LEFT, BTN_RIGHT, BTN_MIDDLE

Consumer Control (input8):
- KEY: `733eff 0 0 483ffff17aff32d bfd4444600000000 1 130ff38b17c000 677bfad9415fed 9ed68000004400 10000002`
- Includes consumer keys (play, pause, next, prev, etc.) and potentially extra mouse button codes

System Control (input9):
- KEY: `c000 10000000000000 0` → bits 14-15 = KEY_SLEEP, KEY_POWER
