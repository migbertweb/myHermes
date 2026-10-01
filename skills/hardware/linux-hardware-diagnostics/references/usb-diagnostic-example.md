# USB Diagnostic Example — Pendrive Not Detected After Disconnect

## Scenario

Pendrive (31.5 GB, vendor `346d:5678`) was detected initially as `/dev/sdc` with 3 partitions, but disconnected after ~22 seconds. After reconnecting, the system did not detect it at all.

## Initial Detection (dmesg)

```
[+119s] usb 1-1: new high-speed USB device number 11
[+119s] usb 1-1: New USB device found, idVendor=346d, idProduct=5678
[+119s] usb 1-1: Product: Disk 2.0
[+120s] sd 2:0:0:0: [sdc] 61440000 512-byte logical blocks: (31.5 GB/29.3 GiB)
[+120s] sdc: sdc1 sdc2 sdc3
[+120s] sd 2:0:0:0: [sdc] Attached SCSI removable disk
[+141s] usb 1-1: USB disconnect, device number 11
[+147s] usb 1-1: new full-speed USB device number 12
[+147s] usb 1-1: New USB device found, idVendor=248a, idProduct=fa02
[+147s] usb 1-1: Product: Wireless Receiver (mouse)
```

## After Reconnecting — Nothing

| Check | Result |
|-------|--------|
| `lsusb` | No device with `346d:5678` |
| `sudo dmesg` (fresh) | Only UFW block messages — zero USB events |
| `lsblk` | No `sdc`, no new block device |
| `lsusb -t` | Port 1-1 occupied by mouse dongle |

## Interpretation

- **Port conflict**: the mouse receiver connected on the same port (1-1) after the pendrive disconnected. If the user reconnected the pendrive where the mouse is, that port is already taken.
- **Complete silence on reconnection** → either the pendrive was plugged into a different port that is dead, or the pendrive itself is electrically dead.
- **No kernel event at all** (not even a failed USB enumeration) → the device is not making electrical contact.

## Key Takeaway

When a USB device was detected once but then disappears and won't reappear, and there's zero dmesg activity on reconnection, the problem is at the **physical/electrical layer** — not software. The device, the cable, or the port is failed.
