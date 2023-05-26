import pycom
from network import Bluetooth
import time
import machine

pycom.heartbeat(False)
pycom.rgbled(0x550000)  # Red

wait_time = None
guard_contact = False
advertising = False

bluetooth = Bluetooth()
bluetooth.init()

def connection_callback (bt_o):
    global guard_contact
    events = bt_o.events()   # this method returns the flags and clears the internal registry
    if events & Bluetooth.CLIENT_CONNECTED:
        pycom.rgbled(0x005500)  # green
    elif events & Bluetooth.CLIENT_DISCONNECTED:
        guard_contact = True
        pycom.rgbled(0x550000)  # Red


# alive_message = bluetooth.service(b'0000000000000000')
# alive_message.characteristic(uuid = '0000000000000001', value = b'Im OK')
while True:

    if guard_contact:
        print('guard contact')
        bluetooth.advertise(False)
        advertising = False
        bluetooth.start_scan(5)
        pycom.rgbled(0x550000) #red
        guard_contact = False

    elif bluetooth.isscanning():
        print('scanning after timing from guard')
        adv = bluetooth.get_adv()

        if adv:
            print(bluetooth.resolve_adv_data(adv.data, bluetooth.ADV_NAME_CMPL))

            if bluetooth.resolve_adv_data(adv.data, bluetooth.ADV_NAME_CMPL) == 'guard_bee':
                print('found it')
                wait_time = int.from_bytes(bluetooth.resolve_adv_data(adv.data, bluetooth.ADV_SERVICE_DATA), 'big')
                bluetooth.stop_scan()

    elif wait_time:
        print('going to sleep')
        pycom.rgbled(0x000000) #off
        machine.sleep(wait_time * 1000)
        print('woke up!')
        wait_time = None

    elif not advertising:
        bluetooth.deinit()
        bluetooth.init()
        bluetooth.callback(trigger=Bluetooth.CLIENT_CONNECTED | Bluetooth.CLIENT_DISCONNECTED, handler=connection_callback)
        
        print('advertising!')
        pycom.rgbled(0x000055) #blue

        bluetooth.set_advertisement(name = "bee_hive", manufacturer_data = "fipy")
        bluetooth.advertise(True)
        advertising = True
