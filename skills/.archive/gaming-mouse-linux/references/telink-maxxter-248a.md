# Telink/Maxxter Gaming Mouse (248a:fa02 / 248a:fb01)

Investigation from 2026-07-26 session. Hardware: generic gaming mouse with Telink chipset, sold under multiple brands (Rexus, Maxxter, etc.).

## USB IDs

| Mode | ID | Kernel name |
|------|----|-------------|
| Wireless (dongle) | `248a:fa02` | `Telink Wireless Receiver Mouse` |
| Wired (USB cable) | `248a:fb01` | `Telink Wireless Gaming Mouse` |

## Event devices (wired mode)

| Device | Event | Type | Notable |
|--------|-------|------|---------|
| Gaming Mouse | event19 / mouse3 | pointer | KEY=1f0000 = BTN_LEFT/RIGHT/MIDDLE/SIDE/EXTRA |
| Consumer Control | event20 / kbd | keyboard/media | Extended key codes |
| System Control | event21 / kbd | system | Power/sleep keys |
| Gaming Mouse (ABS) | event22 | absolute | Scroll/digitizer |
| Gaming Mouse Keyboard | event23 / kbd | keyboard | Full keyboard scancodes |

## Event devices (wireless mode)

| Device | Event | Type | Notable |
|--------|-------|------|---------|
| Wireless Receiver Mouse | event6 / mouse0 | pointer | KEY=70000 = only 3 buttons (no side/extra) |
| Consumer Control | event7 / kbd | keyboard/media | Same as wired, but side buttons don't fire |
| System Control | event8 / kbd | system | Power/sleep |
| Wireless Receiver | event9 | absolute | Scroll/digitizer |
| Wireless Receiver Keyboard | event10 / kbd | keyboard | Full keyboard |

## Key finding

In **wireless mode** (248a:fa02), the extra side buttons generate ZERO events on any event device. Only the DPI button works at hardware level (cycles stored DPI values). This is a firmware limitation of the receiver, not a missing driver.

In **wired mode** (248a:fb01), the side buttons produce standard BTN_SIDE (275) and BTN_EXTRA (276) events through the mouse pointer device.

## Hyprland binds (wired only)

```ini
bind = , mouse:275, workspace, e-1    # Side button = prev workspace
bind = , mouse:276, workspace, e+1    # Extra button = next workspace
bind = , mouse:275, exec, playerctl previous    # Or media controls
bind = , mouse:276, exec, playerctl next
```

## CachyOS forum reference

Thread: https://discuss.cachyos.org/t/mouse-side-buttons-in-wireless-mode-not-detetcted/12907

Same issue reported by another user with exact same hardware ID. No solution found — it's a firmware limitation, not configurable.
