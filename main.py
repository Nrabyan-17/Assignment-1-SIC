import ujson
import network
import utime as time
import dht
from machine import Pin
from umqtt.simple import MQTTClient

# Setup Device yang fungsinya untuk mengatur ID Unik pada perangkat IoT
DEVICE_ID = "wokwi001"

# Setup WiFI untuk menyambungkan perangkat IoT ke Jaringan
WIFI_SSID       = "Wokwi-GUEST"
WIFI_PASSWORD   = ""

# Setup MQTT
MQTT_BROKER             = "broker.mqttdashboard.com" # Alamat broker atau perantara MQTT yang digunakan untuk komunikasi
MQTT_CLIENT             =  DEVICE_ID                 # Nama Klien untuk perangkat IoT
MQTT_TELEMETRY_TOPIC    = "iot/telemetry"            # Topic untuk mengirim data sensor ke Mikrokontroller
MQTT_CONTROL_TOPIC      = "iot/control"              # Topic untuk menerima perintah kontrol

# DHT Sensor Setup
DHT_PIN = Pin(15) # Menginisialisasi sensor DHT (Pin 15) untuk mengukur suhu dan kelembapan

# LED/LAMP Setup
# Untuk mengatur pin output untuk LED Merah, Biru, dan Flash. Pada awalnya, LED dihidupkan (.on()).
RED_LED     = Pin(12, Pin.OUT)
BLUE_LED    = Pin(13, Pin.OUT)
FLASH_LED   = Pin(2, Pin.OUT)
RED_LED.on()
BLUE_LED.on()

# Methods atau Function 
# Fungsinya: Callback ini dipanggil pada saat ada pesan MQTT diterima
def did_recieve_callback(topic, message):
    print('\n\nData Diterima! \ntopic = {0}, message = {1}'.format(topic, message))

    # device_id/lamp/color/state
    # device_id/lamp/state
    # lamp/state
    if topic == MQTT_CONTROL_TOPIC.encode():
        if message == ('{0}/lamp/red/on'.format(DEVICE_ID)).encode():
            RED_LED.on()
        elif message == ('{0}/lamp/red/off'.format(DEVICE_ID)).encode():
            RED_LED.off()
        elif message == ('{0}/lamp/blue/on'.format(DEVICE_ID)).encode():
            BLUE_LED.on()
        elif message == ('{0}/lamp/blue/off'.format(DEVICE_ID)).encode():
            BLUE_LED.off()
        elif message == ('{0}/lamp/on'.format(DEVICE_ID)).encode() or message == b'lamp/on':
            RED_LED.on()
            BLUE_LED.on()
        elif message == ('{0}/lamp/off'.format(DEVICE_ID)).encode() or message == b'lamp/off':
            RED_LED.off()
            BLUE_LED.off()
        elif message == ('{0}/status'.format(DEVICE_ID)).encode() or message == ('status').encode():
            global telemetry_data_old
            mqtt_client_publish(MQTT_TELEMETRY_TOPIC, telemetry_data_old)
        else:
            return
        # Fungsi untuk mengirimkan status LED (Merah/Biru) ke Broker MQTT dalam format JSON
        send_led_status()

# Menghubungkan perangkat ke broker MQTT
def mqtt_connect():
    print("Menyambung ke MQTT broker ...", end="")
    mqtt_client = MQTTClient(MQTT_CLIENT, MQTT_BROKER, user="", password="")
    mqtt_client.set_callback(did_recieve_callback)
    mqtt_client.connect()
    print("Tersambung.")
    mqtt_client.subscribe(MQTT_CONTROL_TOPIC)
    return mqtt_client

# Membuat data suhu dan kelembapan dalam format JSON untuk dikirim ke broker MQTT.
def create_json_data(temperature, humidity):
    data = ujson.dumps({
        "device_id": DEVICE_ID,
        "temp": temperature,
        "humidity": humidity,
        "type": "sensor"
    })
    return data

# Mengirim data ke broker MQTT pada topik tertentu
def mqtt_client_publish(topic, data):
    print("\nMengupdate MQTT Broker...")
    mqtt_client.publish(topic, data)
    print(data)

# Mengirimkan status LED ke Broker MQTT dalam format JSON
def send_led_status():
    data = ujson.dumps({
        "device_id": DEVICE_ID,
        "red_led": "ON" if RED_LED.value() == 1 else "OFF",
        "blue_led": "ON" if BLUE_LED.value() == 1 else "OFF",
        "type": "lamp"
    })
    mqtt_client_publish(MQTT_TELEMETRY_TOPIC, data)


# Logika dari perangkat IoT

# Kegunaan: untuk mengaktifkan koneksi WiFI dan menyambungkan ke jaringan WiFI_SSID
wifi_client = network.WLAN(network.STA_IF)
wifi_client.active(True)
print("Menyambungkan Device ke WiFi")
wifi_client.connect(WIFI_SSID, WIFI_PASSWORD)

# Tunggu sampai WiFi tersambung
while not wifi_client.isconnected():
    print("Menyambung...")
    time.sleep(0.1)
print("WiFi Tersambung!")
print(wifi_client.ifconfig())

# Terhubung ke MQTT
mqtt_client = mqtt_connect()
RED_LED.off()
BLUE_LED.off()
mqtt_client_publish(MQTT_CONTROL_TOPIC, 'lamp/off')
dht_sensor = dht.DHT22(DHT_PIN)
telemetry_data_old = ""

# Loop utama perangkat, dengan tugas: 
# 1. Untuk mengecek pesan baru dari broker MQTT.
# 2. Membaca data suhu dan kelembapan dari sensor DHT22.
# 3. Jika data baru berbeda dari data sebelumnya, maka akan mengirimkan data ke broker.
while True:
    mqtt_client.check_msg()
    print(". ", end="")

    FLASH_LED.on()
        try:
    dht_sensor.measure()
        except:
    pass
    
    time.sleep(0.2)
    FLASH_LED.off()

    telemetry_data_new = create_json_data(dht_sensor.temperature(), dht_sensor.humidity())

    if telemetry_data_new != telemetry_data_old:
        mqtt_client_publish(MQTT_TELEMETRY_TOPIC, telemetry_data_new)
        telemetry_data_old = telemetry_data_new

    time.sleep(0.1)