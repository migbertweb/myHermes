# ESP32-C3 Super Mini — Discrepancias de Pinout

## Advertencia: múltiples fuentes, múltiples versiones

El ESP32-C3 Super Mini tiene al menos **2 variantes de placa** (estándar azul/negra y "Plus" roja), múltiples fabricantes (AZ-Delivery, Seeed, etc.), y **3 diagramas de pinout comúnmente citados con discrepancias en SPI**. Esto causa confusión frecuente.

## Comparativa de fuentes

### SPI2 — Pines por defecto (según cada fuente)

| Función SPI | GitHub (sidharth) | Mischianti | LastMinuteEngineers (abril 2026) |
|:-----------:|:-----------------:|:----------:|:-------------------------------:|
| **MOSI**    | GPIO6             | GPIO6      | **GPIO7**                       |
| **MISO**    | GPIO5             | GPIO5      | GPIO5                           |
| **SCK**     | GPIO4             | GPIO4      | **GPIO6**                       |
| **SS/CS**   | GPIO7             | GPIO7      | **GPIO10**                      |

### Origen de la discrepancia

- **GitHub/Mischianti** muestran las funciones **FSPI** (Fast SPI del hardware, usado para flash interna) en lugar de SPI2. FSPI tiene asignaciones fijas por IO MUX.
- **LastMinuteEngineers** muestra **SPI2** (el bus SPI programable para periféricos), que pasa por la GPIO Matrix.

### Conclusión técnica

**Ambos mapeos funcionan** porque el ESP32-C3 tiene una **GPIO Matrix** que permite reasignar cualquier señal SPI2 a cualquier GPIO mediante software. La diferencia práctica es:
- Usar los pines nativos (IO MUX) → ruta directa, menor latencia (irrelevante para display a 20-40 MHz)
- Usar otros pines → ruta por GPIO Matrix, micro-latencia adicional (inapreciable)

## Pines físicos de la placa (16 pines, 2 filas de 8)

### Lado izquierdo (USB hacia arriba, de arriba a abajo)
| Pin | GPIO | Función (AZ-Delivery) | Notas |
|:---:|:----:|:----------------------|:------|
| 1   | 5    | MISO/FSPIWP | JTAG MTDI |
| 2   | 6    | **MOSI/SDA** | JTAG MTCK |
| 3   | 7    | SS/FSPID | JTAG MTDO |
| 4   | 8    | **SCL** (I2C) / LED | Strapping — evitar uso general |
| 5   | 9    | **SDA** (I2C) / BOOT | Strapping — funciona como SCLK vía GPIO Matrix |
| 6   | 10   | FSPICS0 | JTAG |
| 7   | 20   | RXD0 | UART0 RX |
| 8   | 21   | TXD0 | UART0 TX |

### Lado derecho (USB hacia arriba, de arriba a abajo)
| Pin | GPIO | Función (AZ-Delivery) | Notas |
|:---:|:----:|:----------------------|:------|
| 1   | 5V   | Alimentación | Entrada desde USB o externa |
| 2   | GND  | Tierra | |
| 3   | 3.3V | VCC regulado | Salida 3.3V |
| 4   | 4    | **RST** | JTAG MTMS |
| 5   | 3    | GPIO/PWM | ADC1_CH3 |
| 6   | 2    | FSPIQ/MISO | Strapping — evitar |
| 7   | 1    | GPIO/PWM | ADC1_CH1 |
| 8   | 0    | GPIO/PWM | ADC1_CH0 |

### Pines a evitar para uso general
| GPIO | Razón |
|:----:|:------|
| **2** | Strapping pin — debe estar HIGH en boot. Si se pone LOW, el boot falla. |
| **8** | Conectado al LED onboard (activo bajo). También es pin strapping. |

## Board variants

- **Estándar** (negra/azul): la más común
- **Plus** (roja): 14 pines (7+7), pinout similar pero con menos pines
- Algunos fabricantes etiquetan diferente. **Siempre verificar el diagrama del fabricante específico.**

## Referencias

- https://detailspin.com/esp32/esp32-c3-super-mini-pinout.html (AZ-Delivery)
- https://lastminuteengineers.com/esp32-c3-super-mini-pinout-reference/
- https://mischianti.org/esp32-c3-super-mini-high-resolution-pinout-datasheet-and-specs/
- https://github.com/sidharthmohannair/Tutorial-ESP32-C3-Super-Mini
- https://www.espboards.dev/esp32/esp32-c3-super-mini/
- https://docs.espressif.com/projects/esp-idf/en/latest/esp32c3/api-reference/peripherals/spi_master.html
