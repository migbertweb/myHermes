# Diagnóstico: Pronóstico OWM muestra "Sin datos"

## Checklist de causas posibles

### 1. Buffer HTTP insuficiente → JSON truncado

La respuesta de `api.openweathermap.org/data/2.5/forecast` puede superar los 16KB.

**Verificación desde PC:**
```bash
# Medir tamaño real de la respuesta
curl -s "http://api.openweathermap.org/data/2.5/forecast?id=CIUDAD_ID&appid=API_KEY&units=metric&lang=es" -o /tmp/forecast.json -w "HTTP %{http_code}, bytes=%{size_download}"

# Validar si el JSON completo es válido
python3 -c "import json; json.load(open('/tmp/forecast.json')); print('VALID')"

# Validar si el JSON truncado al límite actual es válido
python3 -c "
import json
data = open('/tmp/forecast.json').read()
limit = 16384  # o el valor de FORECAST_BUFFER_MAX
try:
    json.loads(data[:limit])
    print(f'{limit}: VALID')
except json.JSONDecodeError as e:
    print(f'{limit}: INVALID - {e}')
"
```

**Fix:** Aumentar `FORECAST_BUFFER_MAX` en `main/main.c` (mínimo 20000).

### 2. HTTP request falla silenciosamente

**Verificación:** Leer logs seriales. Si el ESP32 imprime:
- `Forecast HTTP open failed` → problema de red/conexión
- `Forecast bad response: status=XXX` → API key inválida, city ID incorrecto, o límite de requests excedido
- `Forecast JSON parse error` → probablemente buffer insuficiente (caso 1)

**Fix según el error:**
- `status=401` → API key incorrecta o no activada para forecast
- `status=404` → City ID inválido
- `status=429` → Demasiadas requests, esperar o cambiar a plan pago

### 3. Tiempo no sincronizado → forecast nunca se pide

El código en `app_main()` solo llama a `forecast_fetch()` si `time_synced == true`. Si SNTP no sincroniza (ej. firewall bloquea NTP), el forecast nunca se obtiene.

**Verificación:** El reloj muestra hora incorrecta en el display. El LED verde de sincronización (píxel en esquina inferior derecha) no aparece.

### 4. Parseo falla por formato inesperado

OWM puede cambiar la estructura JSON sin previo aviso. Verificar que el response JSON tenga la estructura esperada:

```python
python3 -c "
import json
data = json.load(open('/tmp/forecast.json'))
print('Keys:', list(data.keys()))
print('list entries:', len(data.get('list', [])))
if data.get('list'):
    print('First entry keys:', list(data['list'][0].keys()))
"
```

## Procedimiento completo de diagnóstico remoto (SSH)

```bash
# 1. Verificar que el ESP32 responde
ping 192.168.1.14

# 2. Testear la API de forecast directamente desde el servidor
curl -s "http://api.openweathermap.org/data/2.5/forecast?id=3459712&appid=API_KEY&units=metric&lang=es" -o /tmp/owm_test.json -w "%{http_code}, %{size_download}B"

# 3. Verificar validez del JSON completo
python3 -c "import json; json.load(open('/tmp/owm_test.json')); print('OK')"

# 4. Verificar si el buffer actual del ESP32 lo cortaría
python3 -c "
data = open('/tmp/owm_test.json').read()
limit = 20000  # FORECAST_BUFFER_MAX actual
print(f'Response: {len(data)}B, Buffer: {limit}B, {\"FITS\" if len(data) <= limit else \"OVERFLOW!\"}')"

# 5. Leer logs del ESP32 (si hay conexión serial)
ssh servidor "cat /dev/ttyACM0"  # o usar el script read_serial.py
```
