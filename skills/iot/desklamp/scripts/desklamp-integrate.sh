#!/bin/bash
# desklamp-integrate.sh — Copia los archivos de DeskLamp al proyecto DeskMate
# Ejecutar desde el servidor. Copia a laptop CachyOS via SSH.
# 
# Uso: bash scripts/desklamp-integrate.sh

PROJECT_DIR="/home/migbert/proyectos/deskmate"
SRC_DIR="/tmp/desklamp"

echo "==> Copiando led_control.h y led_control.c a $PROJECT_DIR/main/"
ssh cachy "cp $SRC_DIR/led_control.h $PROJECT_DIR/main/"
ssh cachy "cp $SRC_DIR/led_control.c $PROJECT_DIR/main/"
echo "OK"

echo ""
echo "==> Archivos copiados. Edita main.c manualmente para integrar:"
echo "    1. #include \"led_control.h\""
echo "    2. led_init() después de init display"
echo "    3. led_tick() en el bucle principal"
echo "    4. led_cycle_mode() en handler del botón"
echo ""
echo "==> Build remoto:"
echo "    ssh cachy \"cd $PROJECT_DIR && . ~/.espressif/v5.5.3/esp-idf/export.sh && idf.py build\""
echo ""
echo "==> Flash remoto:"
echo "    ssh cachy \"cd $PROJECT_DIR && . ~/.espressif/v5.5.3/esp-idf/export.sh && fuser -k /dev/ttyACM0 2>/dev/null; idf.py -p /dev/ttyACM0 flash\""
