from paho.mqtt import client as mqtt_client
import random
import time
import datetime
broker = 'fedorov.team'
port = 1883
topic = "#"


#broker = 'localhost'
#port = 9090


client_id = f'python-mqtt-12388'


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    #client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client):
     msg_count = 0
     while True:
         time.sleep(1)
         msg = f"messages: {msg_count}"
         result = client.publish(topic, msg)
         # result: [0, 1]
         status = result[0]
         if status == 0:
             print(f"Send --{msg}-- to topic --{topic}--")
         else:
             print(f"Failed to send message to topic {topic}")
         msg_count += 1

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        try:
           print(f" {datetime.datetime.now().strftime('%H:%M')} Received --{msg.payload.decode()}-- from --{msg.topic}-- topic")
        except:
            pass

    client.subscribe(topic)
    client.on_message = on_message


client = connect_mqtt()
subscribe(client)
client.loop_forever()
