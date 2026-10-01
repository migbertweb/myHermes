---
name: desklamp
description: Lámpara origami DeskLamp — anillo WS2812B 8 LEDs + ESP32-C3 DeskMate. Efectos dinámicos integrados al proyecto DeskMate. USB hub 5V.
version: 1.6 (2026-07-19) — Brillo global, GRB verificado con botones RGB panel, led_cycle_mode eliminado
---

# DeskLamp — Lámpara origami con ESP32-C3 + WS2812

Lámpara de escritorio de baja intensidad: un cubo sonobe de papel origami con un anillo WS2812B de 8 LEDs en su interior, controlado por el ESP32-C3 Super Mini del proyecto DeskMate.

## Hardware

### ⚠️ GPIO: Usar GPIO 5, NO GPIO 8

En el **ESP32-C3 SuperMini** de este proyecto, **GPIO 8 está conectado al LED built-in** de la placa. Usarlo para el anillo WS2812B causa conflicto: el LED onboard parpadea y la señal RMT se corrompe. **Usar GPIO 5** — libre, sin conflictos. GPIO 7 también sirve como alternativa.

### Protip: Component Sourcing
- When ordering LED rings, verify the bit count (e.g., 7 vs 8 LEDs) and diameter.
- Shopee BR is a viable fast alternative to AliExpress for small electronics components in Brazil.

### BOM

| Componente | Especificación | Precio | Dónde |
|---|---|---|---|
| Anillo WS2812B 8 LEDs | 5V, RGB 5050, Ø33mm | ~$3 | Shopee BR ✅ ya comprado |
| Resistencia 220Ω–470Ω 1/4W | carbon film | ~$0.10 | qualquer loja |
| Capacitor 100µF 16V (opcional) | electrolítico | ~$0.20 | qualquer loja |
| Papel origami 15×15 | branco ou washi | ~$1 | papelaria local |
| Base madera 10×10×3cm | bricolaje / reciclada | — | — |

### Conexión (recomendada — una sola fuente)

```
USB Hub 5V ─── cable USB-C ─── ESP32 VBUS
                                      │
                    ┌──────────────────┤
                    │                  │
               Anillo VCC         Anillo GND
               (rojo)              (blanco)
                    │                  │
                    └── pin 5V ESP ────┘
                                           ┌─────┐
Anillo DIN (verde) ────────────────────────┤330Ω ├── GPIO 5
                                           └─────┘
```

**NO se necesita MOSFET** — los WS2812 tienen driver integrado y se alimentan del pin 5V del ESP32 (que viene directamente del USB).

| Cable | Conectar a |
|---|---|
| Anillo VCC (rojo) | Pin **5V** del ESP32 |
| Anillo GND (blanco/negro) | Pin **GND** del ESP32 |
| Anillo DIN (verde) → [220Ω–470Ω] → | **GPIO 5** del ESP32 |
| Anillo DO (Data Out) | ❌ **Sin conectar** — solo para encadenar más anillos |

⚠️ **Crítico:** la resistencia va **en serie con DIN**, no en paralelo. Sin ella, un transitorio puede quemar el GPIO. 330Ω funciona bien (el usuario no tenía 470Ω).

### ⚠️ Orden de color: probar GRB primero, RGB como fallback

El estándar WS2812B de WorldSemi usa orden **GRB**. Si los colores se ven mal (blanco sale rosado/verdoso, rojo↔verde intercambiados), probar el orden alternativo. En `encode_rgb()`:
```c
uint8_t buf[3] = { c.g, c.r, c.b };  // orden GRB (WorldSemi estándar) ← probar primero
// Si no: { c.r, c.g, c.b };         // orden RGB (algunos clones)
```
Verificar visualmente: modo LAMP (blanco cálido 3000K) debe verse ámbar/anaranjado, no rosado ni verdoso. El anillo de este proyecto (Shopee BR, 2026) resultó ser GRB genuino.

## Código

### led_control.h

