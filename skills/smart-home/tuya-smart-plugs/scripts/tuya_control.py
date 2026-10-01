#!/home/piro/.tuya-venv/bin/python3
"""Control de enchufes Tuya"""
import tinytuya
import sys

DEVICES = {
    "cuarto": {
        "id": "5676087234ab950d3f67",
        "ip": "192.168.1.2",
        "key": "k;q<#)ei6~H2R<`p",
        "version": 3.3
    },
    "sala": {
        "id": "eb36eef3376660c896dcqo",
        "ip": "192.168.1.4",
        "key": "!5fV~`:v7+i@@nIL",
        "version": 3.5
    },
    "tramontina": {
        "id": "vdevo178131546308609",
        "ip": "",
        "key": "m~IClr['!./`>P=B",
        "version": 3.1
    }
}

if len(sys.argv) < 2 or sys.argv[1] not in DEVICES:
    print(f"Enchufes: {', '.join(DEVICES.keys())}")
    print(f"Uso: {sys.argv[0]} <enchufe> <on|off|status>")
    sys.exit(1)

device = DEVICES[sys.argv[1]]
action = sys.argv[2] if len(sys.argv) > 2 else "status"

if not device["ip"]:
    print(f"{sys.argv[1]}: sin IP (probablemente desconectado)")
    sys.exit(1)

d = tinytuya.OutletDevice(
    device["id"], device["ip"],
    device["key"],
    version=device["version"]
)
d.set_socketPersistent(False)
d.set_socketTimeout(5)

if action == "status":
    try:
        s = d.status()
        on_off = "ENCENDIDO" if s["dps"]["1"] else "APAGADO"
        watts = s["dps"].get("19", 0) / 10
        print(f"{sys.argv[1]}: {on_off} ({watts}W)")
    except Exception as e:
        print(f"Error: {e}")
elif action == "on":
    d.turn_on()
    print(f"{sys.argv[1]}: ENCENDIDO")
elif action == "off":
    d.turn_off()
    print(f"{sys.argv[1]}: APAGADO")
else:
    print(f"Acción inválida: {action} (on/off/status)")
