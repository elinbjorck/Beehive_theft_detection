import pycom
from network import Bluetooth
import time
import machine
from network import WLAN

pycom.heartbeat(False)

wait_time = None
guard_contact = False
advertising = False

bluetooth = Bluetooth()
rtc = machine.RTC()

def connection_callback (bt_o):
    global guard_contact
    events = bt_o.events()   # this method returns the flags and clears the internal registry
    if events & Bluetooth.CLIENT_DISCONNECTED:
        guard_contact = True


def log_event(event_description, event_time):
    year, month, day, hour, minute, second, _, _ = event_time
    time_stamp = '[{year}/{month}/{day}|{hour}:{minute}:{second}]'.format(year = year, month = month, day = day, hour = hour, minute = minute, second = second)
    log = open('log.txt', 'a')
    log.write('{time_stamp}\t{event_description}\n'.format(time_stamp = time_stamp, event_description = event_description))
    log.close()
    print('{time_stamp}\t{event_description}'.format(time_stamp = time_stamp, event_description = event_description))

log_event('Rebooted', time.localtime())

log_event('Connecting to wifi', time.localtime())

wlan = WLAN(mode = WLAN.STA)
wlan.connect(ssid = 'bee_fi', auth = (WLAN.WPA2, 'beesarecool'))
while not wlan.isconnected():
    machine.idle()
log_event('wifi connected!', time.localtime())

rtc.ntp_sync('pool.ntp.org')

# alive_message = bluetooth.service(b'0000000000000000')
# alive_message.characteristic(uuid = '0000000000000001', value = b'Im OK')
while True:

    if guard_contact:
        bluetooth.advertise(False)
        advertising = False
        bluetooth.start_scan(5)
        guard_contact = False

    elif bluetooth.isscanning():
        log_event('scanning for timing from guard', time.localtime())
        adv = bluetooth.get_adv()

        if adv:

            if bluetooth.resolve_adv_data(adv.data, bluetooth.ADV_NAME_CMPL) == 'guard_bee':
                wait_time = int.from_bytes(bluetooth.resolve_adv_data(adv.data, bluetooth.ADV_SERVICE_DATA), 'big')
                log_event('Advertising again in {wait_time} sec.'.format(wait_time = wait_time), time.localtime())
                bluetooth.stop_scan()

    elif wait_time:
        log_event('going to sleep', time.localtime())
        machine.sleep(wait_time * 1000)
        log_event('woke up!', time.localtime())
        wait_time = None

    elif not advertising:
        bluetooth = Bluetooth()
        bluetooth.callback(trigger=Bluetooth.CLIENT_CONNECTED | Bluetooth.CLIENT_DISCONNECTED, handler=connection_callback)
        
        log_event('advertising!', time.localtime())

        bluetooth.set_advertisement(name = "bee_hive", manufacturer_data = "fipy")
        bluetooth.advertise(True)
        advertising = True
