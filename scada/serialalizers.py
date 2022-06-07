from rest_framework import serializers
from .models import Sensor, tmp


class SensorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sensor
        depth = 3
        fields = "__all__"
       # fields = ("sensorId", "type", "data", "date")


class SensorDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sensor
        depth = 2
        exclude = ("id",)


class SensorDataOnlySerializer(serializers.ModelSerializer):

    class Meta:
        model = Sensor
        fields = ("date", "data")


class tmpSerializer(serializers.ModelSerializer):
    class Meta:
        model = tmp
        fields = "__all__"