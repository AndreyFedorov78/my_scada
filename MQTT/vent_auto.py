#!/usr/bin/env python
"""Автоматика вентиляции по CO2 (сервис vent_scada, юнит MQTT/vent_scada.service).

Правила (время московское):
  23:30–10:00  — скорость 1;
  10:00–23:00  — CO2 в любой комнате > 900 ppm → скорость 3, у всех < 700 → скорость 1,
                 700–900 — скорость не меняем (гистерезис);
  23:00–23:30  — автоматика ничего не делает.
Учитываются только CO2_SENSORS (Гостиная и спальня). Датчик, не выходивший на связь больше часа, не учитывается.

Команда отправляется только при смене нужной скорости (переход порога, наступление ночи),
поэтому ручное переключение с сайта не перебивается каждую минуту. Если устройство не
подтвердило команду (R-100 не стал нужным), повторяем до MAX_ATTEMPTS раз.
После переключения вентиляция до минуты отдаёт старые значения регистров, поэтому для
подтверждения берём только показания, пришедшие позже STALE_AFTER_SEND после команды.
"""
import sys
import os
import time
import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, "..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_scada.settings")

import django

django.setup()

import pytz
from django.db import connections
from django.utils import timezone
from paho.mqtt import publish
from scada.models import Sensor

VENT_ID = 950559233          # устройство «Вентиляция»
SPEED_PARAM = 'R-100'        # скорость вентилятора 0..3
CO2_PARAM = 'CO'
CO2_SENSORS = [1953992342, 39756490697949184]   # Гостиная, спальня23 (Кабинет Бориса не учитываем)
CO2_HIGH = 900               # выше — скорость 3
CO2_LOW = 700                # ниже — скорость 1
SENSOR_TIMEOUT = datetime.timedelta(hours=1)
NIGHT_SPEED = 1
HIGH_SPEED = 3
LOW_SPEED = 1
BROKER = 'localhost'
LOOP_SECONDS = 60
STALE_AFTER_SEND = datetime.timedelta(seconds=70)   # до этого R-100 может быть старым
RETRY_AFTER = datetime.timedelta(minutes=3)
MAX_ATTEMPTS = 3
MSK = pytz.timezone('Europe/Moscow')


def log(msg):
    print(f"{datetime.datetime.now(MSK):%F %T} {msg}", flush=True)


def decide(t, co2_values):
    """Нужная скорость для времени t (datetime.time, МСК) и свежих показаний CO2.
    None — не менять (гистерезис, окно 23:00–23:30 или нет живых датчиков)."""
    if t >= datetime.time(23, 30) or t < datetime.time(10, 0):
        return NIGHT_SPEED
    if t >= datetime.time(23, 0) or not co2_values:
        return None
    if max(co2_values) > CO2_HIGH:
        return HIGH_SPEED
    if max(co2_values) < CO2_LOW:
        return LOW_SPEED
    return None


def fresh_co2(now):
    """Последнее показание CO2 каждого датчика из CO2_SENSORS, если оно не старше часа."""
    latest = {}
    rows = (Sensor.objects.filter(type__subtitle=CO2_PARAM, sensorId_id__in=CO2_SENSORS,
                                  date__gte=now - SENSOR_TIMEOUT)
            .order_by('-date').values_list('sensorId__title', 'data'))
    for title, data in rows:
        latest.setdefault(title, data)
    return latest


def current_speed(since=None):
    """Последнее значение R-100; с since — только пришедшее не раньше since (иначе None)."""
    rows = Sensor.objects.filter(sensorId_id=VENT_ID, type__subtitle=SPEED_PARAM)
    if since is not None:
        rows = rows.filter(date__gte=since)
    row = rows.order_by('-date').first()
    return row.data if row else None


def send_speed(speed):
    id = VENT_ID % 256
    router = VENT_ID - id
    publish.single(f'my_scadaRX/{router}/{id}/{SPEED_PARAM}', str(speed), hostname=BROKER)


def main():
    target = None        # последняя скорость, которую выставила автоматика
    sent_at = None
    attempts = 0
    confirmed = True
    log("vent_auto запущен")
    while True:
        try:
            now = timezone.now()
            co2 = fresh_co2(now)
            desired = decide(now.astimezone(MSK).time(), list(co2.values()))
            if desired is not None and desired != target:
                log(f"CO2 {co2 or '—'} → скорость {desired} (была цель {target}, факт {current_speed()})")
                send_speed(desired)
                target, sent_at, attempts, confirmed = desired, now, 1, False
            elif not confirmed:
                if current_speed(since=sent_at + STALE_AFTER_SEND) == target:
                    confirmed = True
                    log(f"устройство подтвердило скорость {target}")
                elif now - sent_at >= RETRY_AFTER:
                    if attempts < MAX_ATTEMPTS:
                        attempts += 1
                        log(f"нет подтверждения, повтор {attempts}: скорость {target}")
                        send_speed(target)
                        sent_at = now
                    else:
                        confirmed = True
                        log(f"устройство не подтвердило скорость {target} за {MAX_ATTEMPTS} попытки")
        except Exception as e:
            log(f"Исключение: {e}")
            connections.close_all()
        time.sleep(LOOP_SECONDS)


if __name__ == '__main__':
    main()
