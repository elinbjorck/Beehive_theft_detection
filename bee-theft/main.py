import pycom
from network import Bluetooth
import machine
import time

nr_of_hives = 2
id_set = set()
id_set_counter = set()

wait_time = 60
adv_time = 3
scan_time = 5

hive_contact = False
no_contact_count = 0
max_no_contact = 5

pycom.heartbeat(False)
bluetooth = Bluetooth()
pycom.rgbled(0x550000)  # Red

def connection_callback (bt_o):
    events = bt_o.events()   # this method returns the flags and clears the internal registry

    if events & Bluetooth.CLIENT_CONNECTED:
        pycom.rgbled(0x005500)  # green

    elif events & Bluetooth.CLIENT_DISCONNECTED:
        pycom.rgbled(0x550000)  # Red


bluetooth.callback(trigger=Bluetooth.CLIENT_CONNECTED | Bluetooth.CLIENT_DISCONNECTED, handler=connection_callback)
bluetooth.start_scan(-1)

while len(id_set) < nr_of_hives:
    adv = bluetooth.get_adv()

    if adv:

        if bluetooth.resolve_adv_data(adv.data, bluetooth.ADV_NAME_CMPL) == 'bee_hive':
            id_set.add(adv.mac)
    else:
        time.sleep(0.5)

for mac in id_set:
    connection = None

    try:
        connection = bluetooth.connect(mac)
        hive_contact = True

    except:
        print('Error while connecting to the bluetooth device or reading data.')
    if connection:
        connection.disconnect()

print('Located correct number of hives. Saved mac-adresses.')    
bluetooth.stop_scan()

while True:

    if hive_contact:
        pycom.rgbled(0x000055)
        bluetooth.set_advertisement(name = "guard_bee", manufacturer_data = "fipy", service_data = wait_time.to_bytes(4, 'big'))

        bluetooth.advertise(True)
        time.sleep(adv_time)
        bluetooth.advertise(False)

        pycom.rgbled(0x000000) #off
        machine.sleep((wait_time - adv_time) * 1000)
        pycom.rgbled(0x550000) #red

        bluetooth = Bluetooth()
        bluetooth.callback(trigger=Bluetooth.CLIENT_CONNECTED | Bluetooth.CLIENT_DISCONNECTED, handler=connection_callback)
        bluetooth.start_scan(scan_time)
        hive_contact = False

    elif bluetooth.isscanning():
        adv = bluetooth.get_adv()

        if adv:

            if bluetooth.resolve_adv_data(adv.data, bluetooth.ADV_NAME_CMPL) == 'bee_hive':
                id_set.add(adv.mac)

                if len(id_set) == nr_of_hives:
                    connection = None
                    try:
                        connection = bluetooth.connect(adv.mac)
                        id_set_counter.add(adv.mac)

                    except:
                        file = open('data.txt')
                        print('Error while connecting to the bluetooth device or reading data.')
                    if connection:
                        connection.disconnect()
                        if not bluetooth.isscanning():
                            bluetooth.start_scan(scan_time)
                else:
                    id_set.remove(adv.mac)
                    print('Someone might be pretending to be a hive')

        if len(id_set_counter) == len(id_set):
            id_set_counter = set() 
            no_contact_count = 0
            print('All hives are good!')
            hive_contact = True
            bluetooth.stop_scan()
    
    else:
        no_contact_count += 1

        if no_contact_count < max_no_contact:
            print('Could not find all hives. Trying again...')
            bluetooth.start_scan(scan_time)

        else:
            print('some hives are missing')
            no_contact_count = 0
            hive_contact = True