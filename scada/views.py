import datetime
import hashlib
import time
import pytz
import requests

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import View
from rest_framework.response import Response
from rest_framework.views import APIView
from .blynk import Blynk
from .models import Sensor, tmp, SensorList, DataTypes, Widget, MyWidgets, SensorArhive
from .serialalizers import MyWidgetsSerializer, GetWidgetsListSerializer
from .serialalizers import SensorSerializer, SensorDetailSerializer, tmpSerializer
from new_app import mqtt


def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


class ButtonTest(LoginRequiredMixin, View):
    @staticmethod
    def get(request):
        return render(request, 'scada/bt.html')


class Index(LoginRequiredMixin, View):
    @staticmethod
    def get(request):
        widgets = Widget.objects.all()
        return render(request, 'scada/index.html', {'widgets': widgets})


class Clock(View):
    @staticmethod
    def get(request):
        return render(request, 'scada/clock.html')


class DevManage(APIView):
    @staticmethod
    def get(request):
        # result = Blynk()
        return Response(status=201)

    @staticmethod
    def post(request):
        if request.user.username != 'tester':
            if (type(request.data.get('id', "error")) != int or
                    request.data.get('val', "") == "" or
                    request.data.get('name', "") == ""):
                print("error")
                return Response(status=300)
            id = request.data['id'] % 256
            router = request.data['id'] - id
            val = request.data['val']
            name = request.data['name']
            topic = f'{mqtt.ROOT_TOPIC}RX/{router}/{id}/{name}'
            print(topic)
            mqtt.client.publish(topic, val)
            return Response(status=201)
        return Response(status=300)


# class SensorView(LoginRequiredMixin,APIView):
class SensorView(APIView):
    @staticmethod
    def get(request):
        sensor = Sensor.objects.all()[:200]
        sv_serializer = SensorSerializer(sensor, many=True)
        return Response(sv_serializer.data)

    @staticmethod
    def post(request):  # получение данных от датчика и записб в бд
        sensor = SensorDetailSerializer(data=request.data)
        if sensor.is_valid():
            sensor = sensor.save()
            sensor = Sensor.objects.filter(sensorId=sensor.sensorId).filter(type=sensor.type).order_by('-date')[:3]
            if len(sensor) == 3:
                if sensor[0].date - sensor[2].date < datetime.timedelta(minutes=15):
                    sensor[1].delete()
        return Response(status=201)

    @staticmethod
    def delete(request):
        Sensor.objects.all().delete()
        return Response(status=201)


class SensorDetailView(LoginRequiredMixin, APIView):
    @staticmethod
    def get(request, pk):
        sensor = Sensor.objects.get(id=pk)
        serializer = SensorDetailSerializer(sensor)
        return Response(serializer.data)


class AllSensors(LoginRequiredMixin, APIView):
    @staticmethod
    def get(request):
        all_sensors = []
        sensor = Sensor.objects.all().order_by('-date')
        while len(sensor) > 0:
            all_sensors.append(sensor[0])
            sensor_id = sensor[0].sensorId
            data_type = sensor[0].type
            sensor = sensor.exclude(Q(sensorId=sensor_id) & Q(type=data_type))
        serializer = SensorSerializer(all_sensors, many=True)
        return Response(serializer.data)


class SensorLastDays(APIView):
    @staticmethod
    def get(request, sensor_id, data_type, days):
        start_date = timezone.now() - datetime.timedelta(days=days)
        sensor = SensorArhive.objects.all().order_by('date').filter(sensorId=sensor_id, type=data_type,
                                                                    date__gt=start_date)
        sensor_new = []
        actual_date = timezone.now() - datetime.timedelta(days=days)
        dat = 0
        counter = 0

        for i in sensor:
            sensor_new.append({'date': i.date, 'data': i.data})
        """    if not (i.date.date() == actual_date.date() and i.date.hour == actual_date.hour):
                if counter != 0:
                    sensor_new.append({'date': actual_date, 'data': dat / counter})
                actual_date = i.date
                counter = 0
                dat = 0
            dat += i.data
            counter += 1
        sensor_new.append({'date': actual_date, 'data': dat / counter if counter != 0 else 0})
        """

        return Response(sensor_new)


