### GPIO CONFIGURATION
NETWORK_LED_PIN = 18

SHT30S_SDA_PIN = 8
SHT30S_SCL_PIN = 9
SHT30A_SDA_PIN = 4
SHT30A_SCL_PIN = 5
BH1750_SDA_PIN = 26
BH1750_SCL_PIN = 27

SHT30_I2C_PORT = 0
BH1750_I2C_PORT = 1

ADC_PIN = 28
LOW_BATTERY = 3.5 # 3.5V
BATTERY_NEEDS_REPORT = True

### DEVICE
DEVICE_UPDATES_TIMEOUT_MS = 60000 * 120 # 120min (2h)
DEVICE_LIGHTSLEEP_TIMEOUT_MS = 60000 * 30 # 30min, max - 1h

### WIFI
WIFI_CLIENT_HOSTNAME = "OCTOPUSSY-AGENT"
WIFI_NETWORK_NAME = "FARMHOUSE_WIFI_ROUTER_SSID"
WIFI_NETWORK_PASSWORD = "FARMHOUSE_WIFI_ROUTER_PASSWORD"
WIFI_CONNECTION_TIMEOUT = 15000

### Telegram
TELEGRAM_HOST = "api.telegram.org"
TELEGRAM_BOT_ID = "bot0000000000:XXX_xXXXXXXXXXXXXXX-XXXXXXXX" #Your bot token
TELEGRAM_CHAT_ID = "-1001111111112"  # Your Telegram channel ID
TELEGRAM_NEEDS_REPORT = True

### MQTT Home Assistant
MQTT_USER = "mqtt_user"
MQTT_PASSWORD = "mqtt_password"
MQTT_NEEDS_REPORT = True

### Gemini AI
GEMINI_API_KEY = "Your_Gemini_API_KEY_from_Google_AI_Studio"
GEMINI_PROMPT_TEMPLATE = (
    "You are a greenhouse tomato expert. Analyze these five current metrics: "
    "Air Temp: {0}°C, Humidity: {1}%, Light: {2}lx, Soil Moisture: {3}%, Soil Temp: {4}°C. "
    "You must respond in one part output ONLY one of the two following options: "
    "If watering is needed, output exactly: 'needs watering - [Volume]L'. "
    "If watering is not needed, output exactly: 'no watering needed.'"
)
GEMINI_MODEL_NAME = "gemini-3.5-flash-lite"
GEMINI_ENDPOINT_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_NAME}:generateContent"
GEMINI_NEEDS_RESOLUTION = False