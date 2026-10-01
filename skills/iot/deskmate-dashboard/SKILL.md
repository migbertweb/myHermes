---
name: deskmate-dashboard
description: DeskMate — panel de escritorio inteligente con ESP32-C3 Super Mini + ST7789 240x240 (SPI). Reloj NTP + clima OpenWeatherMap + iconos clima XBM 32x32.
version: "3.6 (2026-07-19) — Pantalla de boot con IP, pitfalls IP fija y DHCP"
---

# DeskMate Dashboard

Panel de escritorio inteligente con **ESP32-C3 Super Mini** + **ST7789 240x240** via SPI, ESP-IDF nativo (sin Arduino).

## Conexión Remota (SSH)

El proyecto vive en la laptop CachyOS (`192.168.1.17`). El servidor tiene configurado el host `cachy` en `~/.ssh/config`:

```
Host cachy
     HostName 192.168.1.17
     User migbert
     Port 22
     StrictHostKeyChecking accept-new
```

Comandos útiles vía SSH:

```bash
# Build
ssh cachy "cd /home/migbert/proyectos/deskmate && . /home/migbert/.espressif/v5.5.3/esp-idf/export.sh && idf.py build"

# Flash
ssh cachy "cd /home/migbert/proyectos/deskmate && . /home/migbert/.espressif/v5.5.3/esp-idf/export.sh && fuser -k /dev/ttyACM0 2>/dev/null; idf.py -p /dev/ttyACM0 flash"

# Monitor serial
ssh cachy "cd /home/migbert/proyectos/deskmate && . /home/migbert/.espressif/v5.5.3/esp-idf/export.sh && idf.py -p /dev/ttyACM0 monitor"
```

**ESP-IDF:** v5.5.3 en `/home/migbert/.espressif/v5.5.3/esp-idf/`.
**Dispositivo:** ESP32-C3 en `/dev/ttyACM0` (usuario migbert en grupo `uucp`).

### Fase 5 (v0.4) — Pantalla de pronóstico + navegación automática
- **Switch de pantallas**: `screen_t` enum (SCREEN_CLOCK=0, SCREEN_FORECAST=1) en estructura `current_screen`
- **Auto-rotación**: Timer de 10s rota clock↔forecast. Sin botón — navegación 100% automática.
- **Forecast OWM**: Endpoint `/data/2.5/forecast`, buffer 20KB en heap, 40 entradas (cada 3h x 5 días). Parseo con `cJSON`.
  - **Agrupación por día**: Entero `date_key = YYYY*10000 + MM*100 + DD`. Salta entradas del día actual.
  - **Datos por día**: `temp_min` (mín de todos), `temp_max` (máx de todos), `pop` (máx probabilidad 0-100%), `icon` (preferencia horario diurno 9-15h).
  - **Refresh**: Cada 20 minutos (2× WEATHER_INTERVAL).
- **Layout forecast (240×240)**:
  ```
  y=10: ── PRONÓSTICO ──               (TEAL, centrado)
  y=26: ────────────────                (separador)
  y=40: ☀️ LUN  24°/18°  20%            (icono 32×32 + día TEAL + temp WHITE + POP% CYAN)
  y=80: ⛅ MAR  25°/15°  49%            (cada línea cada 40px)
  y=120: 🌧️ MIE  17°/16°  100%
  y=160: ☁️ JUE  22°/15°  29%
  y=220: [ Pronóstico ]                  (indicador de pantalla)
  ```
- **Dibujo diferencial del forecast**: Solo se dibuja cuando `forecast_first_run=true`. La pantalla es estática hasta que se cambia a otra pantalla y se regresa, o se refrescan los datos.

## Fases completadas

### Fase 6 (v0.5) — Probabilidad de lluvia en pantalla principal
- **Problema**: OWM devuelve `pop` (probability of precipitation) solo en el endpoint `/forecast`, NO en `/weather`. La pantalla de reloj solo usaba current weather.
- **Solución**: Aprovechar el forecast ya cacheado — en `forecast_fetch()`, las entradas del día actual se saltan para el array `forecast_days[]` (pronóstico de días siguientes), pero ahora se **intercepta el `pop`** antes del `continue` para capturar la máxima probabilidad del resto del día.
- **Variables**: `static uint8_t today_pop` (0-100%) y `static bool today_pop_valid`.
- **Display — línea de POP siempre visible (y=212)**: La línea se dibuja SIEMPRE, incluso antes del primer fetch de forecast, para que el usuario vea la posición ocupada. Estados:
  - Sin datos (cargando) → `"Lluvia: --%"` en `COLOR_MUTED` (gris)
  - `today_pop > 0` → `"Lluvia: XX%"` en `COLOR_GREEN` (0x07E0, scale 2)
  - `today_pop == 0` → `"Sin lluvia"` en `COLOR_MUTED` (scale 2)
- **Posición**: y=212, scale 2 (26px), justo debajo de la descripción (y=184, scale 2).
- **Color**: `COLOR_GREEN` por preferencia. Originalmente era `COLOR_CYAN`.
- **Sensación eliminada**: La línea de sensación térmica se quitó porque no era de interés — liberó espacio vertical para que el POP subiera a scale 2.
- **Redibujo diferencial**: `display_clock()` detecta cambios en `today_pop` / `today_pop_valid` como parte de `weather_changed`, actualizando la línea sin flicker c/20 min.

### Fase 13 (v1.6) — Pantalla de boot con IP
- **`display_boot()`**: muestra "DeskMate" + IP asignada + SSID por ~5s al iniciar
- **`current_ip[16]`**: almacena la IP obtenida vía `IP_EVENT_STA_GOT_IP` con `snprintf(current_ip, sizeof(current_ip), IPSTR, IP2STR(&event->ip_info.ip))`
- **Boot flags**: `boot_done` y `boot_counter` controlan la transición boot→reloj
- Arranca con `lcd_fill_screen(COLOR_BLACK)`, dibuja título en scale 3, IP sin prefijo en scale 2 (verde si conectado), SSID en scale 1, barra de progreso animada
- Transición automática tras 5 iteraciones del bucle (~5s): `boot_done = true`, `clock_first_run = true`
- Resuelve el problema de IP cambiante tras reinicio de router o placa — la IP se ve en pantalla antes del reloj
- **IP fija no implementada**: `esp_netif_dhcpc_stop()` + `esp_netif_set_ip_info()` causa freeze total. Alternativa: reserva DHCP en router por MAC `8c:d0:b2:a9:f8:67`
- Commit: `e693130`

