---
name: esp-idf-workflow
description: ESP-IDF workflow for CachyOS laptop. Build, flash, monitor ESP32 projects locally. ESP-IDF v5.5.3 toolchain.
---
# ESP-IDF Workflow on CachyOS Laptop

## Connection

This workflow runs **locally** on your CachyOS laptop (`192.168.1.17`). No SSH needed for ESP-IDF commands.

## Toolchain

ESP-IDF **v5.5.3** at `/home/migbert/.espressif/v5.5.3/esp-idf/`.
ESP32-C3 device typically at `/dev/ttyACM0` (user in `uucp` group).

### Activate toolchain before first use each session:
```bash
. /home/migbert/.espressif/v5.5.3/esp-idf/export.sh
```

## Commands (run locally from any ESP-IDF project directory)

### Build
```bash
idf.py build
```

### Flash
```bash
idf.py -p /dev/ttyACM0 flash
```

### Build + Flash
```bash
idf.py -p /dev/ttyACM0 build flash
```

### Monitor serial
```bash
idf.py -p /dev/ttyACM0 monitor
```

## Pitfalls When Patching C Source Remotely

When using Python scripts (via `execute_code` or `write_file` + `scp`) to patch large C files, watch for:

### Brace-Matching Eating Other Functions

Searching for `content.find("static void my_func(void)")` may match the **prototype** (`;` ending), not the **definition** (`{` following). The prototype is usually earlier in the file. Matching braces from the prototype's location will consume ALL intervening code until the first `{` it finds, which may be inside a DIFFERENT function entirely.

**Rule:** Always search for the full definition signature including the opening brace:
```python
# WRONG - matches prototype first:
idx = content.find("static void my_func(void)")

# RIGHT - only matches the definition:
idx = content.find('static void my_func(void)\n{')
```

### Marker Text Must Include Full Closing Delimiter

When replacing a block comment that starts with `/*`, ensure your replacement text includes the `*/` that closes it. If the marker includes `*/` but the replacement doesn't, the closing `*/` is removed from the file, leaving an unclosed comment that cascades errors.

### Multiple Identical Signatures

If a function has both a prototype and a definition with the same signature, `content.replace(old, new)` replaces the FIRST occurrence (the prototype). Plan for this — either delete the prototype first, or match a more specific string.

## Troubleshooting

### Port & Access

- **Port busy:** `fuser -k /dev/ttyACM0` kills the serial monitor.
- **Permission:** Must be in `uucp` group for ACM device access.

### Boot Crashes (Guru Meditation)

ESP32-C3 errors appear as `Guru Meditation Error (StoreProhibited/LoadProhibited)` with a register dump.

**Most Common Causes — Fix before investigating anything else:**

1. **NULL Event Group (`xEventGroupCreate` missing)**
   - Symptom: crash in `xEventGroupSetBits()` at `event_groups.c:NNN`
   - Root cause: `wifi_event_group` is NULL because `xEventGroupCreate()` was never called
   - Fix: add `wifi_event_group = xEventGroupCreate();` in `app_main()` BEFORE `lcd_init()` or any WiFi call
   - Relevant: `ESP_LOGE(TAG, "wifi_event_group is NULL!");` as a guard

2. **Missing `nvs_flash_init()`**
   - Symptom: WiFi fails to init, NVS errors in boot log
   - Fix: always call `nvs_flash_init()` at the VERY TOP of `app_main()`, with the erase-retry pattern:
   ```c
   esp_err_t ret = nvs_flash_init();
   if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
       ESP_ERROR_CHECK(nvs_flash_erase());
       ret = nvs_flash_init();
   }
   ESP_ERROR_CHECK(ret);
   ```

3. **GPIO Button Active-Low Inversion**
   - ESP32 GPIOs use internal pull-up; button to GND = active-low
   - `gpio_get_level(PIN_BUTTON)` returns `1` when NOT pressed, `0` when pressed
   - Correct reading: `bool btn = !gpio_get_level(PIN_BUTTON);`
   - Auto-rotation condition: `if (!btn) { ... }` means "only rotate when button is NOT pressed" (btn is true-when-pressed)
   - If you forget the `!`, auto-rotation NEVER fires because `btn` is always `1`

### Decoding Crash Addresses

ESP32-C3 is RISC-V (NOT Xtensa). Use the riscv32 toolchain:

```bash
riscv32-esp-elf-addr2line -pfiaC -e build/deskmate.elf 0x4200XXXX
```

Replace `0x4200XXXX` with the `epc1` value from the Guru Meditation dump.

### Serial Log Diagnosis (Boot Sequence)

A healthy boot on the DeskMate dashboard looks like:
```
0.4s  → Display init
3.9s  → WiFi + IP
5.1s  → SNTP sync
8.5s  → Weather fetch
9.9s  → Forecast fetch
10.2s → Clock display
25.2s → Auto-rotation to forecast
```

If any step is missing or the device hangs, check:
- **WiFi blocks:** NVS not initialized, or event group NULL (see above)
- **HTTP fails:** DNS or connectivity — check `OWM_API_KEY` and WiFi credentials
- **Display stays black:** SPI pins, panel init order, or `lcd_fill_screen(COLOR_BLACK)` never called