```c
#pragma once
#include <stdint.h>
#include <stdbool.h>

#define LED_COUNT       8
#define LED_GPIO        5    /* NO usar GPIO 8 (LED built-in en SuperMini) */

typedef enum {
    LED_MODE_PULSE = 0,       // Respiración suave (modo inicial)
    LED_MODE_CHASE_RANDOM,    // Un LED viaja, color aleatorio
    LED_MODE_LAMP,            // Blanco cálido fijo
    LED_MODE_RAINBOW,         // Arcoíris rotativo
    LED_MODE_CANDLE,          // Llama de vela
    LED_MODE_AURORA,          // Azul/verde/violeta lento
    LED_MODE_SOLID,           // Color sólido configurable
    LED_MODE_OFF,             // Apagado
    LED_MODE_COUNT
} led_mode_t;

typedef struct {
    uint8_t r, g, b;
} rgb_t;

void led_init(void);
void led_set_mode(led_mode_t mode);
void led_cycle_mode(void);
void led_toggle_power(void);
void led_tick(void);
led_mode_t led_get_mode(void);
bool led_is_on(void);

/* Control remoto (Fase 3 — panel web DeskMate) */
void led_set_color(uint8_t r, uint8_t g, uint8_t b);
void led_get_color(uint8_t *r, uint8_t *g, uint8_t *b);
void led_set_brightness(uint8_t b);
uint8_t led_get_brightness(void);
```

### led_control.c

