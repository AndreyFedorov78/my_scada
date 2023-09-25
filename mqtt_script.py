#!/usr/bin/env python
import os
import django

# Установка переменной окружения DJANGO_SETTINGS_MODULE
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_scada.settings")

# Загрузка настроек Django
django.setup()


print("starting")
