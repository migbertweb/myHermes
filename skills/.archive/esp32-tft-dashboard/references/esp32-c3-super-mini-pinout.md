# ESP32-C3 Super Mini — Pinout de Referencia

Placa compacta basada en el chip RISC-V ESP32-C3. WiFi/BLE, 160MHz, 400KB SRAM, 4MB flash.
**Opera exclusivamente a 3.3V.** No conectar 5V a GPIOs.

---

## Diagrama físico

```
        ┌─────────────────────┐
  GND   │ ● ● ● ● ● ● ● ●   │ 3V3
  GPIO 0│ ● ● ● ● ● ● ● ●   │ 5V
  GPIO 1│ ● ● ● ● ● ● ● ●   │ RST
  GPIO 2│ ● ● ● ● ● ● ● ●   │ GPIO 9
  GPIO 3│ ● ● ● ● ● ● ● ●   │ GPIO 10
  GPIO 4│ ● ● ● ● ● ● ● ●   │ GPIO 20
  GPIO 5│ ● ● ● ● ● ● ● ●   │ GPIO 21
  GPIO 6│ ● ● ● ● ● ● ● ●   │ GPIO 7
        └─────────────────────┘
         USB-C (abajo)
```

**Nota:** el orden puede variar según el fabricante — verificar serigrafía.

---

## Tabla completa de pines

| GPIO | Función | ADC | Seguro? | Notas |
|---|---|---|---|---|
| **GPIO 0** | GPIO, PWM | ✅ ADC1_CH0 | ✅ Sí | Buen pin para LDR / sensor analógico |
| **GPIO 1** | GPIO, PWM | ✅ ADC1_CH1 | ✅ Sí | Buen pin para encoder DT |
| **GPIO 2** | GPIO, PWM | ✅ ADC1_CH2 | ❌ **NO** | **Strapping pin** — debe estar HIGH en boot para arranque normal |
| **GPIO 3** | GPIO, PWM | ✅ ADC1_CH3 | ✅ Sí | Buen pin para encoder CLK |
| **GPIO 4** | GPIO, PWM, SPI SCK | ✅ ADC1_CH4 | ✅ Sí | Buen pin para DHT11 / sensores digitales |
| **GPIO 5** | GPIO, PWM, SPI MISO | ✅ ADC1_CH5 | ✅ Sí | Buen pin para WS2812B / NeoPixel |
| **GPIO 6** | GPIO, PWM, SPI MOSI | ❌ | ✅ Sí | **MOSI del display** — no se puede usar ADC aquí |
| **GPIO 7** | GPIO, PWM, SPI SS | ❌ | ✅ Sí | **SCLK del display** |
| **GPIO 8** | GPIO, I2C SDA, Onboard LED | ❌ | ⚠️ **Evitar** | **Strapping pin** + LED activo en LOW — interfiere con boot e I2C |
| **GPIO 9** | GPIO, I2C SCL, BOOT button | ❌ | ⚠️ **Evitar** | **Strapping pin** — conectado al botón BOOT. Solo apto como RST del display |
| **GPIO 10** | GPIO, PWM | ❌ | ✅ Sí | Buen pin para DC del display |
| **GPIO 20** | GPIO, PWM, UART RX | ❌ | ✅ Sí | Usable después de subir código. Bueno como CS/MISO del display |
| **GPIO 21** | GPIO, PWM, UART TX | ❌ | ✅ Sí | Usable después de subir código. Bueno como CS del display |

---

## Resumen de pines seguros (10 disponibles)

**Prioridad alta (usar primero):**
`GPIO 0, 1, 3, 4, 5, 6, 7, 10`

**Usables con precaución (después de subir código):**
`GPIO 20, 21`

**Evitar completamente:**
`GPIO 2, 8, 9`

---

## Funciones especiales

