import re
import utime
import ubinascii

import definitions as vars

from wifiw import WiFiW
from telegaw import TelegaW
from googla import GooglA
from sensors import get_sensors_data
from mqtt_proxy import OctopussyMQTTProxy, find_ha_ip
from machine import Pin, ADC, deepsleep, lightsleep

# -------------------------
# Configuration
# -------------------------
led = Pin(vars.NETWORK_LED_PIN, Pin.OUT)
battery_adc = ADC(Pin(vars.ADC_PIN))

# -------------------------
# WiFi
# -------------------------
wifi_client = WiFiW(hostname=vars.WIFI_CLIENT_HOSTNAME,
                    network=vars.WIFI_NETWORK_NAME,
                    password=vars.WIFI_NETWORK_PASSWORD)

# -------------------------
# Telega
# -------------------------
telegaw_client = TelegaW(
    telegram_host=vars.TELEGRAM_HOST,
    telegram_bot_id=vars.TELEGRAM_BOT_ID,
    telegram_chat_id=vars.TELEGRAM_CHAT_ID)

# -------------------------
# GooglA
# -------------------------
googla_client = GooglA(
    api_key=vars.GEMINI_API_KEY, 
    api_url=vars.GEMINI_ENDPOINT_URL)

# -------------------------
# Light signals
# -------------------------
signal_init = [
    (1, 0.15), (0, 0.15),
    (1, 0.15), (0, 0.15),
    (1, 0.15), (0, 0.15),
    (1, 3), (0, 0.21)
]

signal_wifi_connect = [
    (1, 0.7), (0, 0.2),
    (1, 0.18), (0, 0.2),
    (1, 0.18)
]

signal_wifi_reconect = [
    (1, 0.5), (0, 0.5),
    (1, 0.5), (0, 0.5),
    (1, 0.5), (0, 0.5),
    (1, 0.5), (0, 0.5),
    (1, 0.5), (0, 0.5),
]

signal_telega_start_sending = [
    (1, 0.18), (0, 0.7), (1, 0.5)
]

signal_telega_end_sending = [
    (0, 0.21), (1, 0.4), (0, 0.23), 
    (1, 0.18), (0, 0.21)
]

signal_ha_start_sending = [
    (1, 1), (0, 0.4), (1, 0.6)
]

signal_ha_end_sending = [
    (0, 0.21), (1, 1), (0, 0.4),
    (1, 0.6), (0, 0.21)
]

signal_deepsleep = [
    (0, 0.21), (1, 3), (0, 0.8),
    (1, 1.6), (0, 0.9), (1, 1.6), (0, 0.9),
    (1, 1.4), (0, 0.7), (1, 1.3), (0, 0.5)
]

def light_led(value, duration):
    led.value(value)
    utime.sleep(duration)
    utime.sleep(0.03)

def light_signal(signal):
    for value, duration in signal:
        light_led(value, duration)

# -------------------------
# Battery
# -------------------------
def battery_check():
    global need_shutdown
    global battery_voltage

    raw = battery_adc.read_u16()
    voltage = raw * 5.7 * 3.2 / 65535

    battery_voltage = voltage
    adc_str = f"Voltage: {voltage:.2f}v"
    print(adc_str)

    if voltage < vars.LOW_BATTERY:
        print("Low battery")
        need_shutdown = True

    return adc_str

# -------------------------
# shutdown
# -------------------------
def shutdown():
    print('>shutdown!')
    led.on()
    light_signal(signal_deepsleep)
    led.off()
    utime.sleep(1)
    deepsleep()

# -------------------------
# Init
# -------------------------
light_signal(signal_init)

led.off()

air_temperature = 0
air_humidity = 0
illuminance = 0
soil_moisture = 0
soil_temperature = 0
battery_voltage = 0

# -------------------------
# Main loop
# -------------------------
update_last_time = (utime.ticks_ms() - 
                      vars.DEVICE_UPDATES_TIMEOUT_MS)

ha_ip = None
device_id = None
adc_str = None

need_shutdown = False