### Fase 12 (v1.5) — Control LED desde panel web (tipo WLED)
- **8 modos** (agregado SOLID): Pulse, Chase, Lamp, Rainbow, Candle, Aurora, Solid, Off
- **Color picker**: `<input type="color">` envía `led_color` con RGB vía WebSocket al cambiar
- **Slider de brillo**: 0-255, atenúa todos los LEDs en `send_leds()` vía multiplicación `(color * brightness) >> 8`
- **Botón ON/OFF**: toggle vía `led_power`, invierte `led_is_on()` si es necesario
- **cJSON en webserver**: `ws_handler` parsea comandos JSON entrantes y llama a `led_set_mode()`, `led_set_color()`, `led_set_brightness()`, `led_toggle_power()`
- **Nuevas API en led_control**: `led_set_color(r,g,b)`, `led_get_color()`, `led_set_brightness(b)`, `led_get_brightness()`
- **Modo SOLID**: `effect_solid()` aplica `solid_color` global a todos los LEDs. El color se configura desde el panel web y persiste aunque se cambie a otros modos
- **Commit**: `cac41ee`

### Fase 11 (v1.4) — WebSocket streaming de datos reales
- **ws_broadcast()**: envía JSON a todos los clientes WS conectados (max 4) vía `httpd_ws_send_frame_async()`
- **Tracking de clientes**: array `ws_fds[MAX_WS_CLIENTS]`, se agregan en handshake WS, se eliminan si falla envío
- **Datos enviados cada 1s** desde el bucle principal:
  - `{"type":"clock","time":"HH:MM:SS","wday":"Domingo","date":"DD/MM/YYYY"}`
  - `{"type":"weather","icon":"☀️","temp":30,"desc":"cielo claro","pop":"Sin lluvia"}`
  - `{"type":"forecast","days":[{label,icon,max,min,pop},...]}`
  - `{"type":"led","mode":0-6}`
- **Mapeo iconos→emoji**: `weather_emoji(code)` y `xbm_emoji(enum)` convierten códigos OWM y xbm_icon_t a emoji
- **Forecast JSON**: construye string dinámico con `snprintf` + `strncat` en buffer de 384 bytes
- **Commit**: `36e2902`

### Fase 10 (v1.3) — Panel web con HTTP + WebSocket

### Fase 9 (v1.2) — Anillo WS2812B con control RMT
- **GPIO 5** para el anillo WS2812B 8 LEDs (GPIO 8 ocupado por LED built-in de la placa)
- Conexión: `GPIO 5 → [330Ω] → DI del anillo`. Alimentación: 5V y GND directo del ESP32
- **8 modos** (ciclan con cada cambio de pantalla cada 15s, o desde panel web):
  - `PULSE` (0) — Respiración ámbar
  - `CHASE_RANDOM` (1) — 1 LED/segundo con color aleatorio vía `esp_random()`
  - `LAMP` (2) — Blanco cálido fijo
  - `RAINBOW` (3) — Arcoíris rotativo
  - `CANDLE` (4) — Velas parpadeantes
  - `AURORA` (5) — Azul/verde/violeta ondulante
  - `SOLID` (6) — Color sólido configurable (desde panel web)
  - `OFF` (7) — Apagado
- **Timing RMT corregido**: T_RESET=60µs (>50µs datasheet), orden GRB estándar WS2812B
- Archivos: `led_control.h` (API), `led_control.c` (driver RMT con lookup table seno 8-bit)
- `led_tick()` en bucle principal cada 1s, `led_cycle_mode()` en auto-rotación de pantalla
- Binario: 815KB (79.5% de partición 1MB). 210KB libres para panel web futuro
- **LED built-in**: no usar GPIO 8 para el anillo porque está conectado al LED onboard de la placa SuperMini
- **Anillo con LED defectuoso**: un LED no enciende (hardware). Los demás funcionan correctamente con todos los modos
- Commits: `ff814fc` (LED), `ab8f947` (layout), `55275bc` (refactor), `c8462dc` (v1)

### Fase 8 (v1.1) — Simplificación: sin botón, auto-rotación 15s
- **Eliminado**: `gpio_btn_init()`, `switch_to_next_screen()`, `btn_was_pressed`, `PIN_BUTTON` de pin_config.h
- **Auto-rotación**: `SCREEN_AUTO_ROTATE_SEC = 15`, sin condicional de botón
- **Bucle principal simplificado**: solo alterna pantallas cada 15s, sin handler de botón ni debounce
- **LED DeskLamp**: `led_cycle_mode()` fue eliminado de la auto-rotación en v1.6 (commit `63046ce`). El modo LED se controla 100% desde el panel web vía WebSocket. La auto-rotación de pantalla (15s) ya no afecta al anillo.

### Fase 1 — Driver display + test pattern
- Inicialización SPI a 40 MHz, RGB565, BGR order
- Pantalla de colores para verificar conectividad

### Fase 2 — Reloj NTP via WiFi
- WiFi station mode con retry
- SNTP con pool.ntp.org
- Zona horaria: São Paulo (BRT+3, UTC-3, sin DST)
- Display: hora+min+seg scale 4x (y=20, integrados HH:MM:SS), día scale 2x 8×13 teal (y=54), fecha scale 2x 8×13 muted (y=84)
- Icono WiFi 20×16 propio en esquina superior izquierda — símbolo clásico 3 arcos + punto de acceso (verde = conectado, rojo + X = desconectado)
- **Dos fuentes bitmap**: 5×7 (font_5x7.h) para hora, 8×13 (font_8x13.h) para día, fecha, clima, sensación

