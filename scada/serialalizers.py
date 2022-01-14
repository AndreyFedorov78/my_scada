from rest_framework import serializers
from .models import Sensor


class SensorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sensor
        fields = "__all__"
       # fields = ("sensorId", "type", "data", "date")


class SensorDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sensor
        exclude = ("id",)


class SensorDataOnlySerializer(serializers.ModelSerializer):

    class Meta:
        model = Sensor
        fields = ("date", "data")
