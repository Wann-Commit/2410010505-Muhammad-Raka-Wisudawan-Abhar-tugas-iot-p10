"""
Penugasan Individu Materi 10
Simulasi ESP32 dengan Python:
1. Kirim suhu (simulasi DHT22) setiap 3 detik
2. Terima perintah relay "ON"/"OFF" -> GPIO 26
3. Terima nilai PWM 0-255 -> LED GPIO 2
"""
import time
import random
import threading
import paho.mqtt.client as mqtt

# ================= KONFIGURASI =================
NIM = "2410010505"

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_CLIENT_ID = f"PythonDevice-{NIM}"

TOPIC_SUHU = f"iot/{NIM}/sensor/suhu"
TOPIC_RELAY = f"iot/{NIM}/aktuator/relay"
TOPIC_PWM = f"iot/{NIM}/aktuator/pwm"
TOPIC_STATUS_RELAY = f"iot/{NIM}/status/relay"   # feedback
TOPIC_STATUS_PWM = f"iot/{NIM}/status/pwm"       # feedback

PIN_RELAY = 26      # GPIO relay (simulasi)
PIN_LED_PWM = 2     # GPIO LED PWM (simulasi)
INTERVAL_PUBLISH = 3  # detik

# ================= STATE GLOBAL =================
relay_state = "OFF"
pwm_value = 0


# ================= CALLBACK MQTT =================
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("[MQTT] Terhubung ke broker")
        client.subscribe(TOPIC_RELAY, qos=0)
        client.subscribe(TOPIC_PWM, qos=0)
        print(f"[MQTT] Subscribe: {TOPIC_RELAY}")
        print(f"[MQTT] Subscribe: {TOPIC_PWM}")
    else:
        print(f"[MQTT] Gagal terhubung, kode: {reason_code}")


def on_message(client, userdata, msg):
    global relay_state, pwm_value
    payload = msg.payload.decode("utf-8").strip()
    print(f"[MQTT] Pesan masuk [{msg.topic}]: {payload}")

    # ---------- KONTROL RELAY (GPIO 26) ----------
    if msg.topic == TOPIC_RELAY:
        if payload in ("ON", "1"):
            relay_state = "ON"
            print(f"[AKTUATOR] Relay GPIO {PIN_RELAY} -> HIGH (MENYALA)")
        elif payload in ("OFF", "0"):
            relay_state = "OFF"
            print(f"[AKTUATOR] Relay GPIO {PIN_RELAY} -> LOW (MATI)")
        else:
            print(f"[AKTUATOR] Perintah relay tidak dikenal: {payload}")
            return
        client.publish(TOPIC_STATUS_RELAY, relay_state, qos=0)

    # ---------- KONTROL PWM (GPIO 2) ----------
    elif msg.topic == TOPIC_PWM:
        try:
            nilai = int(float(payload))
        except ValueError:
            print(f"[AKTUATOR] Nilai PWM tidak valid: {payload}")
            return
        if nilai < 0 or nilai > 255:
            print(f"[AKTUATOR] Nilai PWM di luar 0-255: {nilai}")
            return
        pwm_value = nilai
        persen = round(nilai / 255 * 100)
        bar = "#" * (persen // 5)
        print(f"[AKTUATOR] LED GPIO {PIN_LED_PWM} PWM = {nilai} ({persen}%) [{bar:<20}]")
        client.publish(TOPIC_STATUS_PWM, str(pwm_value), qos=0)


def on_disconnect(client, userdata, flags, reason_code, properties=None):
    print(f"[MQTT] Terputus (kode: {reason_code}). Mencoba reconnect...")


# ================= PEMBACAAN SENSOR =================
def baca_suhu():
    """Simulasi DHT22: suhu acak sekitar 27 derajat C."""
    base = 27.0
    noise = random.uniform(-1.5, 1.5)
    return round(base + noise, 2)


# ================= THREAD PUBLISH SENSOR =================
def publish_loop(client):
    while True:
        try:
            suhu = baca_suhu()
            if suhu is not None:
                client.publish(TOPIC_SUHU, str(suhu), qos=0)
                print(f"[SENSOR] Publish suhu: {TOPIC_SUHU} -> {suhu} °C")
        except Exception as e:
            print(f"[SENSOR] Error: {e}")
        time.sleep(INTERVAL_PUBLISH)


# ================= MAIN =================
def main():
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=MQTT_CLIENT_ID,
        protocol=mqtt.MQTTv311,
    )
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    print(f"[MQTT] Menghubungkan ke {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    time.sleep(1)

    publisher = threading.Thread(target=publish_loop, args=(client,), daemon=True)
    publisher.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MAIN] Menghentikan program...")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()