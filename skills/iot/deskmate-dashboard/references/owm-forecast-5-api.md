# OWM 5 Day / 3 Hour Forecast API

Documentación de investigación para implementar pronóstico extendido en DeskMate.

## Endpoint

```
api.openweathermap.org/data/2.5/forecast?id=3459712&appid=API_KEY&units=metric&lang=es
```

Misma API key que el endpoint `/weather` actual. Incluido en plan FREE (60 req/min, 1000 req/día).

## Diferencias clave vs /weather actual

| Aspecto | /weather (actual) | /forecast |
|---------|-------------------|-----------|
| Tamaño respuesta | ~500 bytes | ~15-20 KB |
| Entradas | 1 | 40 (5 días × 8 intervalos de 3h) |
| Formato | `{...}` | `{list: [{...}, ...], ...}` |
| `pop` | ❌ No disponible | ✅ Probability of Precipitation (0.0–1.0) |
| `temp_min/max` | Única temp | Cada bloque tiene su min/max |

## Estructura de respuesta (un bloque de `list[]`)

```json
{
  "dt": 1685134800,
  "main": {
    "temp": 25.5,
    "feels_like": 25.8,
    "temp_min": 24.2,
    "temp_max": 26.1,
    "pressure": 1013,
    "sea_level": 1013,
    "grnd_level": 1009,
    "humidity": 65
  },
  "weather": [{"id": 802, "main": "Clouds", "description": "nubes dispersas", "icon": "03d"}],
  "clouds": {"all": 40},
  "wind": {"speed": 3.6, "deg": 120},
  "visibility": 10000,
  "pop": 0.3,
  "rain": {"3h": 0.5},
  "dt_txt": "2023-05-27 12:00:00"
}
```

## Campo `pop` (Probability of Precipitation)

- Valor: 0.0 a 1.0 (multiplicar por 100 para porcentaje)
- 0.0 = 0% probabilidad, 1.0 = 100%
- Presente en CADA bloque de 3h
- Los valores altos (>0.7) suelen ir acompañados de `rain.3h` o `snow.3h`

## Estrategia recomendada para ESP32-C3 (400KB SRAM)

### Opción A: Parse streaming + agregación diaria (recomendada)
1. Abrir conexión HTTP, leer headers
2. Usar cJSON para parsear incrementalmente o leer todo en heap (~20KB buffer)
3. Iterar los 40 bloques, agrupar por día calendario
4. Por cada día extraer: temp_max, temp_min, icono representativo (mediodía), POP máximo
5. Almacenar solo 4-5 días resumidos (~80 bytes c/u)
6. Liberar buffer JSON inmediatamente después

### Opción B: Solo próximas 24h (más ligero)
- Parsear solo los primeros 8 bloques (24h)
- Sin agregación: mostrar 4 franjas de 6h (mañana/tarde/noche/madrugada)
- Reduce buffer a ~4KB

### Consideraciones de memoria
- Buffer HTTP: ~4096 bytes (heap) para lectura fragmentada
- cJSON tree para 40 entradas: ~8-12KB adicional
- Total extra: ~12-20KB heap — factible en 400KB SRAM pero requiere `malloc`/`free` cuidadoso
- No usar buffers en stack — mantener patrón heap actual

## Layout propuesto (240×240)

```
┌─────────────────────────┐
│   12:45                 │ ← hora (sin cambios)
│   45                     │ ← segundos (sin cambios)
│   Domingo               │ ← día (sin cambios)
│   07/06/2026            │ ← fecha (sin cambios)
│ ─────────────────────── │
│  [☁️] 19°C              │ ← icono + temp (sin cambios)
│  NUBES                  │ ← descripción (sin cambios)
│  Sens: 20°C             │ ← sensación (sin cambios)
│ ─────────────────────── │
│  LUN  ☀️  28°/22°  30%  │ ← forecast día 1
│  MAR  ⛅  26°/20°  60%  │ ← forecast día 2
│  MIE  🌧️  24°/19°  80%  │ ← forecast día 3
│  JUE  ☁️  25°/21°  20%  │ ← forecast día 4
└─────────────────────────┘
```

Cada línea de forecast: 3-4 letras día + icono chico 16×16 + temp max/min + POP%.
4 líneas × ~18px c/u = ~72px vertical adicional.

## Dependencias necesarias
- cJSON (ya incluido en ESP-IDF)
- Parseo de `dt_txt` para extraer día (actualmente solo parsea el primer weather block)
- Función hash/array para agregar 8 bloques de 3h en un resumen diario
- Iconos clima adicionales: 16×16 para forecast (o reutilizar 32×32 escalados a 16×16)

## Recursos
- [Documentación oficial OWM Forecast 5](https://openweathermap.org/forecast5)
- Plan FREE incluye: Current Weather + Forecast 5 + UV Index (básico)
