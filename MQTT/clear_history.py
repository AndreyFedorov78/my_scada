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
from scada.models import tmp, SensorList, DataTypes, Sensor, SensorArhive
import random
import time
import datetime
import hashlib
import pytz



all = SensorArhive.objects.all()
for item in all:
    item.delete()

