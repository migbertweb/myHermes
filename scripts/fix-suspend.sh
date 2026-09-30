#!/bin/bash
# Fix suspend: set USB devices that block suspend to auto power control
echo "Aplicando fix de suspensión..."
echo auto > /sys/bus/usb/devices/usb1/1-1/power/control 2>/dev/null
echo auto > /sys/bus/usb/devices/usb1/1-7/power/control 2>/dev/null
echo "1-1: $(cat /sys/bus/usb/devices/usb1/1-1/power/control)"
echo "1-7: $(cat /sys/bus/usb/devices/usb1/1-7/power/control)"
echo "Fix aplicado."
