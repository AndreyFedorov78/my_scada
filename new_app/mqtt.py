# Отправка команд устройствам с сайта (DevManage). Приём показаний — MQTT/mqtt_script.py.
import random

from paho.mqtt import client as mqtt_client

ROOT_TOPIC = "my_scada"

broker = 'tldev.ru'
port = 1883
username = ""
password = ""
client_id = f'2023_T-L_scada-{random.randint(1, 1000)}'


def connect_mqtt():
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.connect(broker, port)
    return client
