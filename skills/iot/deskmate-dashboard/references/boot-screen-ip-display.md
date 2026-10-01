# Pantalla de boot con IP (display_boot)

## Propósito

Mostrar la IP asignada por DHCP en la pantalla ST7789 durante ~5s al iniciar el ESP32. Permite al usuario ver la IP sin escanear la red ni conectar el monitor serial.

## Variables globales (main.c)

```c
static char current_ip[16] = "0.0.0.0";   // IP más reciente
static bool boot_done = false;             // transición boot→reloj
static int  boot_counter = 0;              // contador de ~5s
```

## Captura de IP en event handler

```c
} else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
    ip_event_got_ip_t *event = (ip_event_got_ip_t *)data;
    snprintf(current_ip, sizeof(current_ip), IPSTR, IP2STR(&event->ip_info.ip));
    wifi_connected = true;
    // ...
}
```

## display_boot() — función renderizada antes del reloj

```c
static void display_boot(void)
{
    char bar[24];
    static bool first = true;
    if (first) {
        lcd_fill_screen(COLOR_BLACK);
        first = false;
    }
    lcd_draw_text_centered(30, "DeskMate", COLOR_TEAL, 4);

    snprintf(bar, sizeof(bar), "IP: %s", current_ip);
    lcd_draw_text_centered_8x13(90, bar, wifi_connected ? COLOR_GREEN : COLOR_MUTED, 2);

    lcd_draw_text_centered_8x13(120, "Sukuna-78-2.4g", COLOR_MUTED, 1);
    lcd_draw_text_centered_8x13(160, "Conectando...", COLOR_MUTED, 1);

    /* Barra de progreso */
    uint8_t dots = boot_counter % 4 + 1;
    for (int i = 0; i < dots; i++)
        lcd_draw_rect(100 + i * 16, 200, 8, 8, COLOR_SEPARATOR);
}
```

## Transición en bucle principal

```c
while (1) {
    if (!boot_done && time_synced) {
        display_boot();
        boot_counter++;
        if (boot_counter >= 5) {
            boot_done = true;
            clock_first_run = true;
            lcd_fill_screen(COLOR_BLACK);
        }
    } else if (current_screen == SCREEN_CLOCK) {
        display_clock();
        display_status_bar();
    } else {
        display_forecast();
    }
    // ... resto del bucle ...
}
```

## Consideraciones

- `time_synced` garantiza que WiFi está conectado (SNTP solo funciona con IP)
- La IP se muestra en verde si `wifi_connected == true`, en gris si no
- `boot_counter >= 5` da ~5s (el bucle corre a 1Hz)
- La transición limpia la pantalla con `lcd_fill_screen(COLOR_BLACK)`
- No reutilizar `clock_first_run` para el boot — confunde el dibujo diferencial del reloj

## IP fija (NO IMPLEMENTADA — causa freeze)

`esp_netif_dhcpc_stop(netif)` + `esp_netif_set_ip_info()` antes de `wifi_start()` congela el ESP32 sin salida serial. Usar reserva DHCP en el router o mDNS.
