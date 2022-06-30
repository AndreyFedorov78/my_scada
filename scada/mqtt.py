from paho.mqtt import client as mqtt_client
from .models import tmp, SensorList, DataTypes, Sensor
import random
import time
import datetime
import hashlib
import pytz

# https://stackoverflow.com/questions/4530069/how-do-i-get-a-value-of-datetime-today-in-python-that-is-timezone-aware


broker = 'fedorov.team'
port = 1883
topic = "my_scada/#"
client_id = f'T-L_scada-{random.randint(1, 1000)}'


# print("id=", client_id)


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc != 0:
            pass
            print("Failed to connect, return code %d\n", rc)
        else:
            pass
            print("Connected to MQTT Broker!")

    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
       # try:
            for i in msg.payload:
                if not (ord("0") <= i <= ord("9")):
                    return
            data = msg.topic.split('/')
            data.append(msg.payload.decode())  ##!!!!
            if len(data) < 4:
                return
            if not data[1].isdigit():
                return
            if not data[3].isdigit():
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
            newRecord.sensorId = sensor
            newRecord.type = datatype
            data[3] = int(data[3])
            newRecord.data = data[3]
            newRecord.save()
            # удаляем записи в течение 15 минут после предпоследней
            for x in range(0, 10):  # данные могут поступать одновременно, надо качественно подчистить
                sensor = Sensor.objects.filter(sensorId=newRecord.sensorId).filter(
                    type=newRecord.type).order_by('-date')[:3]
                if len(sensor) == 3:
                    if sensor[0].date - sensor[2].date < datetime.timedelta(minutes=15):
                        sensor[1].delete()
      #  except:
      #      pass

    # print("сообщение обработано")

    client.subscribe(topic)
    client.on_message = on_message

print('\n\nMQTT\n\n')
client = connect_mqtt()
subscribe(client)

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
