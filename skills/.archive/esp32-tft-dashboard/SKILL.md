---
name: esp32-tft-dashboard
description: "Build IoT desk dashboard panels with ESP32 (especially ESP32-C3 Super Mini) and ST7789 TFT displays: NTP clock, weather via OpenWeatherMap, local sensors (DHT11, LDR, PIR), WS2812B LEDs, encoder-based menu navigation, WiFi web control, and ESP-IDF native approach."
trigger:
  - "ESP32 desk dashboard project"
  - "IoT display with ESP32 and ST7789"
  - "ESP32-C3 Super Mini + TFT"
  - "Smart desk panel with sensors and LEDs"
  - "Pantalla ESP32 con ST7789 para escritorio"
  - "ESP32 + TFT display project"
  - "Building an ESP32 smart display with sensors"
  - "ESP32-C3 Super Mini TFT ST7789 wiring"
  - "ESP-IDF native ST7789 driver esp_lcd"
  - "ESP32-C3 NTP clock ESP-IDF"
  - "Font bitmap 5x7 ESP32"
  - "WiFi SNTP ESP32-C3 ESP-IDF"
  - "ESP32 OpenWeatherMap HTTP cJSON ESP-IDF"
  - "Weather display ESP32-C3 ST7789"
  - "ESP32 HTTP client fetch headers read pattern"
---

# ESP32 TFT Dashboard — Panel de Escritorio IoT

Guía para construir un panel de escritorio inteligente con **ESP32-C3 Super Mini** + **pantalla ST7789** (240×240), sensores, iluminación LED y conectividad WiFi.

> **Español recomendado** para la conversación y comentarios en código si el usuario es hispanohablante. La API del clima y los logs pueden quedar en inglés para compatibilidad.

---

## 📦 Hardware

| Componente | Propósito |
|---|---|
| **ESP32-C3 Super Mini** | RISC-V single-core @160MHz, WiFi/BLE |
| **ST7789 SPI** | 240×240 TFT a color — reloj, clima, sensores |
| **DHT11 / DHT22 / BME280** | Temperatura y humedad local |
| **WS2812B (NeoPixel)** | Tira LED direccionable para iluminación de escritorio |
| **LDR + resistor 10kΩ** | Sensor de luz ambiental para brillo automático |
| **Encoder rotatorio KY-040** | Navegación entre pantallas del menú |
| **PIR sensor (opcional)** | Detección de presencia para activar pantalla |

---

## ⚠️ ESP32-C3 Super Mini — Pines conflictivos

La placa tiene **13 GPIOs** pero varios tienen restricciones:

| GPIO | Problema | Recomendación |
|---|---|---|
| **GPIO 2** | Strapping pin — debe estar HIGH en boot | **NO USAR** |
| **GPIO 8** | Strapping + LED onboard (active low) | **NO USAR** — además interfiere con I2C y boot |
| **GPIO 9** | Strapping + botón BOOT | Solo para RST del display (configurar como salida en setup) o **evitar** |
| **GPIO 20** | UART0 RX por defecto | Usable como GPIO **después** de subir código |
| **GPIO 21** | UART0 TX por defecto | Usable como GPIO **después** de subir código |

**Pines seguros para uso general:** GPIO 0, 1, 3, 4, 5, 6, 7, 10, 20, 21

La placa opera a **3.3V exclusivamente** — NO conectar nada a 5V en los GPIOs.

---

## 🔌 Cableado típico (ST7789 + sensores + LEDs)

```
ST7789 display:
  SDA  →  GPIO 6   (MOSI)
  SCL  →  GPIO 9   (SCLK — usable via GPIO Matrix)
  DC   →  GPIO 10
  CS   →  GPIO 21
  RST  →  GPIO 4   (o conectar a EN del ESP32 y poner TFT_RST = -1)
  BL   →  3.3V     (o PWM vía transistor para brillo ajustable)
  VCC  →  3.3V
  GND  →  GND

DHT11:
  DATA →  GPIO 4   (con pull-up 10kΩ a 3.3V) — no compartir con RST del display

WS2812B:
  DIN  →  GPIO 5
  VCC  →  5V
  GND  →  GND

LDR (fotoresistencia):
  Pin A →  3.3V  (vía resistor 10kΩ a GND — divisor de voltaje)
  Pin B →  GPIO 0 (ADC)

Encoder KY-040:
  CLK  →  GPIO 3
  DT   →  GPIO 1
  VCC  →  3.3V
  GND  →  GND
```

