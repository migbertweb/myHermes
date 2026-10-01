# Weather Refresh & WiFi Icon Fixes — 2026-06-20

## Bugs encontrados y corregidos en main.c

### Bug 1: `wifi_connected` nunca se ponía en `true`

**Síntoma**: El icono WiFi en el display siempre se mostraba rojo/desconectado, aunque la conectividad funcionara perfectamente (los fetch de OWM y forecast funcionaban).

**Causa raíz**: La variable `static bool wifi_connected = false;` se inicializaba en `false` pero **nunca** se le asignaba `true` en ningún lado del código. Solo se leía para decidir qué icono mostrar.

**Fix** (en `wifi_event_handler`):
- `IP_EVENT_STA_GOT_IP`: añadir `wifi_connected = true;`
- `WIFI_EVENT_STA_DISCONNECTED`: añadir `wifi_connected = false;`

**Evidencia**: `grep -n 'wifi_connected' main/main.c` antes del fix solo mostraba lecturas, ninguna escritura de `true`.

### Bug 2: Weather refresh sobrescribía datos válidos en fetch fallido

**Síntoma**: El usuario reportó que la temperatura no se actualizaba "desde ayer". Tras un refresh que falla (WiFi inestable, timeout HTTP), los datos previos válidos se perdían.

**Causa raíz**: En el bucle principal:
```c
if (time_synced && (now - last_weather_fetch >= WEATHER_INTERVAL)) {
    weather_data = weather_fetch();  // Sobrescribe aunque falle
    ...
}
```
`weather_fetch()` retorna `valid = false` si algo sale mal. La asignación directa pisa el struct completo, perdiendo la última lectura válida.

**Fix**: Usar variable temporal con guarda condicional:
```c
weather_data_t new_data = weather_fetch();
if (new_data.valid) {
    weather_data = new_data;
}
```

### Estado actual (post-fix)

- Build exitoso con `idf.py build` (sin warnings nuevos)
- Flash exitoso a ESP32-C3
- Salida serial confirmada:
  ```
  I (8108) deskmate: HTTP status: 200, content_length: 555
  I (8118) deskmate: Weather: 16.8C (feels 17.1C) - lluvia de gran intensidad
  I (8448) deskmate: Forecast HTTP status: 200, content_length: 16528
  I (8998) deskmate: FCST DOM: 14/21C POP:0%
  I (8998) deskmate: FCST LUN: 11/24C POP:29%
  I (8998) deskmate: FCST MAR: 11/19C POP:100%
  I (8998) deskmate: FCST MIE: 7/17C POP:0%
  ```

### Espacio en partición

```
deskmate.bin binary size 0xc90b0 bytes (823KB)
Smallest app partition is 0x100000 bytes (1MB)
0x36f50 bytes (21%) free
```
