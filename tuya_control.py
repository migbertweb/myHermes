import sys
import tinytuya

# Updated according to user's physical swap:
# Enchufe 2 (now in Sala) -> ID: 5676087234ab950d3f67, IP: 192.168.1.12
# TV cuarto (now in Cuarto) -> ID: eb36eef3376660c896dcqo, IP: 192.168.1.13

DEVICES = {
    'cuarto': {
        'id': 'eb36eef3376660c896dcqo', 
        'ip': '192.168.1.13', 
        'key': 'mZa:IjyK}G`6TUBo', 
        'version': 3.5
    }, 
    'sala': {
        'id': '5676087234ab950d3f67', 
        'ip': '192.168.1.12', 
        'key': 'AiI*Q{_~@FgIp!vY', 
        'version': 3.3
    }, 
    'tramontina': {
        'id': 'vdevo178131546308609', 
        'ip': '', 
        'key': "m~IClr['!./`>P=B", 
        'version': 3.1
    }
}

def control(name, action):
    if name not in DEVICES:
        print(f"Device {name} not found")
        return
    
    dev_data = DEVICES[name]
    if not dev_data["ip"]:
        print(f"Device {name} has no IP configured")
        return

    try:
        d = tinytuya.OutletDevice(dev_data["ip"], dev_data["id"], dev_data["key"], version=dev_data["version"])
        d.set_socketPersistent(False)
        d.set_socketTimeout(5)
        
        if action == "on":
            d.turn_on()
            print(f"{name} turned ON")
        elif action == "off":
            d.turn_off()
            print(f"{name} turned OFF")
        elif action == "status":
            print(d.status())
        else:
            print("Invalid action. Use on/off/status")
    except Exception as e:
        print(f"Error controlling {name}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: tuya <device> <action>")
        sys.exit(1)
    control(sys.argv[1], sys.argv[2])
