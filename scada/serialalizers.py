from rest_framework import serializers
from .models import MyWidgets, SensorList

class MyWidgetsSerializer(serializers.ModelSerializer):

    class Meta:
        model = MyWidgets
        depth = 3
        exclude = ("userId",)


class GetWidgetsListSerializer(serializers.ModelSerializer):

    class Meta:
        model = SensorList
        fields = ("id", "title")
