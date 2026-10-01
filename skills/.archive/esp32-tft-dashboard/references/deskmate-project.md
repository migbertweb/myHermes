# DeskMate Project — ESP32-C3 Super Mini + ST7789 (ESP-IDF)

Project-specific build of the ESP32 TFT dashboard, using **ESP-IDF native** (no Arduino). Built and verified on CachyOS with ESP-IDF v5.5.3.

## Hardware

| Component | Detail |
|---|---|
| **ESP32-C3 Super Mini** (AZ-Delivery) | Chip rev v0.4, flash 4MB XMC, MAC 8c:d0:b2:a9:f8:67 |
| **ST7789 SPI** | 240×240, 7-pin, 1.54" |
| **WiFi** | STA mode, WPA2-PSK, 2.4 GHz |

## Pin mapping (confirmed working)

| Display pin | GPIO | Notes |
|---|---|---|
| MOSI (SDA) | GPIO 6 | SPI data (not default FSPI MOSI) |
| SCLK | GPIO 9 | Strapping pin — works via GPIO Matrix |
| DC | GPIO 10 | |
| CS | GPIO 21 | Also UART0 TX |
| RST | GPIO 4 | |
| BL | 3.3V | Fijo (no PWM) |

## Build & Flash

```bash
cd ~/proyectos/deskmate
. /home/migbert/.espressif/v5.5.3/esp-idf/export.sh
idf.py build
fuser -k /dev/ttyACM0 2>/dev/null   # liberar si ocupado
idf.py -p /dev/ttyACM0 flash
```

## Project structure

```
deskmate/
├── CMakeLists.txt              # project(deskmate), sdkconfig includes
├── sdkconfig                   # CONFIG_ESP_MAIN_TASK_STACK_SIZE=8192
├── build/
│   └── deskmate.bin            # v0.3 — NTP clock + weather (~0xd1878 bytes)
├── main/
│   ├── CMakeLists.txt          # REQUIRES: esp_lcd esp_driver_spi driver esp_event
│   │                          #           esp_netif esp_wifi nvs_flash lwip
│   │                          #           esp_http_client json
│   ├── main.c                  # ~630 lines: SPI, display, WiFi+SNTP, clock, weather
│   └── include/
│       ├── pin_config.h        # WiFi creds, timezone, pin defs, WEATHER defines
│       └── font_5x7.h          # 95-char bitmap 5×7 font
```

## Display driver (SPI config)

- **Bus**: SPI2_HOST, 40 MHz, mode 0
- **DMA**: `SPI_DMA_CH_AUTO`
- **Pixel format**: RGB565 (16 bpp)
- **Element order**: `LCD_RGB_ELEMENT_ORDER_BGR`
- **Color inversion**: `esp_lcd_panel_invert_color(panel, true)` — required for this ST7789 model

## WiFi

- **SSID**: Sukuna-78-2.4g (2.4 GHz only)
- **STA mode**, WPA2-PSK
- **DHCP**: 192.168.1.14
- **RSSI**: -58 dBm (good)
- **Credentials** in `pin_config.h`, not NVS

## NTP Clock

- **SNTP**: single poll at boot, then refresh every 60s
- **Timezone**: CST6CDT (Mexico Central)
- **Sync method**: event group (WIFI_CONNECTED_BIT → TIME_SYNCED_BIT), blocks in app_main
- **Display**: HH:MM large (5×7 font scaled 4x), :SS small (scaled 2x), day-of-week + DD/MM/YYYY, green WiFi indicator (12×12 rect + "WiFi" text scaled 2x)

## Weather (OpenWeatherMap)

- **Endpoint**: `http://api.openweathermap.org/data/2.5/weather?id=3459712&appid=API_KEY&units=metric&lang=es` (HTTP, no HTTPS)
- **City**: Joinville, Brazil (ID 3459712)
- **Fetch interval**: 600s (10 min), first fetch 3s after SNTP sync
- **Display**: Temp °C (scale 2x), feels-like (scale 2x), description (scale 2x)

### HTTP Implementation Details

- Uses **manual pattern**: `esp_http_client_open()` → `esp_http_client_fetch_headers()` → `esp_http_client_read()` loop
- **`esp_http_client_perform()` does NOT work** — consumes response body internally
- **Buffer**: heap-allocated (`malloc`), 2048-4096 bytes, NEVER stack
- **HTTP timeout**: 15s, method GET
- **Stack size**: CONFIG_ESP_MAIN_TASK_STACK_SIZE=8192 (was 3584, overflow with HTTP)

### Weather JSON Parsing

```json
{
  "coord": {"lon": -48.8456, "lat": -26.3044},
  "weather": [{"id": 803, "main": "Clouds", "description": "muy nuboso", "icon": "04n"}],
  "main": {"temp": 19.6, "feels_like": 20.1, "temp_min": 18.0, "temp_max": 21.0,
           "pressure": 1014, "humidity": 88}
}
```

Parsed with `cJSON` — extracts `main.temp`, `main.feels_like`, `weather[0].description`.

## Phases

| Phase | Status | Description |
|---|---|---|
| F1: Display driver | ✅ | ST7789 init + test pattern (color bars) |
| F2: NTP Clock | ✅ | WiFi + SNTP + time rendering |
| F3: Weather | ✅ | OpenWeatherMap HTTP + cJSON parse (+heap buf workaround) |
| F4: Auto-rotate | ❌ | Timer cycling clock/weather/etc |
| F5: DHT11 | ❌ | Local temp/humidity sensor |
| F6: WS2812B LEDs | ❌ | RGB ambient lighting |
| F7: Web dashboard | ❌ | Remote config from phone |

## Verified behavior

- **Boot**: ESP-IDF v5.5.3, chip rev v0.4, flash 4MB
- **Display**: init OK at ~0.5s, shows clock immediately
- **WiFi**: connected in ~3s, IP assigned by DHCP (192.168.1.14)
- **SNTP**: sync at ~5s post-boot
- **Clock**: renders every ~1.1s in main loop
- **Weather**: HTTP status 200, content_length 522, parsed cJSON OK. Output: "19.6°C (feels 20.1°C) - muy nuboso"
- **Heap**: ~133KB total at boot, ~15KB used during weather fetch, freed after

## Known pitfalls (DeskMate-specific)

- `/dev/ttyACM0` busy after `idf.py monitor` — kill with `fuser -k /dev/ttyACM0` or `kill <PID>`
- `esp_event.h` compile error → add `esp_event` to REQUIRES in CMakeLists.txt
- ST7789 SPI mode 0 required (not mode 3)
- Credentials in `pin_config.h` means recompile on network change
- **`esp_http_client_perform()` bug** — always use manual open/fetch_headers/read pattern
- **Stack overflow** — must increase `CONFIG_ESP_MAIN_TASK_STACK_SIZE` to 8192 in sdkconfig
- **Heap vs stack** — HTTP response buffer MUST be malloc'd, never stack-allocated
- **First weather fetch** must wait ~3s after SNTP sync for TCP/IP stack to stabilize
