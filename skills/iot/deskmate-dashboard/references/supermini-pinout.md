# ESP32-C3 SuperMini — Pinout de la placa de Migbert

Placa usada en DeskMate. Foto de referencia: `5V-1024x576.jpg`.

## Lado Izquierdo (USB-C arriba)
| Pin | GPIO | Función alternativa |
|-----|------|---------------------|
| 1 | GPIO5 | ADC1_5 |
| 2 | GPIO6 | MISO (SPI) |
| 3 | GPIO7 | CS (SPI) |
| 4 | GPIO8 | SDA (I2C) / **Built-In LED** ⚠️ |
| 5 | GPIO9 | SCL (I2C) |
| 6 | GPIO10 | — |
| 7 | GPIO20 | UART_RX |
| 8 | GPIO21 | UART_TX |

## Lado Derecho (USB-C arriba)
| Pin | GPIO | Función alternativa |
|-----|------|---------------------|
| 1 | 5V | — (power) |
| 2 | GND | — (power) |
| 3 | 3.3V | — (power) |
| 4 | GPIO4 | ADC1_4 / SCK (SPI) |
| 5 | GPIO3 | ADC1_3 |
| 6 | GPIO2 | ADC1_2 (strapping) |
| 7 | GPIO1 | ADC1_1 |
| 8 | GPIO0 | ADC1_0 |

## GPIOs usados por DeskMate
| GPIO | Uso |
|------|-----|
| 3 | ❌ libre (antes botón, eliminado) |
| 4 | Display RST |
| 5 | **Anillo WS2812B DI** (NUEVO) |
| 6 | Display MOSI/SDA |
| 7 | ❌ libre |
| 8 | ⚠️ LED built-in (NO usar) |
| 9 | Display SCLK |
| 10 | Display DC |
| 20 | ❌ libre |
| 21 | Display CS |

## Notas
- GPIO 2 y 8 son strapping pins — evitar si es posible
- GPIO 8 tiene LED onboard, usar GPIO 5 o 7 para periféricos
- Resistencia recomendada para WS2812B DIN: 220Ω–470Ω (330Ω usado)
