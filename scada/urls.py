from django.contrib import admin
from django.urls import path, include
from .views import SensorView, SensorDetailView, Index, AllSensors, Vent, SensorLastDays

urlpatterns = [
    path("sensor/", SensorView.as_view()),
    path("allsensors/", AllSensors.as_view()),
    path("vent/", Vent.as_view()),
    path("sensor_detail/<int:pk>/", SensorDetailView.as_view()),
    path("sensor_last_days/<int:sensor_id>/<int:data_type>/<int:days>", SensorLastDays.as_view()),
]
