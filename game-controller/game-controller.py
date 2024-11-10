import time
import paho.mqtt.client as mqtt

# MQTT parameters
MQTT_BROKER = "mosquitto"
CLIENT_ID = "light-bulb"
MQTT_PORT = 1883

# Topics
PUB_TOPIC = "test/server"
SUB_TOPIC = "test/prueba"

if __name__ == "__main__":
    try:
        client = mqtt.Client(client_id=CLIENT_ID)
        client.connect(MQTT_BROKER, MQTT_PORT)
        
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print("An unexpected error occurred:", e)
    finally:
        client.disconnect()

