import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    #print(msg.topic, "   ", msg.payload.decode())
    if msg.retain:
        try:
            print(msg.topic, "   ", msg.payload.decode())
        except:
            print(msg.topic, "   ")
        print("This message has the retain flag set")

client = mqtt.Client()
client.on_message = on_message

client.connect("tldev.ru", 1883)
client.subscribe("#")

client.loop_forever()