```c
/*
 * led_control.c — Control de anillo WS2812B (8 LEDs) vía RMT
 * Integración con DeskMate (ESP32-C3, ESP-IDF v5.5+)
 *
 * Conexión: GPIO 5 ──[330Ω]── DIN del anillo (NO usar GPIO 8, es LED built-in)
 * Alimentación: 5V directo del USB hub (LEDs + ESP32 mismo bus)
 * Color: orden GRB (WorldSemi estándar, verificado en este anillo)
 */

#include "led_control.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/rmt_tx.h"
#include "esp_log.h"
#include "esp_random.h"
#include <string.h>
#include <math.h>

static const char *TAG = "desklamp";

/* ───────── RMT encoder para WS2812 ───────── */

#define RMT_RESOLUTION_HZ  10000000  // 10 MHz → 100ns/tick

// Timing WS2812B @ 10 MHz (datasheet: T0H=0.4µs, T1H=0.8µs, RES>50µs)
#define T0H  4   // 0.4µs high
#define T0L  8   // 0.8µs low  → bit 0 = 1.2µs
#define T1H  8   // 0.8µs high
#define T1L  4   // 0.4µs low  → bit 1 = 1.2µs
#define T_RESET 600  // 60µs reset (>50µs requerido por datasheet)

/*
 * Convierte 3 bytes RGB → 24 símbolos RMT.
 * MSB first: bit 7 primero.
 */
static void encode_rgb(rgb_t c, rmt_symbol_word_t *sym)
{
    uint8_t buf[3] = { c.g, c.r, c.b };  // orden GRB (WorldSemi estándar)
    int idx = 0;
    for (int b = 0; b < 3; b++) {
        for (int i = 7; i >= 0; i--) {
            bool bit = (buf[b] >> i) & 1;
            sym[idx].level0    = 1;
            sym[idx].duration0 = bit ? T1H : T0H;
            sym[idx].level1    = 0;
            sym[idx].duration1 = bit ? T1L : T0L;
            idx++;
        }
    }
}

/* ───────── Estado global ───────── */

static rmt_channel_handle_t   tx_chan   = NULL;
static rmt_encoder_handle_t   copy_enc  = NULL;
static rgb_t                  leds[LED_COUNT];
static led_mode_t             cur_mode  = LED_MODE_PULSE;
static bool                   on        = true;
static uint32_t               tick      = 0;

// Lookup de seno 8-bit (sin math.h)
static const int8_t sin8[64] = {
    0,  12,  25,  37,  49,  60,  71,  81,
   90,  98, 106, 112, 117, 122, 125, 126,
  127, 126, 125, 122, 117, 112, 106,  98,
   90,  81,  71,  60,  49,  37,  25,  12,
    0, -12, -25, -37, -49, -60, -71, -81,
  -90, -98,-106,-112,-117,-122,-125,-126,
 -127,-126,-125,-122,-117,-112,-106, -98,
  -90, -81, -71, -60, -49, -37, -25, -12
};

static inline int sin8_lookup(int idx) {
    return sin8[idx & 63];
}

/* ───────── Enviar frame al anillo ───────── */

static void send_leds(void)
{
    rmt_symbol_word_t frame[LED_COUNT * 24 + 1];  // +1 reset
    for (int i = 0; i < LED_COUNT; i++)
        encode_rgb(leds[i], &frame[i * 24]);
    // Reset pulse
    frame[LED_COUNT * 24].level0    = 0;
    frame[LED_COUNT * 24].duration0 = T_RESET;
    frame[LED_COUNT * 24].level1    = 0;
    frame[LED_COUNT * 24].duration1 = 0;

    rmt_transmit_config_t tx_cfg = {
        .loop_count = 0,
        .flags = { .eot_level = 0 },
    };
    ESP_ERROR_CHECK(rmt_transmit(tx_chan, copy_enc, frame,
                                 sizeof(frame[0]) * (LED_COUNT * 24 + 1),
                                 &tx_cfg));
}

/* ───────── Efectos ───────── */

static void effect_lamp(void)
{
    // Blanco cálido 3000K: R=255, G=160, B=80 → 40% brillo suave
    rgb_t c = { .r = 102, .g = 64, .b = 32 };
    for (int i = 0; i < LED_COUNT; i++)
        leds[i] = c;
}

static void effect_rainbow(void)
{
    int rot = (tick >> 2) & 63;
    for (int i = 0; i < LED_COUNT; i++) {
        int hue = ((i * 64) / LED_COUNT + rot) & 63;
        int r = (sin8_lookup(hue + 21) + 128) >> 1;
        int g = (sin8_lookup(hue) + 128) >> 1;
        int b = (sin8_lookup(hue + 43) + 128) >> 1;
        leds[i].r = r;
        leds[i].g = g;
        leds[i].b = b;
    }
}

static void effect_pulse(void)
{
    int v = (sin8_lookup(tick / 3) + 128) >> 1;
    rgb_t c = { .r = v, .g = v * 3 / 5, .b = v * 2 / 7 };
    for (int i = 0; i < LED_COUNT; i++)
        leds[i] = c;
}

static void effect_candle(void)
{
    for (int i = 0; i < LED_COUNT; i++) {
        int noise = (tick * 7 + i * 13) & 31;
        int v = 80 + (noise < 15 ? noise * 3 : (31 - noise) * 2);
        if (v > 130) v = 130;
        leds[i].r = v;
        leds[i].g = v * 3 / 5;
        leds[i].b = v / 4;
    }
}

static void effect_aurora(void)
{
    int phase = (tick / 8) & 127;
    for (int i = 0; i < LED_COUNT; i++) {
        int p = (phase + i * 8) & 127;
        int r = (sin8_lookup(p * 2) + 128) / 6;
        int g = (sin8_lookup(p * 2 + 21) + 128) / 4;
        int b = (sin8_lookup(p * 2 + 43) + 128) / 3;
        leds[i].r = r;
        leds[i].g = g;
        leds[i].b = b;
    }
}

static void effect_off(void)
{
    rgb_t c = { 0 };
    for (int i = 0; i < LED_COUNT; i++)
        leds[i] = c;
}

static void effect_chase_random(void)
{
    /* Apagar todos, encender solo el LED actual con color aleatorio */
    rgb_t off = { 0 };
    for (int i = 0; i < LED_COUNT; i++) leds[i] = off;
    int pos = (tick / 1) % LED_COUNT;  /* 1s por LED (tick corre a 1Hz) */
    leds[pos].r = esp_random() & 0xFF;
    leds[pos].g = esp_random() & 0xFF;
    leds[pos].b = esp_random() & 0xFF;
}

/* ───────── API pública ───────── */

void led_init(void)
{
    rmt_tx_channel_config_t chan_cfg = {
        .clk_src         = RMT_CLK_SRC_DEFAULT,
        .gpio_num        = LED_GPIO,
        .mem_block_symbols = 64,
        .resolution_hz   = RMT_RESOLUTION_HZ,
        .trans_queue_depth = 4,
    };
    ESP_ERROR_CHECK(rmt_new_tx_channel(&chan_cfg, &tx_chan));

    rmt_copy_encoder_config_t enc_cfg = {};
    ESP_ERROR_CHECK(rmt_new_copy_encoder(&enc_cfg, &copy_enc));

    ESP_ERROR_CHECK(rmt_enable(tx_chan));

    led_set_mode(LED_MODE_LAMP);
    send_leds();

    ESP_LOGI(TAG, "init: GPIO %d, %d LEDs", LED_GPIO, LED_COUNT);
}

void led_set_mode(led_mode_t mode)
{
    if (mode >= LED_MODE_COUNT) return;
    cur_mode = mode;
    on = (mode != LED_MODE_OFF);
    tick = 0;
    ESP_LOGI(TAG, "modo: %d", mode);
}

void led_cycle_mode(void)
{
    led_mode_t next = (cur_mode + 1) % LED_MODE_COUNT;
    led_set_mode(next);
}

void led_toggle_power(void)
{
    if (on) {
        on = false;
        effect_off();
        send_leds();
    } else {
        on = true;
        tick = 0;
    }
}

void led_tick(void)
{
    tick++;
    if (!on) return;

    switch (cur_mode) {
        case LED_MODE_PULSE:        effect_pulse();        break;
        case LED_MODE_CHASE_RANDOM: effect_chase_random(); break;
        case LED_MODE_LAMP:         effect_lamp();         break;
        case LED_MODE_RAINBOW:      effect_rainbow();      break;
        case LED_MODE_CANDLE:       effect_candle();       break;
        case LED_MODE_AURORA:       effect_aurora();       break;
        case LED_MODE_OFF:          effect_off();          break;
        default:                    effect_pulse();        break;
    }

    send_leds();
}

led_mode_t led_get_mode(void) { return cur_mode; }
bool led_is_on(void)          { return on; }
```

