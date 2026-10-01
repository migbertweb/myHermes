# WebSocket + HTTP Server en ESP32-C3 (ESP-IDF v5.5)

## Config sdkconfig obligatoria

```c
CONFIG_HTTPD_WS_SUPPORT=y       // Sin esto, tipos y macros WS no compilan
CONFIG_LWIP_MAX_SOCKETS=12      // HTTP server necesita ~10 sockets mínimo (el default 4 no alcanza)
```

`CONFIG_HTTPD_WS_SUPPORT` viene deshabilitado por defecto. Sin él, `httpd_ws_frame_t`, `HTTPD_WS_TYPE_TEXT`, `.is_websocket = true` no existen en el header.

`CONFIG_LWIP_MAX_SOCKETS=4` (default) causa error en runtime:
```
E (31575) httpd: Config option max_open_sockets is too large (max allowed 1, 3 sockets used by HTTP server internally)
```

## WebSocket client tracking

Usar array simple de FDs, limpieza en fallo de envío:

```c
#define MAX_WS_CLIENTS 4
static int ws_fds[MAX_WS_CLIENTS] = {-1};

// En ws_handler, HTTP_GET → handshake:
int fd = httpd_req_to_sockfd(req);
ws_add_client(fd);

// ws_broadcast:
void ws_broadcast(const char *json) {
    httpd_ws_frame_t pkt = {
        .final = true, .type = HTTPD_WS_TYPE_TEXT,
        .payload = (uint8_t*)json, .len = strlen(json)
    };
    for (int i = 0; i < MAX_WS_CLIENTS; i++) {
        if (ws_fds[i] == -1) continue;
        if (httpd_ws_send_frame_async(server, ws_fds[i], &pkt) != ESP_OK)
            ws_remove_client(ws_fds[i]);  // socket cerrado, limpiar
    }
}
```

## IP fija: CRÍTICO — orden de operaciones

```c
// ❌ ESTO CRASHEA (boot congelado, sin serial):
esp_netif_t *netif = esp_netif_create_default_wifi_sta();
esp_netif_dhcpc_stop(netif);    // DHCPC maybe no ready
esp_netif_set_ip_info(...);     // boot freeze

// ✅ ORDEN CORRECTO (no verificado en este proyecto, pero es el patrón IDF):
esp_netif_t *netif = esp_netif_create_default_wifi_sta();
wifi_init(...);
wifi_set_config(...);
wifi_start();
// Después de que WiFi está UP, detener DHCP y fijar IP
esp_netif_dhcpc_stop(netif);
esp_netif_set_ip_info(netif, &ip_info);
```

Mejor aún: **reserva DHCP en el router** para la MAC del ESP32. MAC conocida: `8c:d0:b2:a9:f8:67`.

## Weather icon → emoji mapping

Códigos OWM a emoji para el JS:

| OWM code | Emoji | Condición |
|---|---|---|
| 01d | ☀️ | Soleado día |
| 01n | 🌙 | Despejado noche |
| 02d | ⛅ | Parcialmente nublado día |
| 02n | ⛅ | Parcialmente nublado noche |
| 03d/n | ☁️ | Nubes dispersas |
| 04d/n | ☁️ | Muy nublado |
| 09d/n | 🌧️ | Lluvia ligera |
| 10d | 🌦️ | Lluvia día |
| 10n | 🌦️ | Lluvia noche |
| 11d/n | ⛈️ | Tormenta |
| 13d/n | 🌨️ | Nieve |
| 50d/n | 🌫️ | Niebla/Viento |

## Comandos WebSocket JSON

```json
// Desde panel → ESP32:
{"command":"led_mode","mode":0}         // 0-7
{"command":"led_color","r":255,"g":0,"b":0}
{"command":"led_brightness","value":128}  // 0-255
{"command":"led_power","on":true}

// Desde ESP32 → panel (broadcast cada 1s):
{"type":"clock","time":"17:04:12","wday":"Domingo","date":"19/07/2026"}
{"type":"weather","icon":"☀️","temp":30,"desc":"cielo claro","pop":"Sin lluvia"}
{"type":"forecast","days":[{"label":"LUN","icon":"☁️","max":29,"min":20,"pop":0},...]}
{"type":"led","mode":2}
```
