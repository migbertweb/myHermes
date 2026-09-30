import tinytuya

DEVICES = [
    {"name": "sala", "ip": "192.168.1.12", "id": "eb36eef3376660c896dcqo", "key": "!5fV~`:v7+i@@nIL", "version": 3.5},
    {"name": "cuarto", "ip": "192.168.1.13", "id": "5676087234ab950d3f67", "key": "k;q<#)ei6~H2R<`p", "version": 3.3},
]

for dev in DEVICES:
    print(f"--- Testing {dev['name']} ---")
    try:
        d = tinytuya.OutletDevice(dev['ip'], dev['id'], dev['key'], version=dev['version'])
        d.set_socketTimeout(5)
        d.set_socketPersistent(False)
        status = d.status()
        print(f"Status: {status}")
    except Exception as e:
        print(f"Error: {e}")
