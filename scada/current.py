"""Текущие показания датчиков в Redis (вместо таблицы Sensor).

На каждый датчик — хэш  scada:cur:<id датчика>,  поле — subtitle типа ("T", "CO", "R-100"),
значение — "<число>|<unix-время>".  Пишет MQTT/mqtt_script.py, читают API и MQTT/vent_auto.py.
"""
import datetime

import redis
from django.conf import settings
from rest_framework import serializers

from .models import SensorList, DataTypes

KEY = 'scada:cur:{}'

_client = None


def client():
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True,
                                       socket_timeout=3, socket_connect_timeout=3)
    return _client


def _key(sensor_id):
    return KEY.format(sensor_id)


def parse(raw):
    value, ts = raw.split('|')
    return int(value), datetime.datetime.fromtimestamp(float(ts), tz=datetime.timezone.utc)


def put(sensor_id, subtitle, value, date):
    client().hset(_key(sensor_id), subtitle, f'{value}|{date.timestamp():.3f}')


def get(sensor_id, subtitle):
    """(значение, datetime UTC) или None."""
    raw = client().hget(_key(sensor_id), subtitle)
    return parse(raw) if raw else None


def get_many(sensor_ids):
    """{id датчика: {subtitle: (значение, datetime UTC)}} за один запрос к Redis."""
    sensor_ids = list(sensor_ids)
    pipe = client().pipeline(transaction=False)
    for sensor_id in sensor_ids:
        pipe.hgetall(_key(sensor_id))
    return {sensor_id: {subtitle: parse(raw) for subtitle, raw in fields.items()}
            for sensor_id, fields in zip(sensor_ids, pipe.execute())}


# --- Выдача в API в прежнем формате SensorSerializer (sensorId, type, data, date) ----------------

class _SensorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorList
        fields = ('id', 'title', 'sort', 'active', 'widget', 'date', 'archive')


class _DataTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataTypes
        fields = '__all__'


_date_field = serializers.DateTimeField()


def data_types_by_subtitle():
    types = {}
    for t in DataTypes.objects.order_by('id'):
        types.setdefault(t.subtitle, t)
    return types


def readings(sensors, types=None, values=None):
    """Список показаний [{sensorId, type, data, date}, ...] для датчиков (SensorList),
    свежие первыми. types — {subtitle: DataTypes}, values — результат get_many(),
    если они уже прочитаны."""
    sensors = list(sensors)
    if types is None:
        types = data_types_by_subtitle()
    if values is None:
        values = get_many(s.id for s in sensors)
    result = []
    for sensor in sensors:
        sensor_data = _SensorListSerializer(sensor).data
        for subtitle, (value, date) in values[sensor.id].items():
            data_type = types.get(subtitle)
            result.append({
                'sensorId': sensor_data,
                'type': _DataTypesSerializer(data_type).data if data_type else None,
                'data': value,
                'date': date,
            })
    result.sort(key=lambda r: r['date'], reverse=True)
    for r in result:
        r['date'] = _date_field.to_representation(r['date'])
    return result
