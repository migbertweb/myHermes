# TFT_eSPI — Configuración para ESP32-C3 Super Mini + ST7789 240×240

Archivo de setup para la librería **TFT_eSPI** (Bodmer) adaptado del repo [AndroidCrypto/ESP32_C3_ST7789_Starter](https://github.com/AndroidCrypto/ESP32_C3_ST7789_Starter).

## Instalación

1. Localiza la carpeta `User_Setups/` dentro de la librería TFT_eSPI:
   - **Arduino IDE:** `~/Arduino/libraries/TFT_eSPI/User_Setups/`
   - **PlatformIO:** `~/.platformio/packages/framework-arduinoespressif32/libraries/TFT_eSPI/User_Setups/`
   - O copia TFT_eSPI a `lib/` en tu proyecto y crea `lib/TFT_eSPI/User_Setups/`

2. Crea el archivo `User_Setups/Setup_DeskMate.h` con el contenido de abajo

3. Edita `User_Setup_Select.h` en la raíz de TFT_eSPI:
   - **Comenta TODAS** las líneas existentes (`// #include <User_Setups/...>`)
   - **Añade al final:**
     ```cpp
     #include <User_Setups/Setup_DeskMate.h>
     ```

---

## Archivo: Setup_DeskMate.h

```cpp
// Setup para: ESP32-C3 Super Mini + ST7789 240x240 SPI
#define USER_SETUP_ID 703

// ── Driver ──────────────────────────────────────────
#define ST7789_DRIVER

// ── Resolución ──────────────────────────────────────
#define TFT_WIDTH  240
#define TFT_HEIGHT 240   // ← Cambiar a 320 si es display de 2.0"

// ── Orden de color e inversión ──────────────────────
// Si los colores se ven invertidos (rojo↔azul), cambiar TFT_BGR ↔ TFT_RGB
#define TFT_RGB_ORDER TFT_BGR
// Si la pantalla se ve en negativo, alternar ON ↔ OFF
#define TFT_INVERSION_ON
//#define TFT_INVERSION_OFF

#define TFT_BACKLIGHT_ON 1

// ── Pines (ESP32-C3 Super Mini) ─────────────────────
#define TFT_MOSI 6   // SDA del display
#define TFT_SCLK 7   // SCL del display
#define TFT_CS   21  // CS
#define TFT_DC   10  // DC
#define TFT_RST  9   // RST (conectado a EN del ESP32)
                     // Si RST está conectado a EN, usar -1

// MISO no se usa (display solo escritura), pero debe definirse
#define TFT_MISO 20

// ── Fuentes ─────────────────────────────────────────
#define LOAD_GLCD   // Font 1. 8px — ~1820 bytes flash
#define LOAD_FONT2  // Font 2. 16px — ~3534 bytes
#define LOAD_FONT4  // Font 4. 26px — ~5848 bytes
#define LOAD_FONT6  // Font 6. 48px — ~2666 bytes (nums + :)
#define LOAD_FONT7  // Font 7. 48px 7-segment — ~2438 bytes
#define LOAD_FONT8  // Font 8. 75px — ~3256 bytes

#define LOAD_GFXFF  // FreeFonts (48 fuentes Adafruit_GFX)
#define SMOOTH_FONT // Anti-aliasing para fuentes FreeFont

// ── Velocidad SPI ──────────────────────────────────
#define SPI_FREQUENCY  40000000  // 40MHz
// Bajar a 27000000 (27MHz) si hay artefactos en la imagen
```

---

## Parámetros de ajuste fino

Si el display no se ve correctamente, prueba estas variaciones (en orden):

### 1. Orden de color
```cpp
#define TFT_RGB_ORDER TFT_RGB    // Intenta este si BGR da colores cambiados
#define TFT_RGB_ORDER TFT_BGR    // Default para muchos displays chinos
```

### 2. Inversión
```cpp
#define TFT_INVERSION_ON   // Si la pantalla se ve como negativo
#define TFT_INVERSION_OFF  // Si los colores se ven normales
```

### 3. Frecuencia SPI (si hay artefactos visuales)
```cpp
#define SPI_FREQUENCY  27000000  // Bajar si falla a 40MHz
#define SPI_FREQUENCY  20000000  // Muy seguro
#define SPI_FREQUENCY  40000000  // Máximo recomendado para ST7789
```

### 4. Pin RST
```cpp
#define TFT_RST  -1   // Si RST del display conectado a EN del ESP32
#define TFT_RST   9   // Si RST va a GPIO 9
```

### 5. Backlight
Si el BL del display está conectado a un pin PWM (para brillo ajustable):
```cpp
#define TFT_BL   GPIO_PIN   // Por ejemplo GPIO 3
// Y en setup():
pinMode(TFT_BL, OUTPUT);
analogWrite(TFT_BL, 128);  // 50% brillo
```

Si el BL está conectado directamente a 3.3V, no necesitas `TFT_BL`.

---

## Código mínimo de prueba

```cpp
#include <TFT_eSPI.h>
#include <SPI.h>

TFT_eSPI tft = TFT_eSPI();

void setup() {
  Serial.begin(115200);
  tft.init();
  tft.setRotation(0);
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawCentreString("Hola Mundo!", 120, 100, 4);
}

void loop() {}
```

Si el display no muestra nada:
1. Verificar conexiones (SDA→GPIO6, SCL→GPIO7, DC→GPIO10, CS→GPIO21)
2. Probar `#define TFT_RST -1`
3. Probar alternar `TFT_INVERSION_ON/OFF`
4. Bajar frecuencia SPI
5. Verificar que 3.3V y GND están bien conectados

---

## Nota sobre PlatformIO

Si usas PlatformIO, puedes evitar modificar la librería del sistema añadiendo flags de compilación en `platformio.ini`:

```ini
[env:esp32-c3-devkitc-02]
platform = espressif32
board = esp32-c3-devkitc-02
framework = arduino
board_build.f_cpu = 160000000L
board_build.flash_mode = dio

; Pasar defines directamente sin modificar la librería
build_flags =
  -DUSER_SETUP_ID=703
  -DST7789_DRIVER
  -DTFT_WIDTH=240
  -DTFT_HEIGHT=240
  -DTFT_RGB_ORDER=TFT_BGR
  -DTFT_INVERSION_ON
  -DTFT_BACKLIGHT_ON=1
  -DTFT_MOSI=6
  -DTFT_SCLK=7
  -DTFT_CS=21
  -DTFT_DC=10
  -DTFT_RST=9
  -DTFT_MISO=20
  -DLOAD_GLCD
  -DLOAD_FONT2
  -DLOAD_FONT4
  -DSMOOTH_FONT
  -DSPI_FREQUENCY=40000000

lib_deps =
  bodmer/TFT_eSPI
```

---

## Referencia
- [Repositorio base probado (AndroidCrypto)](https://github.com/AndroidCrypto/ESP32_C3_ST7789_Starter)
- [TFT_eSPI Docs (Bodmer)](https://github.com/Bodmer/TFT_eSPI)
