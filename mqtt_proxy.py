import time
import socket
import ujson

from umqtt.simple import MQTTClient

def find_ha_ip():
    """
    Resolves the local IP address of the Home Assistant server using mDNS.

    Loops indefinitely with a 5-second delay until the hostname 
    'homeassistant.local' resolves via network socket address info.

    :return: 
        The resolved IP address string of the Home Assistant server.
    """

    target_host = "homeassistant.local"
    print(f"[MQTT HA] searching for Home Assistant ({target_host})...")

    while True:
        try:
            addr_info = socket.getaddrinfo(target_host, 1883)
            ip = addr_info[0][-1][0]
            print("[MQTT HA] have HA found on IP:", ip)
            return ip
        except:
            print("[MQTT HA] not found yet, retrying in 5 seconds...")
            time.sleep(5)


class OctopussyMQTTProxy:
    """
    Proxy handler for registering and updating an 
    agricultural 'Greenhouse/Octopussy' telemetry device 
    in Home Assistant via MQTT.
    """

    BROKER = "192.168.1.168"
    DISCOVERY_PREFIX = "homeassistant"

    def __init__(self, mqtt_user, mqtt_password, 
                            device_id = '000fd0ad',
                            server_ip = "192.168.1.168"):
        """
        Initialize MQTT network settings, maps sensor metadata structures,
        defines the Home Assistant device profile, and opens a client connection.

        :param mqtt_user: 
            The username credential for the MQTT broker.
        :param mqtt_password: 
            The password credential for the MQTT broker.
        :param device_id: 
            A unique hardware string identifier (e.g., chip MAC fragment).
        :param server_ip: 
            The IP address of the target MQTT broker.
        """

        self.mqtt_user = mqtt_user
        self.mqtt_password = mqtt_password
        self.device_id = "Octopussy_" + device_id
        self.BROKER = server_ip

        self.sensors = {
            "air_temperature": {
                "name": "Air Temperature",
                "topic": "octopussy/sensor/air_temp_c",
                "unit": "°C",
                "device_class": "temperature",
                "icon": "mdi:thermometer"
            },

            "air_humidity": {
                "name": "Air Humidity",
                "topic": "octopussy/sensor/air_humidity_p",
                "unit": "%",
                "device_class": "humidity",
                "icon": "mdi:water-percent"
            },

            "illuminance": {
                "name": "Illuminance",
                "topic": "octopussy/sensor/illuminance_lx",
                "unit": "lx",
                "device_class": "illuminance",
                "icon": "mdi:brightness-5"
            },

            "soil_moisture": {
                "name": "Soil Moisture",
                "topic": "octopussy/sensor/soil_moisture_p",
                "unit": "%",
                "device_class": "moisture",
                "icon": "mdi:water-circle"
            },

            "soil_temperature": {
                "name": "Soil Temperature",
                "topic": "octopussy/sensor/soil_temp_c",
                "unit": "°C",
                "device_class": "temperature",
                "icon": "mdi:thermometer-lines"
            },

            "battery_voltage": {
                "name": "Battery Voltage",
                "topic": "octopussy/sensor/battery_voltage",
                "unit": "V",
                "device_class": "voltage",
                "icon": "mdi:battery"
            }
        }

        self.device = {
            "identifiers": [self.device_id],
            "name": "Octopussy " + device_id,
            "model": "Octopussy",
            "manufacturer": "Greenhouse"
        }

        self.client = MQTTClient(
            client_id=self.device_id.encode(),
            server=self.BROKER,
            user=mqtt_user,
            password=mqtt_password)

        self.client.connect()
        print("[MQTT HA] connected.")


    def update_config(self):
        """
        Publishe Home Assistant MQTT Discovery configuration JSON.

        Loop through all configured sensors and post retained
        JSON profiles to the discovery prefix.
        """

        for sensor_id, sensor in self.sensors.items():
            discovery_topic = (
                f"{self.DISCOVERY_PREFIX}/sensor/"
                f"{self.device_id}_{sensor_id}/config")

            state_topic = (
                f"{sensor['topic']}/"
                f"{self.device_id}/state")

            payload = {
                "name": sensor["name"],
                "state_topic": state_topic,
                "unit_of_measurement": sensor["unit"],
                "device_class": sensor["device_class"],
                "icon": sensor["icon"],
                "unique_id": f"{self.device_id}_{sensor_id}",
                "device": self.device
            }

            self.client.publish(
                discovery_topic,
                ujson.dumps(payload).encode(),
                retain=True)

        print("[MQTT HA] sensors discovery configured.")


    def update_state(self, air_temperature, air_humidity, 
                     illuminance, soil_moisture, soil_temperature, 
                     battery_voltage):
        """
        Publishe the latest environmental sensor data to their unique state topics.

        :param air_temperature: 
            Ambient temperature float.

        :param air_humidity: 
            Ambient relative humidity percentage value.

        :param illuminance: 
            Light level value in Lux.

        :param soil_moisture: 
            Volumetric soil moisture percentage value.

        :param soil_temperature: 
            Sub-surface soil temperature value.

        :param battery_voltage:
            Battery voltage on device.
        """

        values = {
            "air_temperature": air_temperature,
            "air_humidity": air_humidity,
            "illuminance": illuminance,
            "soil_moisture": soil_moisture,
            "soil_temperature": soil_temperature,
            "battery_voltage": battery_voltage
        }

        for sensor_id, value in values.items():
            state_topic = (
                f"{self.sensors[sensor_id]['topic']}/"
                f"{self.device_id}/state")

            self.client.publish(
                state_topic,
                str(value).encode()
            )
            print("[MQTT HA] ", self.sensors[sensor_id]["name"], "=",
                  f'{value}{self.sensors[sensor_id]["unit"]}')

        print("[MQTT HA] sensor states published.")


    def update_event_config(self):
        """
        Publishes the Home Assistant MQTT Discovery configuration
        for the Octopussy event entity.
        """

        payload = {
            "name": "Octopussy Events",
            "state_topic": f"octopussy/event/{self.device_id}/state",
            "event_types": [
                "need_watering",
                "battery_critical"
            ],
            "unique_id": f"{self.device_id}_events",
            "icon": "mdi:alert-circle",
            "device": self.device
        }

        self.client.publish(
            f"homeassistant/event/{self.device_id}_events/config",
            ujson.dumps(payload).encode(),
            retain=True)

        print("[MQTT HA] events discovery configured.")


    def event_battery_critical(self, voltage):
        """
        Publishes a battery critical event.

        :param voltage:
            Current battery voltage.
        """

        payload = {
            "event_type": "battery_critical", 
            "voltage": voltage,
            "message": f"Battery critical ({voltage}v), is going OFFLINE!"}

        self.client.publish(
            f"octopussy/event/{self.device_id}/state",
            ujson.dumps(payload).encode()
        )

        print(f"[MQTT HA] event battery critical ({voltage:.2f}) published.")


    def event_need_watering(self, liters):
        """
        Publishes a watering-needed event.

        :param liters:
            Estimated amount of water required in liters.
        """

        payload = {
            "event_type": "need_watering", 
            "liters": liters,
            "message": f"Needs watering - {liters}L"}

        self.client.publish(
            f"octopussy/event/{self.device_id}/state",
            ujson.dumps(payload).encode()
        )

        print(f"[MQTT HA] event need watering ({liters:.2f}L) published.")


    def disconnect(self):
        """
        Terminates the network socket connection with the MQTT broker.
        """
        
        self.client.disconnect()
        print("[MQTT HA] disconnected.")