> **Nota:** Conecta RST del display a EN del ESP32 si quieres liberar un pin. En el código usa `#define TFT_RST -1`.

---

## 🧩 Librerías (PlatformIO / Arduino IDE)

| Librería | Propósito |
|---|---|
| **TFT_eSPI** (Bodmer) | Driver para ST7789 — requiere archivo de setup personalizado |
| **WiFi** / **HTTPClient** | Conectividad WiFi + llamadas a API |
| **ArduinoJson** (v6+) | Parsear respuesta JSON del clima |
| **Adafruit_NeoPixel** | Tira LED RGB |
| **DHT sensor library** | DHT11/DHT22 |
| **RotaryEncoder** | Navegación por encoder |
| **NTPClient** | Hora sincronizada por internet |

---

## 🛠️ TFT_eSPI — Setup personalizado

TFT_eSPI necesita un archivo de configuración de pines. La forma más limpia:

1. Localizar la carpeta `User_Setups/` dentro de la librería TFT_eSPI
2. Crear `User_Setups/Setup_DeskMate.h` con el contenido de `references/st7789-tft-espi-setup`
3. En `User_Setup_Select.h`, comentar TODAS las líneas y añadir:
   ```cpp
   #include <User_Setups/Setup_DeskMate.h>
   ```

**Parámetros que pueden variar según tu display específico:**
- `TFT_RGB_ORDER`: prueba `TFT_RGB` vs `TFT_BGR` si los colores salen invertidos
- `TFT_INVERSION_ON` / `TFT_INVERSION_OFF`: si la pantalla se ve en negativo
- `TFT_HEIGHT`: 240 para displays de 1.54", 320 para 2.0"
- Frecuencia SPI: empezar con 40MHz, bajar a 27MHz si hay artefactos

---

## 🏗️ Arquitectura del proyecto

### Estructura de pantallas (navegables con encoder)

```
Pantalla 1: INICIO (reloj + resumen)
  ┌─────────────────────┐
  │  12:45              │ ← Hora grande
  │  ⛅  Sens: 23°C     │ ← Clima + sensación
  │  🌡️ 25.3°C / 55%   │ ← DHT11 local
  │  💡 LED: Work mode  │ ← Estado iluminación
  │  ◀ ○ ○ ○ ▶          │ ← Indicador de página
  └─────────────────────┘

Pantalla 2: CLIMA (pronóstico)
Pantalla 3: LED CONTROL (modo/brillo/color)
Pantalla 4: ESTADOS (WiFi, uptime, sensores)
```

### Ciclo principal (loop)

```cpp
void loop() {
  handleEncoder();     // Leer encoder, cambiar pantalla/página
  updateClock();       // Actualizar hora cada segundo
  refreshWeather();    // Clima cada 10 minutos
  readSensors();       // DHT + LDR cada 5 segundos
  updateLEDs();        // Efectos WS2812B
  renderDisplay();     // Dibujar pantalla actual
  handleWebServer();   // Atender peticiones HTTP (web dashboard)
}
```

### Gestión de tiempo con FreeRTOS (opcional pero recomendado)

```cpp
// Tareas separadas para mantener UI fluida
xTaskCreate(displayTask, "Display", 4096, NULL, 1, NULL);
xTaskCreate(sensorTask,  "Sensors", 2048, NULL, 1, NULL);
xTaskCreate(ledTask,     "LEDs",    2048, NULL, 1, NULL);
xTaskCreate(wifiTask,    "WiFi",    4096, NULL, 1, NULL);
```

---

## 🌤️ Clima con OpenWeatherMap (Arduino)

