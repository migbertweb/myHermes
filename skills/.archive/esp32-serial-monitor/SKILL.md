---
name: esp32-serial-monitor
description: "Use when reading ESP32 serial logs for health."
---
# ESP32 Serial Monitor Diagnosis

Interpretación del monitor serial de ESP32 (ESP-IDF) para validar que el firmware corre
sano. Aplica a cualquier proyecto ESP-IDF (DeskMate, DeskLamp, etc.).

## Lectura sin TTY

`idf.py monitor` y `miniterm` requieren TTY. Para leer desde sesión no interactiva
(Hermes, cron, SSH sin pty), usar pyserial:

```bash
python3 -c "
import serial, time
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=2)
time.sleep(1)
ser.reset_input_buffer()
start = time.time()
while time.time() - start < 25:
    try:
        data = ser.read(ser.in_waiting or 1).decode('utf-8', errors='replace')
        if data: print(data, end='', flush=True)
    except Exception as e:
        print(f'[ERR] {e}')
        break
ser.close()
"
```

Capturar 20-30s es suficiente para validar estabilidad: ciclo del bucle principal,
auto-rotaciones, ausencia de errores.

## Checklist de salud

| Señal | Sano | Problema |
|---|---|---|
| Reboots | uno solo al conectar | múltiples `boot` en la ventana = crash loop |
| Timestamps ESP `I (xxxxx)` | intervalos regulares (~ciclo del loop) | saltos grandes = tick stall / freeze |
| Errores `E (...)` | ninguno | HTTP fails, stack overflow, watchdog |
| Rotaciones/transiciones | en el intervalo configurado | cada ~200ms = falta `vTaskDelay` en el loop |
| Reloj/estado | avanza correcto | estancado = freeze |

## Pitfall: segundo faltante en logs = log drop, NO salto de reloj

Un log por segundo puede saltarse uno (`12:09:56` → `12:09:58`, falta `57`). Parece
anomalía, casi siempre es benigno:

- **Diagnóstico**: comparar los timestamps internos del ESP (`I (169546)` → `I (170606)`).
  Si avanzan el intervalo normal (~1060ms para loop de 1s con overhead), el reloj de pared
  nunca saltó — el print de ese segundo se perdió en el buffer USB CDC. Si los timestamps
  internos TAMBIÉN saltan ~2s, el tick/RTC sí se estancó.
- **Causa**: a 115200 baud con un log por segundo, el CDC ocasionalmente pierde un frame
  cuando colisiona con otra actividad (WebSocket broadcast, refresh HTTP).
- **Veredicto**: benigno, no afecta display ni firmware. No requiere fix.
- **Regla**: nunca reportar como anomalía del dispositivo sin verificar los timestamps
  internos primero.

## Pitfall: pantalla negra con firmware sano

Si el serial muestra WiFi conectado, NTP sincronizado y weather fetch OK pero el display
está negro, el firmware NO es el problema. Revisar el hardware en orden:
1. **Backlight (BL) sin 3.3V** = pantalla completamente negra aunque el chip reciba datos.
2. VCC del display a 5V en vez de 3.3V (ST7789 es 3.3V — 5V lo quema).
3. GND del display sin conexión (sin referencia común no hay señal).
4. Cable suelto en MOSI/SCLK/CS/DC/RST.
5. Diagnóstico: medir BL a 3.3V vs GND con multímetro. Si el serial funciona, el ESP32
   está bien — el problema es display o cableado.

## Verificación de puerto

```bash
ls -la /dev/ttyACM*          # ¿existe? (grupo uucp/dialout para permisos)
fuser -k /dev/ttyACM0        # liberar puerto antes de flashear (esperar 2-3s, se desregistra)
```

## Referencias por proyecto

- **DeskMate** (ST7789 + WS2812B + WiFi): skill `deskmate-dashboard` — pinout, layout,
  pitfalls de firmware, monitor script.
- **DeskLamp** (anillo WS2812B): skill `desklamp` — GPIO 5 vs 8, timing RMT, GRB.
- **Crash decode RISC-V**: skill `esp-idf-ssh-workflow` — `riscv32-esp-elf-addr2line`.
