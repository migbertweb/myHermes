# Crash diagnostic: Guru Meditation Load access fault on IP obtained

## Symptom

ESP boots, connects WiFi, gets DHCP lease, then IMMEDIATELY crashes with:

```
I (3812) esp_netif_handlers: sta ip: 192.168.1.9, mask: 255.255.255.0, gw: 192.168.1.1
I (3812) deskmate: IP obtenida: 192.168.1.9
Guru Meditation Error: Core  0 panic'ed (Load access fault). Exception was unhandled.

MEPC    : 0x40386f94  MTVAL   : 0x00000000
MCAUSE  : 0x00000005
```

Key indicators:
- Crash happens **immediately** after `IP obtenida` log
- MTVAL = 0x00000000 (NULL pointer dereference — load from address 0)
- MCAUSE = 5 (Load access fault on RISC-V)
- ESP resets and loops: same crash every boot cycle

## Root cause

`wifi_event_group` is an `EventGroupHandle_t` declared as static global, but **never initialized with `xEventGroupCreate()`**:

```c
static EventGroupHandle_t wifi_event_group;  // = NULL (zero-initialized)
```

The `IP_EVENT_STA_GOT_IP` event handler calls:
```c
xEventGroupSetBits(wifi_event_group, WIFI_CONNECTED_BIT);  // CRASH: wifi_event_group is NULL
```

## Diagnosis with addr2line

ESP32-C3 is **RISC-V** (not Xtensa like classic ESP32):

```bash
# Find the tool
find ~/.espressif/tools/riscv32-esp-elf -name 'addr2line' -type f

# Decode crash PC
riscv32-esp-elf-addr2line -pfia -e build/deskmate.elf 0x40386f94
# → xEventGroupSetBits at event_groups.c:580

# Decode return address from stack
riscv32-esp-elf-addr2line -pfia -e build/deskmate.elf 0x42098f72
# → handler_execute at esp_event.c (inlined by esp_event_loop_run)
```

## Fix

Add to app_main() **before** wifi_init():

```c
wifi_event_group = xEventGroupCreate();
```

## Prevention checklist when reconstructing app_main()

All these must be initialized:

| Variable | Init call | When |
|---|---|---|
| panel_handle | esp_lcd_new_panel_st7789() | Inside lcd_init() |
| wifi_event_group | xEventGroupCreate() | Before wifi_init() |
| time_synced | sntp_time_sync_cb() | Sets to true on NTP sync |
| wifi_connected | IP_EVENT_STA_GOT_IP handler | Sets to true on DHCP |
| wifi_retries | Set to 0 at start | Inside wifi_init() |

## C source patching — the breakage that caused this

Naive Python `content.find('{', start_idx)` matched the wrong function's opening brace because prototypes (no `{`) precede definitions. See SKILL.md Pitfall 24 for details. The reconstruction was necessary because the brace-matching bug destroyed app_main.

## Full boot log with crash (2026-06-27)

```
ESP-ROM:esp32c3-api1-20210207
rst:0x15 (USB_UART_CHIP_RESET),boot:0xe (SPI_FAST_FLASH_BOOT)
entry 0x403cbf10
I (272) main_task: Calling app_main()
I (282) deskmate: DeskMate Dashboard iniciando...
I (282) deskmate: Inicializando SPI bus...
I (402) deskmate: Display ST7789 inicializado correctamente
I (402) deskmate: Boton GPIO 3 configurado (pull-up, active low)
I (402) deskmate: Inicializando WiFi...
I (542) wifi:mode : sta (8c:d0:b2:a9:f8:67)
I (542) deskmate: WiFi inicializado
I (542) deskmate: Inicializando SNTP...
I (542) deskmate: SNTP inicializado - esperando sincronizacion
I (552) wifi:state: init -> auth (0xb0)
I (682) wifi:connected with Sukuna-78-2.4g, aid = 3, ...
I (3812) esp_netif_handlers: sta ip: 192.168.1.9, ...
I (3812) deskmate: IP obtenida: 192.168.1.9
*** CRASH ***
```
