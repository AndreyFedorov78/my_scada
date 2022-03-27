import datetime

from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import View
from django.db.models import Q
from django.shortcuts import render
from .models import Sensor
from .serialalizers import SensorSerializer, SensorDetailSerializer, SensorDataOnlySerializer
from .blynk import Blynk
from django.utils import timezone

class Index(View):
    @staticmethod
    def get(request):
        #Sensor.objects.all().delete()
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


class SensorView(APIView):
    @staticmethod
    def get(request):
        sensor = Sensor.objects.all()
        sv_serializer = SensorSerializer(sensor, many=True)
        return Response(sv_serializer.data)

    @staticmethod
    def post(request):
        sensor = SensorDetailSerializer(data=request.data)
        if sensor.is_valid():
            sensor_new = sensor.save()
            


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
        start_date = timezone.now()-datetime.timedelta(days=days)
        sensor = Sensor.objects.all().order_by('date').filter(sensorId=sensor_id, type=data_type, date__gt=start_date)
        sensor_new = []
        actual_date = timezone.now()-datetime.timedelta(days=days)
        dat = 0
        counter = 0
        for i in sensor:
            if not(i.date.date() == actual_date.date() and  i.date.hour == actual_date.hour):
                if counter != 0:
                    sensor_new.append({'date' : actual_date, 'data': dat / counter})
                actual_date = i.date
                counter = 0
                dat = 0

            dat += i.data
            counter += 1
        sensor_new.append({'date': actual_date, 'data': dat / counter if counter != 0 else 0})
        return Response(sensor_new)
