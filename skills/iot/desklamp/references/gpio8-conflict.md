# GPIO 8 Conflict on ESP32-C3 SuperMini

## Problem

On the most common ESP32-C3 SuperMini variant, **GPIO 8 is physically connected to the onboard LED** ("Built-In LED"). Using GPIO 8 for WS2812B LED ring (DeskLamp) causes:
- Signal contention with the onboard LED driver
- RMT signal degradation
- Flickering or no response from the WS2812B ring

## Verified Pinout (2026-07-19)

From the user's ESP32-C3 SuperMini board:

**Left side (top to bottom):**
- GPIO 5 (ADC1_5)
- GPIO 6 (MISO)
- GPIO 7 (CS)
- GPIO 8 (SDA / Built-In LED) ← CONFLICT
- GPIO 9 (SCL)
- GPIO 10
- GPIO 20 (UART_RX)
- GPIO 21 (UART_TX)

**Right side (top to bottom):**
- 5V, GND, 3.3V (power)
- GPIO 4 (ADC1_4 / SCK)
- GPIO 3 (ADC1_3)
- GPIO 2 (ADC1_2)
- GPIO 1 (ADC1_1)
- GPIO 0 (ADC1_0)

## Alternative GPIOs for WS2812B

Free pins (not used by DeskMate ST7789 display or button):
- **GPIO 5** — recommended first choice
- **GPIO 7** — recommended second choice
- **GPIO 10** — available
- **GPIO 20** — available

Change `#define LED_GPIO 8` → `#define LED_GPIO 5` in `led_control.h`.