### ADC (entrada analógica)
Solo estos pines soportan lectura analógica:
| GPIO | Canal ADC | Uso típico |
|---|---|---|
| GPIO 0 | ADC1_CH0 | LDR, potenciómetro |
| GPIO 1 | ADC1_CH1 | Sensor analógico |
| GPIO 2 | ADC1_CH2 | ❌ Evitar |
| GPIO 3 | ADC1_CH3 | Sensor analógico |
| GPIO 4 | ADC1_CH4 | Sensor analógico |
| GPIO 5 | ADC1_CH5 | Sensor analógico |

Resolución: 12 bits (0-4095). Rango: 0-3.3V.

### SPI
| Señal | Default | Uso en proyecto |
|---|---|---|
| MOSI | GPIO 6 | SDA del display ST7789 |
| SCK | GPIO 4 | Se reasigna a GPIO 7 vía GPIO Matrix |
| MISO | GPIO 5 | No usado (display es write-only) |
| SS | GPIO 7 | No usado |

### I2C
| Señal | Default | Nota |
|---|---|---|
| SDA | GPIO 8 | Evitar — conflicto con strapping + LED |
| SCL | GPIO 9 | Evitar — conflicto con botón BOOT |

Si necesitas I2C (para BME280, OLED, etc.), reasignar via GPIO Matrix a GPIOs seguros:
```cpp
Wire.begin(4, 3); // SDA=GPIO4, SCL=GPIO3
```

### UART
| Señal | Default | Nota |
|---|---|---|
| RX | GPIO 20 | No usar durante carga de código |
| TX | GPIO 21 | No usar durante carga de código |

El ESP32-C3 Super Mini usa USB Serial/JTAG integrado para programación (no UART0).
Por lo tanto GPIO 20 y 21 son libres para uso general DESPUÉS de subir el firmware, pero evita `Serial.begin()` sin deshabilitar el USB CDC si ocupas esos pines.

---

## Alimentación

| Pin | Voltaje | Corriente máxima |
|---|---|---|
| **5V** | 4.5-5.5V (USB o entrada externa) | ~500mA (limitado por regulador) |
| **3.3V** | 3.3V salida/entrada | ~300mA (regulador integrado) |
| **GND** | Referencia | — |

**Importante:** No alimentar por USB y 5V externo simultáneamente.
**Tira WS2812B** puede consumir 60mA por LED (blanco full) — alimentar desde 5V externo, NO desde el pin 3.3V del ESP32.

---

## Strapping Pins — Detalle

Estos pines definen el modo de boot del ESP32-C3. Su estado al encender determina cómo arranca:

| GPIO | Señal | Valor | Comportamiento |
|---|---|---|---|
| GPIO 2 | GPIO2_STRAP | HIGH (1) | Boot normal |
|  |  | LOW (0) | **Falla boot** — no arranca |
| GPIO 8 | GPIO8_STRAP | HIGH (1) | Boot normal |
|  |  | LOW (0) | Boot desde descarga (peligroso si flota) |
| GPIO 9 | GPIO9_STRAP | HIGH (1) → toggles | Boot normal al soltar BOOT |
|  |  | LOW (0) | Modo bootloader/descarga |

**Regla de oro:** Si usas estos pines, asegúrate de que estén HIGH al boot (con pull-up externo de 10kΩ a 3.3V). Mejor aún: no los uses.

---

## Referencias
- [Last Minute Engineers: ESP32-C3 Super Mini Pinout](https://lastminuteengineers.com/esp32-c3-super-mini-pinout-reference/)
- [Random Nerd Tutorials: Getting Started](https://randomnerdtutorials.com/getting-started-esp32-c3-super-mini/)
- [Mischianti: ESP32-C3 Super Mini specs](https://mischianti.org/esp32-c3-super-mini-high-resolution-pinout-datasheet-and-specs/)
- [AndroidCrypto: ESP32_C3_ST7789_Starter](https://github.com/AndroidCrypto/ESP32_C3_ST7789_Starter)
