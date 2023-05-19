import pycom
from network import Bluetooth
import machine
import time
from network import WLAN

nr_of_hives = 1
id_set = set()
id_set_counter = set()

wait_time = 10
adv_time = 2
scan_time = 5

hive_contact = False
no_contact_count = 0
max_no_contact = 5

pycom.heartbeat(False)
bluetooth = Bluetooth()
pycom.rgbled(0x550000)  # Red

rtc = machine.RTC()

def connection_callback (bt_o):
    events = bt_o.events()   # this method returns the flags and clears the internal registry

    if events & Bluetooth.CLIENT_CONNECTED:
        pycom.rgbled(0x005500)  # green

    elif events & Bluetooth.CLIENT_DISCONNECTED:
        pycom.rgbled(0x550000)  # Red

def log_event(event_description, event_time):
    year, month, day, hour, minute, second, _, _ = event_time
    time_stamp = '[{year}/{month}/{day}|{hour}:{minute}:{second}]'.format(year = year, month = month, day = day, hour = hour, minute = minute, second = second)
    log = open('log.txt', 'a')
    log.write('{time_stamp} {event_description}\n'.format(time_stamp = time_stamp, event_description = event_description))
    log.close()
    print('{time_stamp} {event_description}'.format(time_stamp = time_stamp, event_description = event_description))

log_event('Rebooted', time.localtime())



log_event('Connecting to wifi', time.localtime())

wlan = WLAN(mode = WLAN.STA)
wlan.connect(ssid = 'bee_fi', auth = (WLAN.WPA2, 'beesarecool'))
while not wlan.isconnected():
    machine.idle()
log_event('wifi connected!', time.localtime())

rtc.ntp_sync('pool.ntp.org')

bluetooth.callback(trigger=Bluetooth.CLIENT_CONNECTED | Bluetooth.CLIENT_DISCONNECTED, handler=connection_callback)
bluetooth.start_scan(-1)
log_event('Locating {nr_of_hives} hives'.format(nr_of_hives = nr_of_hives), time.localtime())
while len(id_set) < nr_of_hives:
    adv = bluetooth.get_adv()

    if adv:

        if bluetooth.resolve_adv_data(adv.data, bluetooth.ADV_NAME_CMPL) == 'bee_hive':
            log_event('foud hive! mac: {mac}'.format(mac = adv.mac), time.localtime())
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
                    log_event('connecting to mac: {mac}'.format(mac = adv.mac), time.localtime())

                    try:
                        connection = bluetooth.connect(adv.mac)
                        id_set_counter.add(adv.mac)

                    except:
                        log_event('Error while connecting to the bluetooth device or reading data.', time.localtime())
                    if connection:
                        connection.disconnect()
                        if not bluetooth.isscanning():
                            bluetooth.start_scan(scan_time)
                else:
                    id_set.remove(adv.mac)
                    log_event('Someone might be pretending to be a hive', time.localtime())

        if len(id_set_counter) == len(id_set):
            id_set_counter = set() 
            no_contact_count = 0
            log_event('All hives are good!', time.localtime())

            hive_contact = True
            bluetooth.stop_scan()
    
    else:
        no_contact_count += 1

        if no_contact_count < max_no_contact:
            log_event('Could not find all hives. Trying again...', time.localtime())
            bluetooth.start_scan(scan_time)

        else:
            log_event('some hives are missing', time.localtime())
            no_contact_count = 0
            hive_contact = True