from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import View
from django.db.models import Q
from django.shortcuts import render
from .models import Sensor
from .serialalizers import SensorSerializer, SensorDetailSerializer
from .blynk import Blynk

# from django.shortcuts import render
# Create your views here.


class Index (View):
    @staticmethod
    def get(request):
        return render(request, 'scada/index.html')

class Vent (APIView):
    @staticmethod
    def get(request):
        result = Blynk()
        return Response(result.data)

    @staticmethod
    def post(request):
        result = Blynk()
        result.put_data(request.data)
        return  Response(status=201)


class SensorView(APIView):
    @staticmethod
    def get(request):
        sensor = Sensor.objects.all()
        serializer = SensorSerializer(sensor, many=True)
        return Response(serializer.data)

    @staticmethod
    def post(request):
        sensor = SensorDetailSerializer(data=request.data)
        if sensor.is_valid():
            sensor.save()
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
        all_sensors=[];
        sensor = Sensor.objects.all().order_by('-date')
        while len(sensor)>0:
            all_sensors.append(sensor[0])
            sensor_id = sensor[0].sensorId
            dataType = sensor[0].type
            sensor = sensor.exclude(Q(sensorId=sensor_id) & Q(type=dataType))
            serializer = SensorSerializer(all_sensors, many=True)
        return Response(serializer.data)