### Integración en main.c del DeskMate

Buscar en `main.c` y agregar:

**1. Include al inicio:**
```c
#include "led_control.h"
```

**2. En app_main(), después de init display:**
```c
led_init();
```

**3. En el bucle principal, justo antes de vTaskDelay:**
```c
led_tick();
```

**4. En el bloque de auto-rotación de pantalla (cada 10s):**
```c
led_cycle_mode();  // cicla modo LED con cada cambio de pantalla
```
El DeskMate v1.1+ no tiene botón; `led_cycle_mode()` se llama en la auto-rotación. Si se reactiva un botón en el futuro, mover la llamada al handler.
```cmake
idf_component_register(SRCS "main.c" "led_control.c"
                       INCLUDE_DIRS "." "include"
                       REQUIRES ...)
```
El `REQUIRES driver` ya está presente en el proyecto — solo hace falta agregar `led_control.c` a SRCS.

## Efectos

| Modo | Visual | Frecuencia |
|---|---|---|
| `LAMP` | 🔆 Blanco 3000K fijo al 40% | — |
| `RAINBOW` | 🌈 Arcoíris rotando | 1 ciclo/5s |
| `PULSE` | 💗 Respira ámbar | 1 ciclo/3s |
| `CANDLE` | 🕯️ 8 velas independientes | variado |
| `AURORA` | ✨ Azul/verde/violeta | 1 ciclo/10s |
| `SOLID` | 🎨 Color sólido configurable (desde panel web) | — |
| `CHASE_RANDOM` | 🔴 Un LED viaja por el anillo, color aleatorio | 1s/posición |
| `OFF` | ⬛ Apagado | — |

`CHASE_RANDOM` es ideal para diagnosticar: enciende un solo LED a la vez, moviéndose por el anillo con colores aleatorios. Si un LED nunca enciende ni en este modo, es defecto físico (soldadura fría o LED quemado).

## Notas extras

### Armado físico

1. **Cubo sonobe**: 12 cuadrados de papel 15×15. Plegado modular sin pegamento. Queda hueco — ideal para meter el anillo dentro.
2. **Anillo**: Pegar con silicona caliente en el techo interior del cubo, LEDs apuntando hacia abajo.
3. **Cables**: 3 cables finos (~28AWG) bajan por una esquina discreta hasta la base. Usar cable de par trenzado o flat cable de extracción.
4. **Base madera**: Taladrar un hueco de ~35mm para el ESP32-C3. Pasacables para el USB-C. El botón GPIO 3 se monta al ras.
5. **Sin pegamento**: El cubo sonobe se sostiene por fricción. Si quieres fijarlo a la base, usa un punto de silicona caliente en la cara inferior.
6. **Oscurecer interior del cubo**: Si la luz se escapa por las uniones del papel, pegar un disco de cartulina blanca en el techo interior (detrás del anillo) para reflejar hacia abajo.

### ⚠️ Brillo global aplicado en `send_leds()` (v1.6)

El brillo se aplica como factor multiplicativo en `send_leds()`, antes de codificar el frame RMT:

```c
static void send_leds(void)
{
    /* Aplicar brillo global */
    rgb_t scaled[LED_COUNT];
    for (int i = 0; i < LED_COUNT; i++) {
        scaled[i].r = ((uint16_t)leds[i].r * brightness) >> 8;
        scaled[i].g = ((uint16_t)leds[i].g * brightness) >> 8;
        scaled[i].b = ((uint16_t)leds[i].b * brightness) >> 8;
    }
    rmt_symbol_word_t frame[LED_COUNT * 24 + 1];
    for (int i = 0; i < LED_COUNT; i++)
        encode_rgb(scaled[i], &frame[i * 24]);
    ...
}
```

`brightness` es `static uint8_t` global, rango 0-255. `led_set_brightness(b)` lo configura desde el panel web. El factor `>> 8` es equivalente a dividir entre 256, preservando la proporción de color.

