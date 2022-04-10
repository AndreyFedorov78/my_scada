import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import View
from django.db.models import Q
from django.shortcuts import render
from .models import Sensor
from .serialalizers import SensorSerializer, SensorDetailSerializer, SensorDataOnlySerializer
from .blynk import Blynk
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin


class Index(LoginRequiredMixin, View):
    @staticmethod
    def get(request):
        # Sensor.objects.all().delete()
        return render(request, 'scada/index.html')


class Vent(APIView):
    @staticmethod
    def get(request):
        result = Blynk()
        return Response(result.data)

    @staticmethod
    def post(request):
        result = Blynk()
        result.put_data(request.data)
        return Response(status=201)


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
                    print('hello', sensor[1],' id', sensor[1].id)
                    sensor[1].delete()

        return Response(status=201)


    @staticmethod
    def delete(request):  # получение данных от датчика и записб в бд
        Sensor.objects.all().delete()
        return Response(status=201)

class SensorDetailView(APIView):
    @staticmethod
    def get(request, pk):
        sensor = Sensor.objects.get(id=pk)
        serializer = SensorDetailSerializer(sensor)
        return Response(serializer.data)


class AllSensors(APIView):
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

