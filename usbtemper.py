import usb.core
import usb.util
import sys
import struct

dev = usb.core.find(idVendor=0x413d, idProduct=0x2107)

#Complete nonsense code that it needs:
COMMANDS = {
    'temp': b'\x01\x80\x33\x01\x00\x00\x00\x00',
}

def findtemp():
    #Voodoo to prevent the things from saying ERRNO 16 RESOURCE BUSY
    for cfg in dev:
        for intf in cfg:
            if dev.is_kernel_driver_active(intf.bInterfaceNumber):
                try:
                    dev.detach_kernel_driver(intf.bInterfaceNumber)
                except usb.core.USBError as e:
                    sys.exit("Could not detatch kernel driver from interface({0}): {1}".format(intf.bInterfaceNumber, str(e)))

    dev.set_configuration()
    usb.util.claim_interface(dev, 1)

    #Write and read to thing twice because it only works every other time otherwise
    dev.write(0x2, COMMANDS['temp'])
    dev.read(0x82, 0x8)
    dev.write(0x2, COMMANDS['temp'])
    tempy = dev.read(0x82, 0x8)
    usb.util.dispose_resources(dev)
    
    temp_data = (struct.unpack_from('>h', tempy, 2)[0] / 100)*1.8 +32
    return round(temp_data)

def findhum(): 
    #Voodoo to prevent the things from saying ERRNO 16 RESOURCE BUSY
    for cfg in dev:
        for intf in cfg:
            if dev.is_kernel_driver_active(intf.bInterfaceNumber):
                try:
                    dev.detach_kernel_driver(intf.bInterfaceNumber)
                except usb.core.USBError as e:
                    sys.exit("Could not detatch kernel driver from interface({0}): {1}".format(intf.bInterfaceNumber, str(e)))

    dev.set_configuration()
    usb.util.claim_interface(dev, 1)

    #Write and read to thing twice because it only works every other time otherwise
    dev.write(0x2, COMMANDS['temp'])
    dev.read(0x82, 0x8)
    dev.write(0x2, COMMANDS['temp'])
    tempy = dev.read(0x82, 0x8)
    usb.util.dispose_resources(dev)

    hum_data = (struct.unpack_from('>H', tempy, 4)[0]/100)
    return round(hum_data)

#I don't know how the fuck I did it, or if I could ever do it again, but its done.