### ✅ Orden GRB verificado (2026-07-19)

El anillo NeoPixel Ring 8× WS2812B RGB LED de Shopee BR usa orden **GRB** (WorldSemi estándar). Verificado con botones 🔴🟢🔵 del panel web: al enviar rojo puro (255,0,0) en modo SOLID, el LED se ve rojo. No requiere cambio a RGB.

### ⚠️ led_cycle_mode() eliminado de auto-rotación (v1.6+)

A partir de commit `63046ce`, `led_cycle_mode()` ya no se llama en la auto-rotación de pantalla. El modo LED ahora se controla **exclusivamente desde el panel web** vía WebSocket. Para reactivar el ciclo automático, agregar de nuevo `led_cycle_mode();` en `main.c` dentro del bloque `if (screen_timer >= SCREEN_AUTO_ROTATE_SEC)`.

### ⚠️ Timing RMT: T_RESET debe ser >50µs (CRÍTICO)

Timings correctos a 10MHz:
| Parámetro | Ticks | Tiempo | Datasheet |
|---|---|---|---|
| T0H | 4 | 0.4µs | 0.4µs ±150ns |
| T0L | 8 | 0.8µs | 0.85µs ±150ns |
| T1H | 8 | 0.8µs | 0.8µs ±150ns |
| T1L | 4 | 0.4µs | 0.45µs ±150ns |
| T_RESET | 600 | 60µs | >50µs |

### Seguridad eléctrica

- El anillo WS2812B 8 LEDs consume ~160mA a full blanco (8 × 20mA). Un hub USB de 5V 2A entrega 12× eso — sin riesgo.
- **Resistencia 220Ω–470Ω en DIN** — no es opcional. Protege el GPIO del ESP32 de transitorios. Cualquier valor en ese rango funciona; si no tienes 470Ω, 330Ω o 220Ω sirven igual. 1MΩ es demasiado alto (atenúa la señal). Sin resistencia puedes quemar el pin.
- **Condensador 100µF** en 5V/GND cerca del anillo: recomendable si ves parpadeos o el ESP32 se resetea al cambiar efectos. Los WS2812 tienen picos de corriente al cambiar de color.
- GND común: el ESP32, los LEDs y el USB deben compartir GND.

### Posibles expansiones

- Más LEDs: `LED_COUNT` se cambia fácil para anillos de 12, 16 o 24 LEDs
- WiFi: control remoto desde el navegador o Home Assistant
- Micrófono MAX4466 para modo "music reactive" con FFT
- Sensor de luz ambiental para brillo automático
- Más botones: uno para modo, otro para brillo
- Efectos nocturnos: el modo AURORA a baja intensidad ilumina sin despertar

### Convenciones

- TLS: no aplica (comunicación local entre módulos en el mismo firmware)
- Sin dependencias externas — todo ESP-IDF nativo
- Sin heap dinámico — todas las estructuras estáticas o en stack
- Sin math.h — lookup table de seno para evitar flash footprint

## Remote workflow (desde el servidor)

El proyecto DeskMate está en la laptop CachyOS. Para editar y flashear desde el servidor:

```bash
# Copiar led_control.c/h al proyecto
ssh cachy "cp /tmp/desklamp/led_control.h /home/migbert/proyectos/deskmate/main/"
ssh cachy "cp /tmp/desklamp/led_control.c /home/migbert/proyectos/deskmate/main/"

# Editar main.c para integrar
ssh cachy "vim /home/migbert/proyectos/deskmate/main/main.c"

# Build
ssh cachy "cd /home/migbert/proyectos/deskmate && . /home/migbert/.espressif/v5.5.3/esp-idf/export.sh && idf.py build"

# Flash
ssh cachy "cd /home/migbert/proyectos/deskmate && . /home/migbert/.espressif/v5.5.3/esp-idf/export.sh && fuser -k /dev/ttyACM0 2>/dev/null; idf.py -p /dev/ttyACM0 flash"

# Monitor
ssh cachy "cd /home/migbert/proyectos/deskmate && . /home/migbert/.espressif/v5.5.3/esp-idf/export.sh && idf.py -p /dev/ttyACM0 monitor"
```

O usar los scripts ya definidos en el skill `deskmate-dashboard` para build y flash remotos.

### Archivos temporales en servidor

Los archivos fuente viven también en el servidor en `/tmp/desklamp/` — se pueden editar desde la sesión de Hermes en el servidor y luego copiar a la laptop con los comandos SSH de arriba. No usar `rm -rf /tmp/desklamp/` hasta que el proyecto esté completo.
