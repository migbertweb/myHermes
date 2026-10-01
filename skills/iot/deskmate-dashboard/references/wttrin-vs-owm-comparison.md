# wttr.in vs OpenWeatherMap para DeskMate

## Evaluación — 2026-06-20

Se evaluó [wttr.in](https://github.com/chubin/wttr.in) como reemplazo de OWM para el DeskMate por su simplicidad (no requiere API key, formato texto).

## wttr.in - Ventajas

- **No necesita API key** — solo `curl wttr.in/Joinville`
- **Formato personalizado** por placeholder: `?format=%t+%f+%h+%C`
  - `%t` = temp, `%f` = sensación, `%h` = humedad, `%C` = texto clima
  - Respuesta en texto plano: `+14°C +10°C 99 Moderate rain` (~50 bytes)
  - Sin JSON, sin cJSON, solo un `sscanf()` o `strncpy()` en el ESP32
- **Internacionalización**: `?lang=es`

## wttr.in - Desventajas para ESP32

| Aspecto | OWM | wttr.in j1 | wttr.in custom |
|---------|-----|------------|----------------|
| Tamaño respuesta | **555 bytes** (current) | 39,289 bytes | ~50 bytes (texto) |
| Parseo | cJSON | cJSON | sscanf/strncpy |
| API Key | ✅ Sí (gratis) | ✅ No necesita | ✅ No necesita |
| Pronóstico | 5 días / 16KB | 3 días | Solo current |
| Iconos XBM | ✅ Mapeo OWM listo (12 iconos) | ❌ Habría que rehacer | ❌ Habría que rehacer |
| Español | ✅ `lang=es` | ✅ `lang=es` | ✅ `lang=es` |
| Latencia | ~1-2s | ~1-2s | ~1-2s |

## Decisión: Seguir con OWM

Para DeskMate, OWM es superior porque:
1. **555 bytes** para current weather vs **39KB** de wttr.in j1
2. **Mapeo de iconos XBM ya implementado** con códigos OWM (01d, 10d, etc.)
3. **Pronóstico de 5 días** ya parseado y funcionando
4. **cJSON ya está en el proyecto** — no hay ganancia en eliminar la dependencia

wttr.in podría ser útil para:
- Proyectos más simples sin display gráfico (solo texto)
- Fallback si OWM falla (pero los fixes de refresh condicional hacen esto innecesario)
- Prototipos rápidos sin API key
