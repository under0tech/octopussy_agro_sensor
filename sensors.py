import gc
import time

import definitions as vars

from machine import I2C, Pin

def read_sht30_data(i2c, addr, commands=[]):
    for cmd in commands:
        i2c.writeto(addr, cmd)

    time.sleep_ms(100)

    data = i2c.readfrom(addr, 6)     
    if len(data) == 6:
        temp_raw = data[0] << 8 | data[1]
        hum_raw = data[3] << 8 | data[4]
        
        temperature = -45 + (175 * temp_raw / 65535)
        humidity = 100 * hum_raw / 65535
        
        return (temperature, humidity)
    else:
        print("[BH1750] SHT30 Error: Invalid response length.")
        return None

def read_bh1750_data(i2c, addr, commands=[]):
    for cmd in commands:
        i2c.writeto(addr, cmd)

    time.sleep_ms(200)

    data = i2c.readfrom(addr, 2)

    if len(data) == 2:
        raw_lux = (data[0] << 8) | data[1]
        lux = raw_lux / 1.2
        return lux
    else:
        print("[SensorS] BH1750 Error: Incomplete data packet received.")
        return None

sensors = [
    {
        "name": "SHT30S",
        "scl": vars.SHT30S_SCL_PIN,
        "sda": vars.SHT30S_SDA_PIN,
        "i2c_port": vars.SHT30_I2C_PORT,
        "addr": 0x44,
        "cmd": [b'\x2C\x10'],
        "read_func": read_sht30_data
    },
    {
        "name": "SHT30A",
        "scl": vars.SHT30A_SCL_PIN,
        "sda": vars.SHT30A_SDA_PIN,
        "i2c_port": vars.SHT30_I2C_PORT,
        "addr": 0x44,
        "cmd": [b'\x2C\x10'],
        "read_func": read_sht30_data
    },
    {
        "name": "BH1750",
        "scl": vars.BH1750_SCL_PIN,
        "sda": vars.BH1750_SDA_PIN,
        "i2c_port": vars.BH1750_I2C_PORT,
        "addr": 0x23,
        "cmd": [b'\x01', b'\x20'],
        "read_func": read_bh1750_data
    }
]

def get_sensors_data():

    air_temperature = 0
    air_humidity = 0
    illuminance = 0
    soil_moisture = 0
    soil_temperature = 0

    for sensor in sensors:
        i2c = None
        gc.collect()
        time.sleep_ms(2000)

        try:
            i2c = I2C(sensor["i2c_port"], scl=Pin(sensor["scl"]), sda=Pin(sensor["sda"]), freq=100000)

            res = sensor["read_func"](i2c, sensor["addr"], sensor["cmd"])
            if res is not None:
                if sensor["name"] == "SHT30S":
                    print(f"[SensorS] Soil Temperature: {res[0]:.2f}°C | Soil Moisture: {res[1]:.2f}%")
                    soil_temperature, soil_moisture = res
                elif sensor["name"] == "SHT30A":
                    print(f"[SensorS] Air Temperature: {res[0]:.2f}°C | Air Humidity: {res[1]:.2f}%")
                    air_temperature, air_humidity = res
                elif sensor["name"] == "BH1750":
                    print(f"[SensorS] Light Intensity: {res:.0f} lx")
                    illuminance = res
            
        except Exception as e:
            print(f"[SensorS] Error reading {sensor['name']}: {e}")

    return (air_temperature, air_humidity,
            illuminance, soil_temperature, soil_moisture)


