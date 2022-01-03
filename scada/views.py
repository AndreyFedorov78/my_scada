from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Sensor
from .serialalizers import SensorSerializer, SensorDetailSerializer

# from django.shortcuts import render
# Create your views here.


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
