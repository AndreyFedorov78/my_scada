from django.contrib import admin
from django.urls import path, include
from .views import SensorView, SensorDetailView

urlpatterns = [
    path("sensor/", SensorView.as_view()),
    path("sensor_detail/<int:pk>/", SensorDetailView.as_view())
]