### Fase 3 — Clima OpenWeatherMap
- HTTP client con `esp_http_client` (patrón manual: open → fetch_headers → read)
- JSON parsing con `cJSON`
- Primer fetch 3s después del SNTP sync
- Auto-refresh cada 600s (10 minutos)
- Display: **icono + temperatura misma fila** (scale 3 amber), descripción centrada debajo (scale 2 white).
- Símbolo de grado ° (char 127) antes de C: `"20°C"` en lugar de `"20C"`

### Fase 4 — Iconos del clima XBM 32×32
- **22 iconos XBM** extraídos de proyecto open-source ([weather-icons](https://github.com/erikflowers/weather-icons) o similar)
- Formato X11 Bitmap: 32×32 px, 1 bit por pixel, 4 bytes por fila, **LSB-first** (bit 0 = píxel más a la izquierda del grupo de 8; ⚠️ error común usar MSB)
- **12 mapeados a OWM** vía `xbm_icon_from_code()`:
  - `01d` → SUN (sol) · `01n` → MOON (luna)
  - `02d` → CLOUD_SUN · `02n` → CLOUD_MOON
  - `03d/n` → CLOUD (nubes dispersas) · `04d/n` → CLOUDS (muy nublado)
  - `09d/n` → RAIN0 (lluvia ligera)
  - `10d` → RAIN1_SUN · `10n` → RAIN1_MOON (lluvia moderada día/noche)
  - `11d/n` → RAIN_LIGHTNING (tormenta)
  - `13d/n` → SNOW (nieve)
  - `50d/n` → WIND (niebla/viento)
- Función `lcd_draw_xbm()` — renderiza formato XBM (bytes, LSB-first) con escalado opcional.
- Icono se renderiza a **escala 2× (64×64)** para mejor visibilidad
- WiFi: icono propio de 20×16 — símbolo clásico de 3 arcos anidados (U invertida) + punto de acceso abajo. Verde cuando conectado, rojo con X cuando desconectado.

## Layout del display (240×240)
```
y=20:   14:09:32               (hora 5×7, scale 4, WHITE — HH:MM:SS misma línea)
y=54:   Domingo                 (día 8×13, scale 2, TEAL)
y=84:   19/07/2026              (fecha 8×13, scale 2, MUTED)
y=116:  ──────────────────────  (separador sutil COLOR_SEPARATOR)
y=118:  [☀️] [30°C]            (icono 64×64 + temp 8×13 scale 3 AMBER — misma fila)
y=184:  CIELO CLARO             (descripción 8×13 scale 2, WHITE)
y=212:  Lluvia: 60%             (probabilidad 8×13 scale 2, GREEN)
```
240/240px exactos. Sin sensación térmica. Todo scale ≥2 excepto hora (5×7 scale 4) y temp (scale 3).

### Notas de layout
- **5×7 font** se usa para hora (scale 4) — HH:MM:SS todo en la misma línea.
- **8×13 font** se usa para día (scale 2), fecha (scale 2), temperatura (scale 3), descripción (scale 2) y POP (scale 2).
- El grupo [icono 64×64 + gap 10px + temp°C] se centra dinámicamente según el ancho real del texto — a scale 3 cada carácter 8×13 ocupa 24px (~120px para -15°C, ~96px para 20°C). La temperatura se posiciona verticalmente centrada respecto al icono.
- **Descripción a scale 2**: se muestra a 18px/char, max ~13 caracteres. Las descripciones largas se truncan (ver Pitfall #11).
- **Símbolo de grado °**: Char 127 en ambas fuentes. `snprintf(buf, sizeof(buf), "%d%cC", temp_i, 127)` — genera "20°C".
- **Truncado de descripción**: Se usa `snprintf(buf, sizeof(buf), "%.*s", max_chars, desc)` donde `max_chars = (LCD_WIDTH - 4) / ((FONT8_WIDTH + 1) * 2)` para scale 2.
- Sin anti-aliasing (revertido por washout en trazos finos — ver Pitfall #11).
- Paleta profesional: TEAL (día), AMBER (temp), GREEN (POP lluvia), MUTED (fecha), WHITE (descripción).
- Altura total usada: 240/240px — ajuste exacto.

## Archivos del proyecto
- `main/main.c` — Código principal: init SPI, ST7789, WiFi, SNTP, HTTP, forecast, display + iconos + dibujo diferencial anti-flicker + fuentes 5×7 y 8×13 + probabilidad de lluvia + integración LED
- `main/led_control.h` — API de control LED WS2812B: 8 modos + color/brightness, GPIO 5, RMT
- `main/led_control.c` — Driver WS2812B vía RMT: encoder RGB, lookup seno 8-bit, 6 efectos
- `main/include/pin_config.h` — Pines ST7789 (MOSI=GPIO6, SCLK=GPIO9, CS=GPIO21, DC=GPIO10, RST=GPIO4), WiFi SSID/PASS, TIMEZONE, OWM config (sin PIN_BUTTON)
- `main/include/font_5x7.h` — Fuente bitmap 5×7 (95 chars ASCII 32-126, 13 bytes/char = 1235B de datos)
- **`main/include/font_8x13.h`** — Fuente bitmap 8×13 (96 chars ASCII 32-127, 13 rows/char, 1248B de datos). Diseño sans-serif limpio, generada con Python.
- `main/include/weather_icons.h` — **22 iconos XBM 32×32** (12 mapeados a OWM) + `xbm_icon_t` enum + `xbm_icon_from_code()` + `xbm_icons[]` lookup table
- `main/webserver.h` — API del servidor web: `start_webserver()`, `stop_webserver()`
- `main/webserver.c` — Servidor HTTP + WebSocket nativo, HTML/CSS/JS dashboard embebido (~9KB)
- `main/CMakeLists.txt` — REQUIRES: esp_lcd, esp_driver_spi, driver, esp_event, esp_netif, esp_wifi, nvs_flash, lwip, esp_http_client, json, esp_http_server
- `CMakeLists.txt` — Project "deskmate"
- `sdkconfig` — CONFIG_ESP_MAIN_TASK_STACK_SIZE=8192 (necesario por HTTP client)
- `tools/gen_font_8x13.py` — Script Python para regenerar font_8x13.h
- `tools/check_fit.py` — Script Python para verificar si descripciones OWM caben en el display con fuente 8×13 (ver `references/owm-spanish-descriptions.md`)

## Build & Flash
```bash
. /home/migbert/.espressif/v5.5.3/esp-idf/export.sh
cd /home/migbert/proyectos/deskmate
idf.py build
fuser -k /dev/ttyACM0 2>/dev/null  # liberar puerto si ocupado
idf.py flash -p /dev/ttyACM0
```

## Monitor serial
```bash
python3 -c "
import serial, time
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=2)
time.sleep(1)
ser.reset_input_buffer()
start = time.time()
while time.time() - start < 20:
    try:
        data = ser.read(ser.in_waiting or 1).decode('utf-8', errors='replace')
        if data: print(data, end='', flush=True)
    except: pass
ser.close()
"
```

## WiFi
- SSID: Sukuna-78-2.4g
- IP: 192.168.1.14 (DHCP)
- MAC: 8c:d0:b2:a9:f8:67

## OpenWeatherMap
- City: Joinville, BR (ID: 3459712)
- Units: metric
- Lang: es
- API key en pin_config.h como OWM_API_KEY

## Separador visual
Una línea horizontal sutil entre la fecha (y=116) y el icono del clima:
```c
lcd_draw_rect(24, 116, LCD_WIDTH - 48, 1, COLOR_SEPARATOR);
```
Renderizada una sola vez en `first_run`. El área de actualización diferencial del clima comienza en y=114, por lo que el separador nunca se borra.

## Colores RGB565
```c
#define COLOR_BLACK      0x0000
#define COLOR_WHITE      0xFFFF
#define COLOR_RED        0xF800
#define COLOR_GREEN      0x07E0
#define COLOR_BLUE       0x001F
#define COLOR_CYAN       0x07FF
#define COLOR_MAGENTA    0xF81F
#define COLOR_YELLOW     0xFFE0
#define COLOR_ORANGE     0xFD20  // R=31, G=18, B=0
#define COLOR_GRAY       0x8410
#define COLOR_DARK_GRAY  0x4208

/* Paleta profesional */
#define COLOR_AMBER     0xFD60  // R=31, G=22, B=0 — ámbar cálido (temperatura)
#define COLOR_TEAL      0x06BF  // R=0,  G=13, B=31 — teal (día)
#define COLOR_SOFT_WHITE 0xBDD7 // R=23, G=26, B=31 — blanco ligeramente azulado (segundos)
#define COLOR_MUTED     0xAD55  // R=21, G=21, B=21 — gris claro elegante (fecha)
#define COLOR_SEPARATOR 0x2945  // R=5,  G=9,  B=10 — línea divisoria sutil
```

## Pitfalls conocidos

1. **Stack overflow**: `esp_http_client` + `cJSON` usan mucha stack. Aumentar CONFIG_ESP_MAIN_TASK_STACK_SIZE a 8192.

2. **HTTP read**: NO usar `esp_http_client_perform()` — consume el body internamente. Usar patrón manual: `open() → fetch_headers() → read()`.

3. **Puerto ocupado**: `fuser -k /dev/ttyACM0` antes de flashear.

4. **Espacio en partición**: ~78% usado tras optimizaciones (818KB, 22% libre). Se liberaron ~196KB con: compilación -Os, deshabilitar IPv6, DHCPS, mDNS, IP fragmentation, asserts, y eliminar lcd_draw_bitmap(). Suficiente para sensores DHT o WS2812B.

5. **Monitor no interactivo**: Usar script Python con pyserial en lugar de miniterm o idf.py monitor (requieren TTY). El script de monitor serial en este skill funciona sin TTY.

6. **lcd_draw_bitmap() deprecated**: Reemplazada por `lcd_draw_xbm()`. La función vieja ya no se usa.

7. **XBM bit ordering — MSB ≠ LSB (⚠️ GOTCHA!)**: El formato X11 Bitmap estándar usa **LSB-first**: el bit 0 de cada byte corresponde al píxel más a la izquierda de su grupo de 8. Es intuitivo asumir MSB-first (bit más significativo primero), pero eso da iconos deformes/feos.

8. **lcd_draw_xbm() single-byte write**: Esta función escribe pixel por pixel y es lenta. Para 32×32 es aceptable, pero para imágenes grandes usar DMA.

9. **Iconos pequeños: diseño manual > algoritmo matemático (⚠️ GOTCHA!)**: Para iconos de menos de ~24px, dibujar curvas con algoritmos (ej. arcos trigonométricos) produce píxeles dispersos que el ojo no reconoce como formas familiares — parecen "ruido". Usar formas geométricas simples. El símbolo WiFi clásico de 3 arcos funciona bien cuando se dibuja como **U-invertidas horizontales** (trapecios con laterales verticales) en vez de arcos curvos reales.

10. **Parpadeo/flicker del display (⚠️ IMPORTANTE)**: `lcd_fill_screen(COLOR_BLACK)` + redibujar TODO cada segundo causa parpadeo visible. **Solución: dibujo diferencial**. Solo redibujar regiones que cambian. Usar `lcd_draw_rect()` para limpiar áreas en vez de `fill_screen()`. Trackear cambios con `static` vars.

11. **Límite de texto en fuente 8×13 a scale 2 (⚠️ DISEÑO — ACTUALIZADO)**: La descripción del clima se muestra a scale 2 (18px/char), máximo ~13 caracteres en 240px. Descripciones como `"tormenta electrica con llovizna intensa"` (39 chars) se truncan a 13 chars — suficiente para el significado. El cálculo es `max_chars = (LCD_WIDTH - 4) / ((FONT8_WIDTH + 1) * 2)`. Antes de este cambio, la descripción estaba a scale 1 (26 chars) y las descripciones más largas se truncan menos agresivamente. **Trade-off aceptado**: ganamos legibilidad a costa de menos texto visible.

12. **Símbolo de grado ° (char 127)**: La fuente 8×13 tiene el símbolo de grado en la posición ASCII 127. Para usarlo: `snprintf(buf, sizeof(buf), "%d%cC", temp_i, 127)` → `"20°C"`. El símbolo está definido en las últimas líneas de `font_8x13.h` (línea ~1538+).

13. **Centrado dinámico de icono + temperatura**: El grupo [icono 64×64 + gap 10px + temp°C] se centra calculando `group_w = 64 + 10 + text_width_8x13(temp_str, 3)` y luego `group_x = (240 - group_w) / 2`. Esto evita que la temperatura se desalinee cuando cambia de "20°C" a "5°C" o "-15°C".

14. **Forecast JSON buffer — límite real (⚠️ MEMORIA - ACTUALIZADO v2.4)**: El forecast OWM puede devolver ~15-20KB de JSON (16,681 bytes verificado el 2026-06-19). **NO usar 16384 (16KB) — el JSON se trunca y `cJSON_Parse()` falla**, dejando la pantalla de pronóstico mostrando "Sin datos". Usar `FORECAST_BUFFER_MAX=20000` (20KB) en heap `malloc`/`free`. Verificar periódicamente con `curl` el tamaño real de la respuesta de `api.openweathermap.org/data/2.5/forecast`.

15. **Agrupación por día sin strings**: Para evitar warnings del compilador con `snprintf` y `int` de `struct tm` (que gcc asume rango completo INT_MIN-INT_MAX), usar entero compuesto `date_key = (year+1900)*10000 + (mon+1)*100 + mday`. Simple y eficiente.

16. **Auto-rotación**: Configurable vía `SCREEN_AUTO_ROTATE_SEC` (actualmente 15s). Alterna entre clock y forecast automáticamente. Sin botón. El modo del anillo LED es 100% manual desde el panel web — `led_cycle_mode()` fue eliminado de la auto-rotación en commit `63046ce`.

17. **GPIO 3 liberado**: El botón y su código (`gpio_btn_init()`, debounce, `switch_to_next_screen()`) se eliminaron en v1.1. GPIO 3 y `PIN_BUTTON` ya no están en pin_config.h. Si se quiere reactivar un botón en el futuro, GPIO 3, 5, 7, 10 o 20 están libres.

18. **`wifi_connected` nunca se actualiza en event handlers (⚠️ GOTCHA!)**: La variable `static bool wifi_connected = false;` se declara y usa en `display_status_bar()` para el icono WiFi, pero **NUNCA se le asigna `true`** en los event handlers. Sin las siguientes líneas, el icono WiFi siempre se muestra rojo aunque la conexión funcione:
    - En el handler `IP_EVENT_STA_GOT_IP`: añadir `wifi_connected = true;`
    - En el handler `WIFI_EVENT_STA_DISCONNECTED`: añadir `wifi_connected = false;`
    Es fácil pasar por alto porque la conexión WiFi funciona, solo el indicador visual falla.

19. **Weather refresh sobrescribe datos válidos en fetch fallido (⚠️ IMPORTANTE)**: En el bucle principal, la línea `weather_data = weather_fetch();` asigna incondicionalmente el resultado de `weather_fetch()`. Si el HTTP falla (timeout, desconexión WiFi), la función retorna `valid = false` y se pierden los datos previos válidos — el display muestra "Clima: --" aunque antes tenía datos buenos. **Solución**: usar variable temporal y solo asignar si el fetch fue exitoso:
    ```c
    weather_data_t new_data = weather_fetch();
    if (new_data.valid) {
        weather_data = new_data;
    }
    ```
    Aplicar el mismo patrón a cualquier fetch que sobrescriba datos globales desde el bucle principal.

20. **`pop` (probabilidad de lluvia) solo está en el endpoint forecast, NO en current weather (⚠️ DISEÑO OWM)**: OWM no incluye `pop` en `/data/2.5/weather`. Si intentas parsearlo del current weather, siempre será 0. Solo `/data/2.5/forecast` lo devuelve (por entrada 3h). Para mostrarlo en la pantalla de reloj:
    - **Solución implementada**: Interceptar las entradas del día actual en `forecast_fetch()` antes del `continue` que las salta. Extraer el `pop` máximo en variables globales `today_pop` / `today_pop_valid`.
    - Se resetean al inicio de cada `forecast_fetch()` (c/20 min) para evitar datos obsoletos.
    - Aparece ~3-10s tras el boot (después del primer fetch de forecast).

21. **`xEventGroupCreate()` olvidado → crash en IP obtenida (⚠️ GOTCHA! RECONSTRUCCIÓN)**: `wifi_event_group` es una variable global `EventGroupHandle_t` que **debe** inicializarse con `xEventGroupCreate()` antes de registrar cualquier event handler. Si se omite (ej. al reconstruir app_main()), el handler `IP_EVENT_STA_GOT_IP` crashea con `Guru Meditation: Load access fault` llamando a `xEventGroupSetBits()` con un handle NULL. El crash ocurre exactamente después del log "IP obtenida: X.X.X.X". Síntoma: el ESP se reinicia en bucle en boot, siempre en el mismo punto.
    - **Diagnóstico**: addr2line del crash PC revela `xEventGroupSetBits at event_groups.c:580`.
    - **Fix**: Agregar `wifi_event_group = xEventGroupCreate();` en app_main(), antes de wifi_init().
    - **Prevención**: Cuando reconstruyas app_main() (por cualquier razón), verificar que TODAS las variables globales se inicialicen: panel_handle, wifi_event_group, time_synced, wifi_connected, etc.

22. **`nvs_flash_init()` antes de WiFi (⚠️ GOTCHA!)**: ESP-IDF requiere llamar `nvs_flash_init()` al inicio de app_main(), antes de `wifi_init()`. Sin esto, el driver WiFi muestra `wifi:config NVS flash: disabled` o `wifi:osi_nvs_open fail ret=4353` (ESP_ERR_NVS_NOT_INITIALIZED) y falla al arrancar. Patrón estándar:
    ```c
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    ```
    Si el código compila pero WiFi no arranca, verificar que nvs_flash_init() esté presente antes de esp_netif_init().

23. **addr2line para ESP32-C3 es RISC-V, no Xtensa (⚠️ HERRAMIENTA)**: ESP32-C3 usa arquitectura RISC-V, no Xtensa como ESP32 clásico. La herramienta correcta es `riscv32-esp-elf-addr2line` (no `xtensa-esp32c3-elf-addr2line`). Para decodificar un crash PC:
    ```bash
    riscv32-esp-elf-addr2line -pfia -e build/deskmate.elf 0x40386f94 0x42098f72
    ```
    Buscar el ejecutable en `~/.espressif/tools/riscv32-esp-elf/.../bin/` — generalmente ya está en el PATH después de export.sh. Las direcciones se obtienen del dump MEPC (PC del crash) y las direcciones de retorno (valores 0x4xxxxx en el stack dump).

24. **Parchar C source en remoto con Python — brace matching frágil con prototipos (⚠️ PRÁCTICA — EVITAR)**: Usar Python `content.find('{', start_idx)` para encontrar el brace de apertura de una función es peligroso cuando hay prototipos de función ANTES de la definición. El prototipo `static void foo(void);` contiene la cadena buscada pero NO tiene `{`. find() encuentra el primer brace después del prototipo, que suele ser el de la siguiente función con cuerpo. Esto produce un reemplazo que destruye funciones enteras.
    - **Alternativa segura**: Para parches pequeños, usar `patch()` tool (fuzzy find-and-replace). Para cambios complejos, escribir el archivo completo desde cero. Si es necesario usar Python, delimitar con marcadores únicos (comentarios `// PATCH_MARKER` en C) o buscar por el patrón completo `static void nombre(void)\\n{` (con newline + brace incluidos).
    - **Si se rompe**: No tener `git` en el ESP32 es un problema. Hacer backup antes: `cp main.c main.c.bak`.
    - **Verificación**: Después de cualquier parche que modifique el flujo de control, verificar que todas las funciones principales estén intactas con un grep rápido de los encabezados.

25. **COLOR_MAGENTA se ve verdoso en ST7789 (⚠️ COLOR — GOTCHA)**: En el display ST7789 de este modelo, `COLOR_MAGENTA` (0xF81F, R=31, G=0, B=31) aparece con un tono verdoso en lugar de magenta puro. Esto se debe a la calibración del panel o al orden BGR del driver. **Preferencia del usuario**: usa `COLOR_CYAN` (0x07FF) para la temperatura y `COLOR_GREEN` (0x07E0) para el POP de lluvia. Si necesitas un tono cálido, usa `COLOR_AMBER` (0xFD60) en lugar de rojo o magenta.

26. **Línea de POP siempre visible como ancla de layout (⚠️ UX)**: La probabilidad de lluvia se dibuja con `if (today_pop_valid)` que solo es `true` después del primer fetch de forecast (~3-10s post-boot). Hasta entonces la línea no existe y el ojo no ve el espacio reservado. **Solución**: eliminar el `if` guard y dibujar siempre la línea — con `"Lluvia: --%"` en `COLOR_MUTED` mientras no hay datos. Esto le confirma al usuario que la posición está ocupada y evita que piense que el POP "no se ve" o quedó fuera de pantalla. Aplicar este patrón a cualquier línea condicional que demore en aparecer.

27. **Espacio vertical ajustado a 240px (⚠️ LAYOUT — v3.2)**: Layout actual verificado (sin sensación, POP scale 2, día/fecha scale 2, HH:MM:SS integrado):
    - y=20: HH:MM:SS → 28px → [20-48]
    - y=54: día scale 2 → 26px → [54-80]
    - y=84: fecha scale 2 → 26px → [84-110]
    - y=116: separador → 1px → [116]
    - y=118: icono 64×64 → [118-182]
    - y=184: desc scale 2 → 26px → [184-210]
    - y=212: POP scale 2 → 26px → [212-238]
    238/240px usados. Cualquier elemento nuevo requiere reducir gaps o escalas.

28. **`patch()` tool con comentarios C — `/*` anidados (⚠️ HERRAMIENTA)**: Al usar `patch()` para reemplazar bloques de comentarios C (`/* ===... */`) que incluyen el inicio de otro comentario en el old_string, el resultado puede ser `/* =` seguido de `/* texto` produciendo `"/*" within comment` (-Werror=comment). El compilador trata esto como error fatal con `-Werror`.
    - **Síntoma**: `error: "/*" within comment [-Werror=comment]` en la línea del comentario de bloque.
    - **Fix**: Reemplazar todo el bloque de comentario incluyendo líneas contiguas en un solo patch, asegurando que el new_string use `*` (asterisco) para las líneas intermedias, no `/*`.
    - **Prevención**: Preferir `//` comentarios de una línea para separadores en C cuando sea posible, o verificar el diff después de cada patch en archivos .c.
    - **Detección**: `grep -n '/\*.*/\*' main/*.c` encuentra comentarios anidados antes de compilar.

29. **Display no muestra nada pero el firmware SÍ corre (⚠️ DIAGNÓSTICO)**: Si el monitor serial muestra WiFi conectado, NTP sincronizado, weather fetch exitoso, y el reloj avanza ("13:36:47 - Domingo"), pero la pantalla está negra, el firmware NO es el problema. **Causa #1: backlight (BL/LED) no conectado a 3.3V** — sin esto la pantalla está completamente negra aunque el chip reciba datos correctamente. Otras causas:
    - **VCC del display conectado a 5V en vez de 3.3V** (el ST7789 es 3.3V)
    - **GND del display no conectado** (sin referencia común no hay señal)
    - **Cable suelto o mal contacto** en cualquiera de los pines SPI (MOSI, SCLK, CS, DC, RST)
    - **Display dañado** (raro pero posible si se conectó a 5V)
    - **Diagnóstico rápido**: medir con multímetro que el pin BL tenga 3.3V respecto a GND. Si el monitor serial funciona, el ESP32 está bien — el problema es solo el display o su cableado.

30. **`/dev/ttyACM0` desaparece tras `fuser -k` (⚠️ TIMING)**: `fuser -k /dev/ttyACM0` puede causar que el dispositivo se desregistre brevemente del kernel. Si inmediatamente después intentas flashear, el puerto no existe. **Solución**: esperar 2-3 segundos tras `fuser -k` para que el dispositivo se re-registre, o verificar con `ls /dev/ttyACM0` antes de flashear. Si el puerto no reaparece, reconectar físicamente el USB.

31. **`git checkout` sin commit previo → pérdida total de cambios no commiteados (⚠️ GIT — CRÍTICO)**: Si el proyecto tiene un solo commit inicial y todos los cambios posteriores están en el working tree sin commit, ejecutar `git checkout -- <file>` **revierte irreversiblemente a la versión del último commit**, perdiendo semanas de trabajo. En este proyecto ocurrió: al hacer `git checkout` para revertir 3 archivos del módulo LED, se perdieron fixes de layout, botón, POP scale 2, y sensación eliminada que estaban en el working tree. **Regla**: NUNCA hacer `git checkout` en un proyecto con cambios no commiteados. Alternativas seguras:
    - **Antes de revertir**: `git stash` o `git commit -am "wip: checkpoint antes de revertir"` (el commit se puede deshacer después con `git reset --soft HEAD~1`)
    - **Para revertir archivos específicos**: hacer backup manual `cp main/main.c main/main.c.bak` antes del checkout
    - **Para recuperar trabajo perdido**: si no hay stash ni commit, la única opción es reconstruir desde el skill — por eso este skill documenta CADA cambio en detalle
    - **Verificación**: `git status` y `git diff --stat` ANTES de cualquier checkout. Si hay cambios, commitear primero.

32. **`vTaskDelay` eliminado accidentalmente durante refactor (⚠️ PARCHES — CRÍTICO)**: Al quitar bloques grandes de código con `patch()`, es fácil eliminar el `vTaskDelay(pdMS_TO_TICKS(1000))` del final del bucle principal. Sin este delay, el bucle corre a máxima velocidad (~50 iteraciones/segundo), causando: rotación de pantalla cada ~200ms, logs a máxima velocidad, hora aparentemente estancada (mismo segundo repetido 10+ veces). **Síntomas en monitor**: múltiples prints del mismo segundo, "Cambiando a pantalla" cada ~400 ticks. **Verificación post-parche**: `grep -n 'vTaskDelay' main/main.c` debe devolver al menos una línea dentro del `while(1)`. Si no, agregarlo inmediatamente antes de compilar.

33. **`xTaskGetTickCount()` NO es para timing real (⚠️ GOTCHA)**: `xTaskGetTickCount()` devuelve ticks del scheduler FreeRTOS, no segundos reales. Dividir entre 1000 (`xTaskGetTickCount() / 1000`) NO convierte a segundos — en ESP-IDF con tick de 10ms, 1000 ticks = 10 segundos. **Solución**: usar `time_t now; time(&now); uint32_t now_sec = (uint32_t)now;` para obtener segundos Unix reales. Esto es esencial para los intervalos de refresco de clima (WEATHER_INTERVAL=600s) y forecast. Sin este fix, los refrescos nunca se disparan correctamente.

34. **Anillo WS2812B — GPIO 8 vs GPIO 5 (⚠️ PLACA)**: En el ESP32-C3 SuperMini de este proyecto, GPIO 8 está conectado al LED built-in de la placa. Usar GPIO 8 para el anillo WS2812B causa conflicto. **Usar GPIO 5 o GPIO 7** en su lugar. La resistencia en serie con DIN puede ser 220Ω–470Ω (330Ω funciona bien). El pin DO del anillo se deja sin conectar. Ver `desklamp` skill para detalles completos del hardware.

35. **WS2812B — orden de color GRB estándar (⚠️ COLOR)**: El estándar WorldSemi WS2812B usa orden **GRB**. Si los colores se ven mal (rojo↔verde intercambiados, blanco sale rosado/verdoso), probar `{ c.r, c.g, c.b }` (RGB) en `encode_rgb()`. El anillo de este proyecto (Shopee BR 2026) resultó ser GRB genuino. Modo LAMP (blanco cálido) debe verse ámbar, no rosado. Ver skill `desklamp` para detalles de timing y diagnóstico.

36. **WS2812B T_RESET debe ser >50µs (⚠️ TIMING — DATASHEET)**: El datasheet WS2812B exige reset mínimo de 50µs entre frames. Con RMT a 10MHz (100ns/tick), se necesitan ≥500 ticks. El código original usaba T_RESET=300 (30µs) causando comportamiento errático: todos los LEDs en blanco fijo, colores incorrectos, efectos que no se ejecutan. **Fix**: `#define T_RESET 600` (60µs). Timings óptimos verificados: T0H=4, T0L=8, T1H=8, T1L=4 (todos dentro de tolerancia datasheet ±150ns). Síntomas de T_RESET corto: LEDs no responden a cambios de color, se quedan en un estado fijo, o muestran colores aleatorios.

38. **Panel web requiere `CONFIG_HTTPD_WS_SUPPORT=y` (⚠️ SDKCONFIG — GOTCHA)**: El soporte WebSocket en el HTTP server de ESP-IDF está deshabilitado por defecto en sdkconfig. Sin esta opción, `httpd_ws_frame_t`, `HTTPD_WS_TYPE_TEXT`, `httpd_ws_recv_frame()`, y `.is_websocket` **no existen** — el compilador lanza `unknown type name 'httpd_ws_frame_t'` y `'httpd_uri_t' has no member named 'is_websocket'`. **Fix**: `CONFIG_HTTPD_WS_SUPPORT=y` en sdkconfig. **Verificación**: `grep 'CONFIG_HTTPD_WS' sdkconfig` debe devolver `=y`, no `is not set`.

39. **Panel web requiere `LWIP_MAX_SOCKETS ≥ 12` (⚠️ SDKCONFIG — GOTCHA)**: El HTTP server necesita `max_open_sockets + 3` sockets internos. Con `LWIP_MAX_SOCKETS=4` (default), `httpd_start()` falla con error `"Config option max_open_sockets is too large (max allowed 1, 3 sockets used by HTTP server internally)"`. El ESP32-C3 necesita espacio para HTTP server (7), WebSocket (1), WiFi (2), HTTP client weather (2) = mínimo 12. **Fix**: `CONFIG_LWIP_MAX_SOCKETS=12` en sdkconfig. **Diagnóstico en monitor**: aparece `E (xxxxx) httpd:` seguido de `E (xxxxx) web: Error al iniciar servidor`. El resto del firmware (display, clima, LED) funciona normal — solo el servidor web no arranca.

40. **`start_webserver()` debe llamarse DESPUÉS de WiFi conectado (⚠️ ORDEN)**: Si se llama a `httpd_start()` antes de que el WiFi obtenga IP, el servidor falla porque el stack TCP/IP no está listo. En el código de `web_led` (PlatformIO), el orden era `wifi_init_sta()` → `start_webserver()`, pero `wifi_init_sta()` era síncrono (esperaba conexión). En DeskMate, `wifi_init()` es asíncrono. **Fix**: mover `start_webserver()` después del bucle `while (!time_synced)` que espera NTP — en ese punto WiFi ya tiene IP garantizada. **Síntoma**: `curl http://<IP>/` devuelve `Connection refused` aunque el ESP32 responde a ping. El monitor serial no muestra errores porque `start_webserver()` aún no se ejecutó o falló silenciosamente.

41. **Buscar IP del ESP32 tras reboot — DHCP puede cambiar (⚠️ RED)**: Después de cada flash, el ESP32 puede obtener una IP diferente vía DHCP. La MAC es `8c:d0:b2:a9:f8:67` pero `arp` no siempre está disponible. **Búsqueda rápida**: escanear puerto 80 en IPs comunes (`192.168.1.9`, `.10`, `.11`, `.12`, `.14`) o usar `nmap -p80 --open 192.168.1.0/24`. La IP 192.168.1.14 está ocupada por un repetidor WiFi — verificar que la respuesta HTML contenga "DeskMate" para confirmar que es el ESP32 y no otro dispositivo. La pantalla de boot (`display_boot()`) muestra la IP asignada durante ~5s al iniciar — solución sin escaneo manual.

42. **IP fija vía `esp_netif_dhcpc_stop()` + `esp_netif_set_ip_info()` causa freeze total (⚠️ GOTCHA)**: Intentar asignar IP estática con `esp_netif_dhcpc_stop(netif)` → `esp_netif_set_ip_info()` hace que el ESP32 se congele en boot sin ninguna salida serial. **Síntomas**: flash exitoso, `/dev/ttyACM0` visible, pero el monitor serial está muerto — ni siquiera los logs de `app_main()` aparecen. El chip responde a `esptool.py read_mac` pero no ejecuta el firmware. **Causa probable**: el netif no está en un estado que acepte `dhcpc_stop()` antes de `wifi_start()`. **Soluciones**:
   - (RECOMENDADA) **Reserva DHCP en el router** — configura IP fija en el servidor DHCP por MAC. Cero código, cero riesgo. La mayoría de los routers tienen "DHCP Reservation" o "Static DHCP".
   - **mDNS** — agregar `espressif/mdns^1.3.0` vía `idf.py add-dependency` permite acceder por `http://deskmate.local/`. Agrega ~15-20KB al binario, requiere configurar el servicio en código (~15 líneas).
   - NO intentar IP fija en firmware a menos que se siga exactamente el ejemplo oficial de ESP-IDF `examples/networking/static_ip`.
- `references/supermini-pinout.md` — Pinout completo del ESP32-C3 SuperMini de este proyecto, con GPIOs usados/libres.
- `references/wttrin-vs-owm-comparison.md` — Comparativa técnica entre wttr.in y OWM para ESP32 (tamaño JSON, API key, iconos XBM, parsing). Decisión: OWM es superior para DeskMate. — Detalle de bugs corregidos: `wifi_connected` nunca actualizado y weather refresh sobrescribiendo datos válidos.
- `references/owm-spanish-descriptions.md` — Lista completa de las 55 descripciones OWM en español con conteo de caracteres.
- `references/owm-forecast-5-api.md` — Documentación del endpoint 5 Day / 3 Hour Forecast, campo `pop`, y estrategia de implementación para ESP32-C3.
- `references/forecast-debug-diagnosis.md` — Procedimiento sistemático para diagnosticar "Sin datos" en la pantalla de pronóstico: buffer insuficiente, HTTP failures, time sync, formato JSON.
- `scripts/check_fit.py` — Script Python que calcula si las descripciones OWM caben en el display a escala 1 y 2.
- `references/webserver-ws-esp32-setup.md` — Configuración de WebSocket, IP fija, comandos JSON, emoji mapping. Ejecutar desde el directorio del proyecto: `python3 scripts/check_fit.py` (o la copia en `tools/check_fit.py`).

## Posibles siguientes pasos
- Humedad + presión atmosférica (OWM ya los devuelve, solo falta parsearlos)
- DHT11 sensor temp/humedad local
- Alarma / timer configurables
- Micrófono MAX4466 para modo "music reactive" con FFT en el anillo