while True:
    print('...')
    led.off()

    if need_shutdown:
        shutdown()
    adc_str = battery_check()

    utime.sleep(2)
    if device_id is not None:
        sleep_ms = int(vars.DEVICE_LIGHTSLEEP_TIMEOUT_MS)
        print(f'[LightsleeP]: Waiting for {sleep_ms} ms - {wifi_client.disconnect()}')
        utime.sleep(1)
        lightsleep(sleep_ms)

    try:
        if need_shutdown or utime.ticks_diff(
            utime.ticks_ms(), update_last_time) >= vars.DEVICE_UPDATES_TIMEOUT_MS:
            if wifi_client.reconnect(vars.WIFI_CONNECTION_TIMEOUT):  

                # Mac-address (decoded)
                if not device_id:    
                    mac_str = ubinascii.hexlify(wifi_client.wifi.config('mac')).decode()
                    device_id = f"{mac_str}"
                    print(f'MAC-address (decoded): {device_id}\n')  

                # Gets sensors data 
                (air_temperature, air_humidity,
                    illuminance, soil_temperature, soil_moisture) = get_sensors_data()

                ai_response = None
                if vars.GEMINI_NEEDS_RESOLUTION:
                    try:
                        ai_prompt = vars.GEMINI_PROMPT_TEMPLATE.format(air_temperature,
                                                                       air_humidity,
                                                                       illuminance,
                                                                       soil_moisture,
                                                                       soil_temperature)
                        ai_response = googla_client.ask_gemini(prompt=ai_prompt)
                        print("[GEMINI] response: ", ai_response)
                    except:
                        pass

                # Sending telega and HA
                if vars.TELEGRAM_NEEDS_REPORT:
                    message = (
                                f"*[OCTOPUSSY {device_id}]*: "
                                f"🌡️ air temperature - {air_temperature:.2f}°C, "
                                f"💧 air humidity - {air_humidity:.2f}%, "
                                f"☀️ illuminance - {illuminance:.0f} lx, "
                                f"🪴 soil moisture - {soil_moisture:.2f}%, "
                                f"🌡️ soil temperature - {soil_temperature:.2f}°C"
                            )

                    light_signal(signal_telega_start_sending)
                    telegaw_client.send_message(message)
                    
                    if ai_response is not None:
                       utime.sleep(1)
                       telegaw_client.send_message(f"*[GEMINI {device_id}]*: {ai_response}") 

                    if adc_str is not None and vars.BATTERY_NEEDS_REPORT:
                        utime.sleep(2)
                        adc_msg = f'*[BatterY {device_id}]*: {adc_str}'
                        if need_shutdown:
                            adc_msg += ', *[ATTENTION - device is going OFFLINE]*.'
                        telegaw_client.send_message(adc_msg)

                    light_signal(signal_telega_end_sending)

                if vars.MQTT_NEEDS_REPORT:
                    try:
                        # Searching for Home Assistant IP
                        if not ha_ip:
                            ha_ip = find_ha_ip()
                            print(f'[MQTT HA] Home Assistant actual IP: {ha_ip}')

                        light_signal(signal_ha_start_sending)
                        mqtt = OctopussyMQTTProxy(
                            mqtt_user=vars.MQTT_USER,
                            mqtt_password=vars.MQTT_PASSWORD,
                            device_id=device_id,
                            server_ip=ha_ip)

                        mqtt.update_config()
                        mqtt.update_event_config()

                        mqtt.update_state(
                            air_temperature=round(air_temperature, 2),
                            air_humidity=round(air_humidity,2),
                            illuminance=int(illuminance),
                            soil_moisture=round(soil_moisture, 2),
                            soil_temperature=round(soil_temperature, 2),
                            battery_voltage=round(battery_voltage, 2))

                        if need_shutdown and vars.BATTERY_NEEDS_REPORT:
                            mqtt.event_battery_critical(voltage=round(battery_voltage, 2))

                        if ai_response is not None:
                            match = re.search(r'(\d+(?:\.\d+)?)\s*L', ai_response)
                            liters = float(match.group(1)) if match else 0
                            if liters > 0:
                                mqtt.event_need_watering(liters=round(liters, 2))

                        mqtt.disconnect()
                        light_signal(signal_ha_end_sending)

                    except Exception as mqe:
                        print("[MQTT HA] error:", [mqe])
                        pass
                
                update_last_time = utime.ticks_ms()
            else:
                light_signal(signal_wifi_reconect)
                print('[WifiW] is not connected')
                pass
    except RuntimeError as ex:
        print(ex)