# class tmpView(LoginRequiredMixin, APIView):
class tmpView(APIView):
    @staticmethod
    def get(request):
        data = tmpSerializer(data=request.data)
        if data.is_valid():
            data.save()
        return Response(status=201)

    @staticmethod
    def post(request):
        # удаляем страрые данные
        tmp.objects.filter(
            date__lt=datetime.datetime.now(pytz.timezone('Europe/Moscow')) - datetime.timedelta(seconds=20)).delete()
        # начинаем обработку
        data = tmpSerializer(data=request.data)
        if data.is_valid():
            if 'data' in data.validated_data:
                hashData = hashlib.md5(data.validated_data['data'].encode()).hexdigest()
                # если строка прилетела в первый раз
                if not tmp.objects.filter(data=hashData).exists():
                    newRecord = tmp()
                    newRecord.data = hashData
                    newRecord.save()
                    data = data.validated_data['data'].split(';')
                    # будем разбирать только строки с четырямя данными
                    if len(data) == 4 and data[0] == "ID":
                        # Если датчик найден обрабатываем данные
                        if SensorList.objects.filter(id=data[1]).exists():
                            sensor = SensorList.objects.get(id=data[1])
                            if sensor.active:
                                if DataTypes.objects.filter(subtitle=data[2]).exists():
                                    datatype = DataTypes.objects.get(subtitle=data[2])
                                else:
                                    datatype = DataTypes()
                                    datatype.subtitle = data[2]
                                    datatype.save()
                                newRecord = Sensor()
                                newRecord.sensorId = sensor
                                newRecord.type = datatype
                                try:
                                    data[3] = int(data[3])
                                    newRecord.data = data[3]
                                    newRecord.save()
                                    # удаляем записи в течение 15 минут после предпоследней
                                    sensor = Sensor.objects.filter(sensorId=newRecord.sensorId).filter(
                                        type=newRecord.type).order_by('-date')[:3]
                                    if len(sensor) == 3:
                                        if sensor[0].date - sensor[2].date < datetime.timedelta(minutes=15):
                                            sensor[1].delete()
                                except:
                                    pass
                        # Если датчик не найденс то здаем его
                        else:
                            sensor = SensorList()
                            sensor.id = data[1]
                            sensor.save()
            return Response(status=201)
        return Response(status=333)


# Работа со списком доступных датчиков конкретного пользователя

class UserWidgets(LoginRequiredMixin, APIView):
    @staticmethod
    def get(request, id=None):
        all_widgets = MyWidgets.objects.filter(userId_id=request.user).order_by('sort')
        serializer = MyWidgetsSerializer(all_widgets, many=True)
        serializer.data[0]['online'] = True
        return Response(serializer.data)

    @staticmethod
    def post(request, id=None):
        if id is None:
            all_widgets = MyWidgets.objects.filter(userId_id=request.user).order_by('sort')
            serializer = MyWidgetsSerializer(all_widgets, many=True)
            for i in serializer.data:
                i['online'] = True
                i['date'] = "--"
                all_sensors = []
                sensor = Sensor.objects.filter(sensorId__id=i['sensor']["id"]).order_by('-date')
                while len(sensor) > 0:
                    all_sensors.append(sensor[0])
                    data_type = sensor[0].type
                    sensor = sensor.exclude(type=data_type)
                i['data'] = SensorSerializer(all_sensors, many=True).data
                i['data'].sort(key=lambda x: x['type']['sort'])
                if len(all_sensors) > 0:
                    now = time.mktime(datetime.datetime.now(pytz.timezone('Europe/Moscow')).timetuple())
                    dat = time.mktime(utc_to_local(all_sensors[0].date).timetuple())
                    if (now - dat) > 600:
                        i['online'] = False
                    if (now - dat) > (24 * 60 * 60):
                        i['date'] = f"{all_sensors[0].date.day}/{all_sensors[0].date.month}/{all_sensors[0].date.year}"
                    else:
                        i['date'] = f"{utc_to_local(all_sensors[0].date).hour}:{all_sensors[0].date.minute}"
            return Response(serializer.data)
        else:  # двигаем виджет
            title = request.data.get('title')
            if title is not None:
                object1 = MyWidgets.objects.get(pk=id)
                object1.title = title
                object1.save()
                return Response(status=201)
            step = request.data.get('step')
            if step is None:
                return Response(status=201)
            object1 = MyWidgets.objects.get(pk=id)
            if 1 == step:
                object2 = MyWidgets.objects.filter(sort__gt=object1.sort).order_by('sort')
            else:
                object2 = MyWidgets.objects.filter(sort__lt=object1.sort).order_by('-sort')
            if len(object2) == 0:
                return Response(status=201)
            object2 = object2[0]
            object1.sort, object2.sort = object2.sort, object1.sort
            object2.save()
            object1.save()

            return Response(status=201)

    @staticmethod
    def delete(request, id):
        MyWidgets.objects.filter(pk=id).delete()
        return Response(status=201)

    # добавление датчика в список
    @staticmethod
    def put(request, id=None):

        user = request.user
        if id is None:
            return Response(status=204)  # если не найден id в запросе
        if len(MyWidgets.objects.filter(userId=user).filter(sensor__id=id)) > 0:
            return Response(status=203)  # если такая запись уже существует
        sensor = SensorList.objects.filter(id=id)
        if len(sensor) == 0:
            return Response(status=203)  # если не существует такого датчика
        # если все нормально создаем новую запись
        sort = 0
        my_list = MyWidgets.objects.filter(userId_id=request.user).order_by('-sort')
        if len(my_list) > 0:
            sort = my_list[0].sort + 1
        sensor = sensor[0]
        widget = MyWidgets()
        widget.userId = user
        widget.sensor = sensor
        widget.title = sensor.title
        widget.sort = sort
        widget.save()
        return Response(status=201)