1. Registrarse en [openweathermap.org](https://openweathermap.org/api) — plan gratis: 60 llamadas/minuto
2. Obtener API Key
3. Endpoint:
   ```
   http://api.openweathermap.org/data/2.5/weather?q=ciudad,pais&units=metric&appid=API_KEY
   ```
4. Almacenar API Key y ciudad en un archivo `config.h` (NO subir a GitHub público):
   ```cpp
   #ifndef CONFIG_H
   #define CONFIG_H
   const char* WIFI_SSID = "tu_red";
   const char* WIFI_PASS = "tu_clave";
   const char* OWM_API_KEY = "tu_api_key";
   const char* CITY = "Ciudad de México, MX";
   #endif
   ```

---

## 💡 Control de LEDs WS2812B

### Modos predefinidos

| Modo | Descripción |
|---|---|
| **Work** | Blanco frío (~4000K), brillo medio |
| **Focus** | Blanco cálido, brillo bajo |
| **Ambient** | Colores suaves en degradado lento |
| **Night** | Rojo tenue (no afecta visión nocturna) |
| **Rainbow** | Efecto arcoíris rotativo 🌈 |
| **Off** | Apagado |

### Configuración típica FastLED

```cpp
#include <FastLED.h>
#define LED_PIN     5
#define NUM_LEDS    30
#define BRIGHTNESS  128
CRGB leds[NUM_LEDS];

void setupLEDs() {
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
}
```

---

## 🌐 Web Dashboard (control desde el celular)

El ESP32 puede servir una página web responsive para control remoto:

```
http://[IP-del-ESP32]/
```

Funciones del dashboard:
- Cambiar modo de LEDs
- Brillo de pantalla y LEDs
- Ver temperatura/humedad en tiempo real
- Activar/desactivar sensores

Usar **WebServer** de ESP32 o **AsyncWebServer** para mejor rendimiento.

---

## 🚨 Pitfalls (Arduino / TFT_eSPI)

### 1. ST7789 y ESP32-C3 — Los pines SPI por defecto NO coinciden
- El ESP32-C3 tiene SPI por defecto en GPIO 4 (SCK), 5 (MISO), 6 (MOSI), 7 (SS)
- Pero el proyecto de referencia (AndroidCrypto) usa GPIO 6 como MOSI y GPIO 7 como SCLK exitosamente gracias a la GPIO Matrix
- Verifica siempre con tu setup específico

### 2. La pantalla muestra colores invertidos o negativo
Probar combinaciones de:
```cpp
#define TFT_RGB_ORDER TFT_RGB   // vs TFT_BGR
#define TFT_INVERSION_ON         // vs TFT_INVERSION_OFF
```

### 3. No se conecta WiFi
- El ESP32-C3 solo soporta 2.4 GHz (no 5 GHz)
- Puede tener problemas con redes empresariales (portales cautivos, WPA2-Enterprise)
- En redes domésticas, verificar que el router no esté en solo-5GHz

### 4. El encoder no responde bien
- Usar pull-ups internos o externos de 10kΩ
- La librería RotaryEncoder puede necesitar `LATCHMODE` en ESP32-C3 por los rebotes
- Añadir capacitor de 100nF entre CLK/GND y DT/GND para eliminar rebotes

### 5. Artefactos en la pantalla SPI
- Reducir `SPI_FREQUENCY` de 40MHz a 27MHz o 20MHz
- Alargar cables SPI O usar cables más cortos
- Añadir capacitor de 10µF entre VCC y GND cerca del display

### 6. No sube el código
- El ESP32-C3 Super Mini necesita modo bootloader: mantener BOOT, presionar RST, soltar BOOT
- Usar cable USB-C que soporte datos (no solo carga)
- En Arduino IDE seleccionar placa **"ESP32C3 Dev Module"**

### 7. Errores de compilación con TFT_eSPI
- Asegurarse de que solo UN archivo de setup está activo en `User_Setup_Select.h`
- Si usas PlatformIO, el archivo de setup puede ir en `lib/TFT_eSPI/User_Setups/` o vía flag de compilación
- Verificar que `TFT_WIDTH` y `TFT_HEIGHT` coinciden con tu display (240×240 para 1.54")

---

## ✅ Verificación

1. **Blink test** — LED onboard (GPIO 8) parpadea
2. **Display test** — Pantalla muestra colores sólidos (rojo, verde, azul)
3. **WiFi test** — Conexión exitosa, IP asignada
4. **NTP test** — Hora correcta sincronizada
5. **DHT test** — Lectura de temperatura y humedad en serial
6. **LED test** — Tira WS2812B enciende con el patrón esperado
7. **Web test** — Navegador carga el dashboard del ESP32
8. **Integration** — Todas las funciones operan juntas sin lag

---

## 🔧 Toolchain setup

### PlatformIO (recomendado para Arduino)
```ini
[env:esp32-c3-devkitc-02]
platform = espressif32
board = esp32-c3-devkitc-02
framework = arduino
lib_deps =
  bodmer/TFT_eSPI
  adafruit/DHT sensor library
  adafruit/Adafruit NeoPixel
  makuna/RotaryEncoder
  arduino-libraries/NTPClient
  bblanchon/ArduinoJson
```

### Arduino IDE
1. Añadir URL de placas ESP32: `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
2. Board: **ESP32C3 Dev Module**
3. Puerto USB-C (el board usa USB Serial/JTAG integrado)
4. Upload Speed: 921600

---

## 📟 ESP-IDF Native Approach (Alternative to Arduino)

Para proyectos que requieren más control, menor binario, o APIs nativas de Espressif. Usa **esp_lcd** en lugar de TFT_eSPI.

### ⚡ Diferencia clave

| Aspecto | Arduino + TFT_eSPI | ESP-IDF + esp_lcd |
|---------|-------------------|-------------------|
| Setup de pines | Archivo User_Setup.h personalizado | En código, via GPIO matrix |
| Dependencias | Librerías externas (TFT_eSPI, DHT, etc.) | Componentes de ESP-IDF |
| Tamaño binario | ~700KB+ | ~500KB+ (~1MB con HTTP + cJSON) |
| Control | Alto nivel | Bajo nivel (FreeRTOS nativo) |
| Curva aprendizaje | Baja | Media |

> Con HTTP client + cJSON + LCD, el binario supera fácilmente 1MB (de ~1MB disponibles en partición app). Monitorear con la advertencia "smallest app partition is nearly full" al hacer build.

### 🖥️ Driver del Display (ST7789 via esp_lcd)

```c
#include "driver/spi_master.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_st7789.h"

static esp_lcd_panel_handle_t panel_handle = NULL;

static void lcd_init(void) {
    // 1. Config SPI bus
    spi_bus_config_t buscfg = {
        .sclk_io_num     = 9,      // GPIO SCLK
        .mosi_io_num     = 6,      // GPIO MOSI
        .miso_io_num     = GPIO_NUM_NC,
        .quadwp_io_num   = GPIO_NUM_NC,
        .quadhd_io_num   = GPIO_NUM_NC,
        .max_transfer_sz = 240 * 240 * 2 + 8,
    };
    spi_bus_initialize(SPI2_HOST, &buscfg, SPI_DMA_CH_AUTO);

    // 2. Panel IO (SPI)
    esp_lcd_panel_io_handle_t io_handle = NULL;
    esp_lcd_panel_io_spi_config_t io_config = {
        .cs_gpio_num     = 21,     // GPIO CS
        .dc_gpio_num     = 10,     // GPIO DC
        .spi_mode        = 0,
        .pclk_hz         = 40 * 1000 * 1000,
        .trans_queue_depth = 10,
        .lcd_cmd_bits    = 8,
        .lcd_param_bits  = 8,
    };
    esp_lcd_new_panel_io_spi(SPI2_HOST, &io_config, &io_handle);

    // 3. Panel ST7789
    esp_lcd_panel_dev_config_t panel_config = {
        .reset_gpio_num  = 4,      // GPIO RST
        .rgb_ele_order   = LCD_RGB_ELEMENT_ORDER_BGR,
        .bits_per_pixel  = 16,
    };
    esp_lcd_new_panel_st7789(io_handle, &panel_config, &panel_handle);

    // 4. Init + encender
    esp_lcd_panel_reset(panel_handle);
    esp_lcd_panel_init(panel_handle);
    esp_lcd_panel_invert_color(panel_handle, true);  // ST7789 necesita inversión
    esp_lcd_panel_disp_on_off(panel_handle, true);
}
```

### 🔤 Fuente Bitmap 5×7 para Texto

El ESP-IDF no incluye fuentes por defecto en esp_lcd. La solución más ligera es una fuente bitmap 5×7 (95 caracteres ASCII imprimibles):

```c
// font_5x7.h — Cada char = 7 filas × 5 bits (MSB alineado a la izquierda)
#define FONT_CHAR_WIDTH  5
#define FONT_CHAR_HEIGHT 7

static const uint8_t font5x7[95][7] = {
    /* 32: Espacio */  {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00},
    /* 33: ! */        {0x04, 0x04, 0x04, 0x04, 0x00, 0x04, 0x00},
    /* 65: A */        {0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11},
    // ... completo en references/font-5x7-table.md
};

static void lcd_draw_char(int x, int y, char c, uint16_t color, uint8_t scale) {
    int idx = c - 32;
    const uint8_t *glyph = font5x7[idx];
    for (int row = 0; row < 7; row++) {
        for (int col = 0; col < 5; col++) {
            if (glyph[row] & (1 << (4 - col))) {
                lcd_draw_rect(x + col * scale, y + row * scale, scale, scale, color);
            }
        }
    }
}
```

**Ventajas:** sin dependencias externas, ~1KB flash, escalable (1x=5×7, 2x=10×14, 3x=15×21).  
Para centrar texto: `x = (LCD_WIDTH - (len * (5 * scale + spacing))) / 2`.

### 🌐 WiFi + SNTP (Reloj NTP)

Patrón con event groups para sincronizar el arranque:

```c
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_sntp.h"

static EventGroupHandle_t wifi_event_group;
#define WIFI_CONNECTED_BIT  BIT0
#define TIME_SYNCED_BIT     BIT2

static void wifi_event_handler(void *arg, esp_event_base_t base,
                               int32_t id, void *data) {
    if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        xEventGroupSetBits(wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

static void sntp_time_sync_cb(struct timeval *tv) {
    xEventGroupSetBits(wifi_event_group, TIME_SYNCED_BIT);
}

void init_ntp_clock(void) {
    // NVS (necesario para WiFi)
    nvs_flash_init();

    // WiFi
    esp_netif_init();
    esp_event_loop_create_default();
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);
    esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, wifi_event_handler, NULL);
    
    wifi_config_t wifi_config = {
        .sta = { .ssid = "TU_SSID", .password = "TU_CLAVE" },
    };
    esp_wifi_set_mode(WIFI_MODE_STA);
    esp_wifi_set_config(WIFI_IF_STA, &wifi_config);
    esp_wifi_start();
    esp_wifi_connect();

    // Esperar WiFi
    xEventGroupWaitBits(wifi_event_group, WIFI_CONNECTED_BIT, pdFALSE, pdFALSE, pdMS_TO_TICKS(30000));

    // SNTP
    setenv("TZ", "CST6CDT,M4.1.0,M10.5.0", 1);  // Zona horaria
    tzset();
    esp_sntp_setoperatingmode(SNTP_OPMODE_POLL);
    esp_sntp_setservername(0, "pool.ntp.org");
    sntp_set_time_sync_notification_cb(sntp_time_sync_cb);
    esp_sntp_init();

    // Esperar sync
    xEventGroupWaitBits(wifi_event_group, TIME_SYNCED_BIT, pdFALSE, pdFALSE, pdMS_TO_TICKS(15000));
}
```

### 🌤️ Clima OpenWeatherMap (HTTP + cJSON)

Fetch del clima usando `esp_http_client` + `cJSON` nativos de ESP-IDF. **Requiere WiFi conectado.**

#### Componentes en CMakeLists.txt

```cmake
idf_component_register(SRCS "main.c"
    INCLUDE_DIRS "." "include"
    REQUIRES esp_lcd esp_driver_spi driver
             esp_event esp_netif esp_wifi nvs_flash
             lwip esp_http_client json)
```

⚠️ `esp_http_client` y `json` son componentes nativos — no requieren instalación externa.

#### Estructura de datos

```c
typedef struct {
    float temp;
    float feels_like;
    char description[64];
    bool valid;
} weather_data_t;

static weather_data_t weather_data = {0};
```

#### HTTP Client — ⚠️ Patrón correcto

**NO usar `esp_http_client_perform()`** — consume el response body internamente. `esp_http_client_read()` devuelve 0 bytes aunque el status sea 200 con content_length=522. Usar el patrón **manual**:

```c
#include "esp_http_client.h"
#include "cJSON.h"

static weather_data_t weather_fetch(void) {
    weather_data_t wd = {0};
    char url[256];

    snprintf(url, sizeof(url),
             "http://api.openweathermap.org/data/2.5/weather"
             "?id=%s&appid=%s&units=%s&lang=%s",
             CITY_ID, API_KEY, "metric", "es");

    esp_http_client_config_t config = {
        .url = url,
        .timeout_ms = 15000,
    };
    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (!client) return wd;

    /* PASO 1: Abrir conexión (0 = GET, sin body) */
    if (esp_http_client_open(client, 0) != ESP_OK) {
        esp_http_client_cleanup(client);
        return wd;
    }

    /* PASO 2: Leer headers (devuelve content_length) */
    int content_length = esp_http_client_fetch_headers(client);
    int http_status = esp_http_client_get_status_code(client);

    if (http_status != 200 || content_length <= 0) {
        esp_http_client_cleanup(client);
        return wd;
    }

    /* PASO 3: Leer body — SIEMPRE heap allocation */
    int buf_size = content_length + 1;
    if (buf_size > 4096) buf_size = 4096;
    char *buffer = malloc(buf_size);
    if (!buffer) { esp_http_client_cleanup(client); return wd; }

    int total_read = 0, read = 0;
    do {
        read = esp_http_client_read(client, buffer + total_read,
                                     buf_size - 1 - total_read);
        if (read > 0) total_read += read;
    } while (read > 0 && total_read < buf_size - 1);
    buffer[total_read] = '\0';

    /* PASO 4: Parsear JSON con cJSON */
    cJSON *root = cJSON_Parse(buffer);
    if (root) {
        cJSON *main_obj = cJSON_GetObjectItem(root, "main");
        cJSON *temp_item = cJSON_GetObjectItem(main_obj, "temp");
        cJSON *feels_item = cJSON_GetObjectItem(main_obj, "feels_like");
        if (cJSON_IsNumber(temp_item)) wd.temp = temp_item->valuedouble;
        if (cJSON_IsNumber(feels_item)) wd.feels_like = feels_item->valuedouble;

        cJSON *weather_arr = cJSON_GetObjectItem(root, "weather");
        if (cJSON_IsArray(weather_arr) && cJSON_GetArraySize(weather_arr) > 0) {
            cJSON *w = cJSON_GetArrayItem(weather_arr, 0);
            cJSON *desc = cJSON_GetObjectItem(w, "description");
            if (cJSON_IsString(desc))
                strncpy(wd.description, desc->valuestring, sizeof(wd.description) - 1);
        }
        cJSON_Delete(root);
    }

    free(buffer);
    esp_http_client_cleanup(client);
    wd.valid = true;
    return wd;
}
```

#### Integración en el main loop

```c
time_t last_weather_fetch = time(NULL);
#define WEATHER_INTERVAL 600  // 10 minutos

while (1) {
    display_clock();  // muestra clima desde weather_data global

    time_t now = time(NULL);
    if (time_synced && (now - last_weather_fetch >= WEATHER_INTERVAL)) {
        weather_data = weather_fetch();
        last_weather_fetch = now;
    }
    vTaskDelay(pdMS_TO_TICKS(1000));
}
```

#### Enlaces API OpenWeatherMap

| Parámetro | Ejemplo | Nota |
|---|---|---|
| `id` | `3459712` | City ID (recomendado sobre city name — evita problemas de encoding) |
| `units` | `metric` | `metric` = Celsius, `imperial` = Fahrenheit |
| `lang` | `es` | Descripciones en español |
| Endpoint | `http://api.openweathermap.org/data/2.5/weather` | Usar HTTP (no HTTPS) para evitar TLS en ESP32-C3 |

---

## 🚨 Pitfalls del enfoque ESP-IDF

- **esp_event.h no encontrado** — falta `esp_event` en REQUIRES de CMakeLists.txt. Añadirlo explícitamente.
- **No hay fuentes integradas** — necesitas fuente bitmap propia o LVGL.
- **SNTP bloqueante** — el patrón con xEventGroupWaitBits bloquea app_main hasta sincronizar. Alternativa: tarea separada.
- **Puerto serie ocupado** — `idf.py monitor` deja el puerto bloqueado. Matar el proceso anterior con `fuser -k /dev/ttyACM0` antes de flashear.
- **GPIO 9 como SCLK** — funciona via GPIO Matrix pero algunos pinouts lo listan como BOOT button. El ESP32-C3 lo reasigna sin problema.
- **Invertir color** — la mayoría de los ST7789 necesitan `esp_lcd_panel_invert_color(panel, true)` o los colores salen negativos.
- **⚠️ Stack overflow con HTTP + cJSON** — El task `main` por defecto tiene 3584 bytes de stack, insuficiente para `esp_http_client` + `cJSON` + buffer. Aumentar en sdkconfig:
  ```
  CONFIG_ESP_MAIN_TASK_STACK_SIZE=8192
  ```
  Y usar **heap allocation** (`malloc`) para el buffer HTTP, NUNCA stack (`char buf[2048]`).
- **⚠️ `esp_http_client_perform()` NO sirve para leer body** — consume la respuesta internamente. Usar SIEMPRE: `esp_http_client_open()` + `esp_http_client_fetch_headers()` + `esp_http_client_read()`.
- **⚠️ Heap en vez de stack para buffers grandes** — `char buf[2048]` local causa stack overflow aunque el task tenga 8KB. Siempre `malloc` + `free`.
- **Timing del primer fetch** — esperar ~3s después del sync SNTP antes del primer fetch HTTP. La pila TCP/IP necesita estabilizarse.
- **Heap limitado** — ESP32-C3 tiene ~133KB heap. `esp_http_client` + `cJSON` + buffer consumen ~10-15KB durante el fetch. Liberar con `cJSON_Delete()` y `free()`.
- **Partición app llena** — con HTTP + cJSON + LCD, el binario supera 1MB (de 1MB disponibles en partición factory). Si el build advierte "smallest app partition is nearly full", considerar aumentar tamaño de partición o reducir componentes.

---

## 📚 Referencias
- `references/esp32-c3-super-mini-pinout.md` — Tabla detallada de pines
- `references/st7789-tft-espi-setup.md` — Archivo de configuración TFT_eSPI funcional
- `references/esp32-c3-super-mini-pinout-discrepancies.md` — Discrepancias de pinout entre fuentes (SPI, FSPI, GPIO Matrix)
- `references/deskmate-project.md` — Proyecto completo DeskMate con ESP-IDF nativo (código fuente, pines, fases, resultados de verificación)
- [AndroidCrypto/ESP32_C3_ST7789_Starter](https://github.com/AndroidCrypto/ESP32_C3_ST7789_Starter) — Repo base probado (Arduino)
- [Random Nerd Tutorials: ESP32-C3 Super Mini](https://randomnerdtutorials.com/getting-started-esp32-c3-super-mini/)
- [Last Minute Engineers: ESP32-C3 Super Mini Pinout](https://lastminuteengineers.com/esp32-c3-super-mini-pinout-reference/)
