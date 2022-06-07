import datetime, time
import hashlib
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import View
from django.db.models import Q
from django.shortcuts import render
from .models import Sensor, tmp, SensorList, DataTypes, Widget
from .serialalizers import SensorSerializer, SensorDetailSerializer, SensorDataOnlySerializer, tmpSerializer
from .blynk import Blynk
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin


class Index(LoginRequiredMixin, View):
    @staticmethod
    def get(request):
        widgets = Widget.objects.all();
        return render(request, 'scada/index.html', {'widgets': widgets})


class Index2(LoginRequiredMixin, View):
    @staticmethod
    def get(request):
        widgets = Widget.objects.all();
        return render(request, 'scada/index2.html', {'widgets': widgets})

class Clock(View):
    @staticmethod
    def get(request):
        return render(request, 'scada/clock.html')

class OldIpad(LoginRequiredMixin, View):
    @staticmethod
    def get(request):
        alarm_level = 35
        kolodez = SensorList.objects.filter(title='Колодец')[0]
        all_data = Sensor.objects.filter(sensorId=kolodez)[0]
        water = all_data.data
        delta = datetime.datetime.today().timestamp()-all_data.date.timestamp()
        out_sensor = SensorList.objects.filter(title='Улица дача')[0]
        all_data = Sensor.objects.filter(sensorId=out_sensor)
        temperature = (all_data.filter(type__title="Температура")[0].data)/10
        pressure = all_data.filter(type__title="Давление")[0].data
        humidity = all_data.filter(type__title="Влажность")[0].data/10
        hour = datetime.datetime.now().hour
        minute = datetime.datetime.now().minute


        online = (delta < 300)
        data = {
            'alarm' : water < alarm_level,
            'hour': f"{hour:02}",
            'minute': f"{minute:02}",
            'level': int(water/100*350+50),
            'water': water,
            'online': online,
            'temperature' : temperature,
            'pressure' : pressure,
            'humidity' : humidity
        }
        return render(request, 'scada/ipad.html', data)




class Vent(APIView):
    @staticmethod
    def get(request):
        result = Blynk()
        return Response(result.data)

    @staticmethod
    def post(request):
        if request.user.username != 'tester':
            result = Blynk()
            result.put_data(request.data)
            return Response(status=201)
        return Response(status=300)


##class SensorView(LoginRequiredMixin,APIView):
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
        sensor = Sensor.objects.all().order_by('date').filter(sensorId=sensor_id, type=data_type, date__gt=start_date)
        sensor_new = []
        actual_date = timezone.now() - datetime.timedelta(days=days)
        dat = 0
        counter = 0
        for i in sensor:
            if not (i.date.date() == actual_date.date() and i.date.hour == actual_date.hour):
                if counter != 0:
                    sensor_new.append({'date': actual_date, 'data': dat / counter})
                actual_date = i.date
                counter = 0
                dat = 0
            dat += i.data
            counter += 1
        sensor_new.append({'date': actual_date, 'data': dat / counter if counter != 0 else 0})
        return Response(sensor_new)

#class tmpView(LoginRequiredMixin, APIView):
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
        tmp.objects.filter(date__lt=datetime.datetime.now() - datetime.timedelta(seconds=20)).delete()
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
