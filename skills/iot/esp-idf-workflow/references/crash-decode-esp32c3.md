# ESP32-C3 Crash Decoding Reference

ESP32-C3 uses a **RISC-V** core (NOT Xtensa like ESP32/ESP32-S3). The toolchain is `riscv32-esp-elf` — never use `xtensa-` variants.

## Guru Meditation Error Format

```
Guru Meditation Error: Core  panic'ed (StoreProhibited/ LoadProhibited/ ...)
MEPC    : 0x4200XXXX
RA      : 0x4200XXXX
...
```

### Key fields
- **MEPC** (Machine Exception PC) — instruction that caused the fault, primary decode target
- **RA** — return address (caller)
- **Cause** — type of exception: `StoreProhibited` (writing bad address), `LoadProhibited` (reading bad address), `InstructionAccessFault` (jumping to bad address)

## Decode a Crash Address

From the project build directory (where `deskmate.elf` lives):

```bash
riscv32-esp-elf-addr2line -pfiaC -e build/deskmate.elf 0x4200XXXX
```

Flags breakdown:
- `-p` — pretty-print (one line)
- `-f` — show function name
- `-i` — inline chain (shows all callers through inlined functions)
- `-a` — show address before resolution
- `-C` — demangle C++ names (harmless for C)

### Example

```
$ riscv32-esp-elf-addr2line -pfiaC -e build/deskmate.elf 0x4200ABCD
0x4200abcd: xEventGroupSetBits at /IDF/components/freertos/FreeRTOS-Kernel/event_groups.c:580
```

This tells you EXACTLY which function and line crashed, making the fix obvious (e.g., NULL event group).

## Common Crash Patterns

| MEPC function | Likely cause | Fix |
|---|---|---|
| `xEventGroupSetBits` | `wifi_event_group` is NULL | Add `xEventGroupCreate()` to `app_main` |
| `nvs_flash_init` | Flash not initialized yet | Call `nvs_flash_init()` at top of `app_main` |
| `esp_wifi_start` | NVS not ready | See above |
| `gpio_set_level` / `gpio_get_level` | Bad GPIO number or pin config | Check pin definitions in `PIN_*` macros |
| `esp_http_client_*` | Out of heap or bad URL | Check `OWM_API_KEY`, reduce `FORECAST_BUFFER_MAX` |

## Toolchain Path

ESP-IDF v5.5.3:
```
/home/migbert/.espressif/tools/riscv32-esp-elf/esp-14.2.0_20251107/riscv32-esp-elf/bin/
```

This is in PATH after running `export.sh`.