class GetWidgetsList(LoginRequiredMixin, APIView):
    @staticmethod
    def post(request):
        my_sensors = MyWidgets.objects.filter(userId=request.user).values('sensor')
        new_sensors = SensorList.objects.exclude(id__in=my_sensors).filter(active=True)
        result = GetWidgetsListSerializer(new_sensors, many=True).data
        return Response(result)


class OldIpad(View):
    @staticmethod
    def get(request):
        alarm_level = 35
        kolodez = SensorList.objects.filter(title='Колодец')[0]
        all_data = Sensor.objects.filter(sensorId=kolodez)[0]
        water = all_data.data
        delta = datetime.datetime.today().timestamp() - all_data.date.timestamp()

        pool = SensorList.objects.filter(title='Бассеин')[0]
        all_data = Sensor.objects.filter(sensorId=pool)[0]
        pool = all_data.data / 10

        out_sensor = SensorList.objects.filter(title='Улица дача')[0]
        all_data = Sensor.objects.filter(sensorId=out_sensor)
        temperature = (all_data.filter(type__title="Температура")[0].data) / 10
        pressure = all_data.filter(type__title="Давление")[0].data
        humidity = all_data.filter(type__title="Влажность")[0].data / 10
        hour = datetime.datetime.now(pytz.timezone('Europe/Moscow')).hour
        minute = datetime.datetime.now(pytz.timezone('Europe/Moscow')).minute

        online = (delta < 600)
        data = {
            'alarm': water < alarm_level,
            'pool': pool,
            'hour': f"{hour:02}",
            'minute': f"{minute:02}",
            'level': int(water / 100 * 350 + 50),
            'water': water,
            'online': online,
            'temperature': temperature,
            'pressure': pressure,
            'humidity': humidity
        }
        return render(request, 'scada/ipad2.html', data)


class Connect(LoginRequiredMixin, APIView):
    @staticmethod
    def get(request):
        answer = mqtt.client.is_connected()
        # mqtt.client.enable_logger()
        # subscribe=mqtt.client.
        return Response({'connect': answer})


"""
Спарвочник ответов http :
200 OK («хорошо»)[2][3];
201 Created («создано»)[2][3][4];
202 Accepted («принято»)[2][3];
203 Non-Authoritative Information («информация не авторитетна»)[2][3];
204 No Content («нет содержимого»)[2][3];
205 Reset Content («сбросить содержимое»)[2][3];
206 Partial Content («частичное содержимое»)[2][3];
207 Multi-Status («многостатусный»)[5];
208 Already Reported («уже сообщалось»)[6];
226 IM Used («использовано IM»).
"""
