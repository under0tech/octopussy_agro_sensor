import utime
import network as net

class WiFiW:
    """
    Lightweight Wi-Fi driver for microcontrollers Pi Pico W.

    Provides Wi-Fi network management.
    """

    def __init__(self,
            hostname,
            network,
            password):
        """
        Initialize the Wi-Fi driver.

        :param hostname:
            Hostname to assign to Wi-Fi module.

        :param network:
            Wi-Fi network name (SSID).

        :param password:
            Wi-Fi network password.
        """

        self.hostname = hostname
        self.network = network
        self.password = password

        net.hostname(self.hostname)
        self.wifi = net.WLAN(net.STA_IF)

    def connect(self, timeout=5000) -> bool:
        """
        Connect to a Wi-Fi network.

        :return:
            True if connection is succeed.
            False if any fails.
        """

        self.wifi.active(True)
        self.wifi.connect(self.network, self.password)

        while not self.wifi.isconnected():
            utime.sleep(1)

        start_time = utime.ticks_ms()
        while not self.wifi.isconnected():
            if utime.ticks_diff(utime.ticks_ms(), start_time) > timeout:
                print("[WiFiW] connection timed out!")
                self.wifi.active(False)
                return False

            utime.sleep_ms(1000)

        if self.wifi.status() == 3:
            print("[WiFiW] successfully connected!")
            print("[WiFiW] IP config:", self.wifi.ifconfig())
            return True

        return False

    def reconnect(self, timeout=5000) -> bool:
        """
        Check the current Wi-Fi connection and reconnect if necessary.

        If the WiFi module is already connected to an access point,
        no reconnection is attempted.

        :return:
            True if already connected or reconnection succeeds.
            False if the connection attempt fails.
        """

        if self.wifi.isconnected():
            return True

        return self.connect(timeout)

    def disconnect(self) -> bool:
        """
        Check the current Wi-Fi connection and disconnect if necessary.

        :return:
            True if disconnected.
            False if connected.
        """
                
        if self.wifi.isconnected():
            self.wifi.disconnect()
            self.wifi.active(False)
            print("[WiFiW] successfully disconnected!")
        
        return not self.wifi.isconnected()