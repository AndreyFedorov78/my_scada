#!/usr/bin/env python
import sys
import os
import django
import syslog


# Получаем абсолютный путь до текущей директории скрипта
current_dir = os.path.dirname(os.path.abspath(__file__))

# Получаем абсолютный путь до корневой директории вашего проекта
project_root = os.path.abspath(os.path.join(current_dir, ".."))  # Поднимаемся на уровень выше

# Добавляем путь к корневой директории в список путей Python
sys.path.append(project_root)

# Устанавливаем переменную окружения DJANGO_SETTINGS_MODULE
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_scada.settings")

# Загружаем настройки Django

django.setup()


from paho.mqtt import client as mqtt_client
from scada.models import SensorList, DataTypes, Sensor, SensorArhive
from scada import current
from django.db import connections
from django.utils import timezone
import random
import time
import datetime

# https://stackoverflow.com/questions/4530069/how-do-i-get-a-value-of-datetime-today-in-python-that-is-timezone-aware

ROOT_TOPIC = "my_scada"

broker = 'tldev.ru'
port = 1883
username = ""
password = ""
topic = ROOT_TOPIC+"/#"
client_id = f'app_T-L_scada-{random.randint(1, 1000)}'


client = None

def connect_mqtt():
    syslog.syslog(f'вызов соединения client_id= {client_id}')
    print(f'вызов соединения client_id= {client_id}')
    def on_connect(client, userdata, flags, rc):
        if rc != 0:
            syslog.syslog("Failed to connect, return code %d\n", rc)
            print("Failed to connect, return code %d\n", rc)
        else:
            syslog.syslog("Connected to MQTT Broker!")
            print("Connected to MQTT Broker!")

    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


# --- Кэш справочников в памяти процесса ------------------------------------------------------
# Датчики и типы почти не меняются: перечитываем их раз в META_TTL секунд (галочки «Включен»
# и «Хранить историю» из админки подхватятся не позже чем через минуту), а не на каждое сообщение.
META_TTL = 60
sensors = {}        # id -> SensorList
data_types = {}     # subtitle -> DataTypes
meta_loaded_at = None    # time.monotonic() последней загрузки


def load_meta():
    global sensors, data_types, meta_loaded_at
    sensors = {s.id: s for s in SensorList.objects.all()}
    types = {}
    for t in DataTypes.objects.order_by('id'):
        types.setdefault(t.subtitle, t)     # в базе бывали дубли subtitle — берём первый
    data_types = types
    meta_loaded_at = time.monotonic()


def get_sensor(sensor_id):
    if meta_loaded_at is None or time.monotonic() - meta_loaded_at > META_TTL:
        load_meta()
    sensor = sensors.get(sensor_id)
    if sensor is None:
        # если датчик не найден, создаем его (выключенным — включают в админке)
        sensor, _ = SensorList.objects.get_or_create(id=sensor_id)
        sensors[sensor_id] = sensor
    return sensor


def get_data_type(subtitle):
    data_type = data_types.get(subtitle)
    if data_type is None:
        data_type = DataTypes.objects.filter(subtitle=subtitle).order_by('id').first()
        if data_type is None:
            data_type = DataTypes.objects.create(subtitle=subtitle, title=subtitle)
        data_types[subtitle] = data_type
    return data_type


# --- Текущие значения — в Redis (scada/current.py), таблица Sensor больше не пишется -------------

def seed_current():
    """Один раз при старте: переносим в Redis последние значения из таблицы Sensor, если в Redis
    их ещё нет (первый запуск после перехода на Redis или Redis потерял данные)."""
    r = current.client()
    for row in Sensor.objects.select_related('type').order_by('-date'):   # свежие первыми, hsetnx оставит их
        if row.type is not None and row.date is not None:
            key = current.KEY.format(row.sensorId_id)
            r.hsetnx(key, row.type.subtitle, f'{row.data}|{row.date.timestamp():.3f}')


# --- Архив: не чаще точки в ARCHIVE_STEP -------------------------------------------------------
# Та же схема, что была: «якорь» (предыдущая точка) + «хвост» (последнее показание). Пока от якоря
# прошло меньше ARCHIVE_STEP, хвост перезаписывается новым показанием; иначе хвост становится
# якорем и добавляется новая точка. Раньше то же делалось INSERT + 10 SELECT + DELETE на сообщение.
ARCHIVE_STEP = datetime.timedelta(minutes=15)
archive_state = {}  # (sensor_id, type_id) -> {'anchor': date|None, 'tail_pk': pk|None, 'tail_date': date|None}


def save_archive(sensor, data_type, value, now):
    key = (sensor.id, data_type.id)
    state = archive_state.get(key)
    if state is None:
        last = list(SensorArhive.objects.filter(sensorId=sensor, type=data_type)
                    .order_by('-date').values_list('pk', 'date')[:2])
        state = {'tail_pk': last[0][0] if last else None,
                 'tail_date': last[0][1] if last else None,
                 'anchor': last[1][1] if len(last) > 1 else None}
        archive_state[key] = state

    if (state['anchor'] is not None and now - state['anchor'] < ARCHIVE_STEP
            and SensorArhive.objects.filter(pk=state['tail_pk']).update(data=value, date=now)):
        state['tail_date'] = now
        return
    record = SensorArhive.objects.create(sensorId=sensor, type=data_type, data=value)
    state['anchor'] = state['tail_date']
    state['tail_pk'], state['tail_date'] = record.pk, now


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        # топик my_scada/<id датчика>/<тип>, в теле целое число
        try:
            value = msg.payload.decode()
        except UnicodeDecodeError:
            return
        parts = msg.topic.split('/')
        if len(parts) < 3 or not parts[1].isdigit() or not value.lstrip('-').isdigit():
            return
        subtitle = parts[2]
        if not subtitle or len(subtitle) > DataTypes._meta.get_field('subtitle').max_length:
            return

        sensor = get_sensor(int(parts[1]))
        if not sensor.active:
            return
        data_type = get_data_type(subtitle)
        value = int(value)
        now = timezone.now()

        current.put(sensor.id, subtitle, value, now)
        if sensor.archive:
            save_archive(sensor, data_type, value, now)
    client.subscribe(topic)
    client.on_message = on_message


def mqtt_start():
    global client  # Declare client as a global variable
    client = connect_mqtt()  # Изменение значения клиента
    seed_current()
    subscribe(client)  # Подписка на MQTT
    client.loop_forever()

while (1):
    syslog.syslog("Перезапуск подписки")
    print("Перезапуск подписки")
    try:
        mqtt_start()
    except KeyboardInterrupt:
        print("Программа прервана пользователем (Ctrl-C).")
        break
    except Exception as e:
        syslog.syslog(f"Исключение: {e}") # {str("e"")}\n{traceback_str}")
        print(f"Исключение: {e}") # {str("e"")}\n{traceback_str}")
        # Сбрасываем соединения Django с БД: после обрыва MySQL (OOM, рестарт)
        # старое соединение остаётся мёртвым и каждая попытка падает с (2013).
        # close_all() заставит Django открыть новое при следующем запросе.
        connections.close_all()
        # Закрываем старый MQTT-клиент, иначе копятся сокеты в CLOSE-WAIT.
        try:
            if client is not None:
                client.disconnect()
        except Exception:
            pass

    time.sleep(10)
