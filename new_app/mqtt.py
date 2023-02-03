from paho.mqtt import client as mqtt_client
from scada.models import tmp, SensorList, DataTypes, Sensor, SensorArhive
import random
import time
import datetime
import hashlib
import pytz

# https://stackoverflow.com/questions/4530069/how-do-i-get-a-value-of-datetime-today-in-python-that-is-timezone-aware

ROOT_TOPIC = "my_scada"

broker = 'fedorov.team'
port = 1883
username = "myscada"
password = "12345678"
topic = ROOT_TOPIC+"/#"
client_id = f'T-L_scada-{random.randint(1, 1000)}'


# print("id=", client_id)


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc != 0:
            print("Failed to connect, return code %d\n", rc)
        else:
            print("Connected to MQTT Broker!")

    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        try:
            msg_body = msg.payload.decode()
        except:
            return
        #print (msg.topic,"   ",msg_body)
        data = msg.topic.split('/')
        data.append(msg.payload.decode())  ##!!!!
        if len(data) < 4:
            return
        if not data[1].isdigit():
            return
        if not data[3].lstrip('-').isdigit():
            return

        if not SensorList.objects.filter(id=data[1]).exists():
            # если датчик не найден, создаем его.
            sensor = SensorList()
            sensor.id = data[1]
            sensor.save()
        sensor = SensorList.objects.get(id=data[1])
        if not sensor.active:
            return
        if not DataTypes.objects.filter(subtitle=data[2]).exists():
            datatype = DataTypes()
            datatype.subtitle = data[2]
            datatype.save()
        datatype = DataTypes.objects.get(subtitle=data[2])
        newRecord = Sensor()
        arhive = SensorArhive()
        arhive.sensorId = newRecord.sensorId = sensor
        arhive.type = newRecord.type = datatype
        data[3] = int(data[3])
        arhive.data =  newRecord.data = data[3]
        arhive.save()
        newRecord.save()
        sensor = Sensor.objects.filter(sensorId=newRecord.sensorId).filter(
                type=newRecord.type).exclude(pk=newRecord.pk)[1:]

        for item in sensor:
            item.delete()


        for x in range(0, 10):  # данные могут поступать одновременно, надо качественно подчистить
            sensor = SensorArhive.objects.filter(sensorId=newRecord.sensorId).filter(
                type=newRecord.type).order_by('-date')[:3]
            if len(sensor) == 3:
                if sensor[0].date - sensor[2].date < datetime.timedelta(minutes=15):
                    sensor[1].delete()

    #  except:
    #      pass

    client.subscribe(topic)
    client.on_message = on_message





client = connect_mqtt()
subscribe(client)
# client.loop_forever()

"""
def publish(client):
     msg_count = 0
     while True:
         time.sleep(1)
         msg = f"messages: {msg_count}"
         result = client.publish(topic, msg)
         # result: [0, 1]
         status = result[0]
         if status == 0:
            // print(f"Send `{msg}` to topic `{topic}`")
         else:
             pass
            // print(f"Failed to send message to topic {topic}")
         msg_count += 1
"""
