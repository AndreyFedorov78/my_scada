from django.contrib import admin
from django.urls import path, include
from .views import SensorView, SensorDetailView, Index, AllSensors, DevManage, SensorLastDays, tmpView
from .views import UserWidgets, GetWidgetsList, Connect

urlpatterns = [
    path("sensor/", SensorView.as_view()),
    path("getsensor/", GetWidgetsList.as_view()),
    path("mywidgets/", UserWidgets.as_view()),
    path("mywidgets/<int:id>/", UserWidgets.as_view()),
    path("allsensors/", AllSensors.as_view()),
    path("devmanage/", DevManage.as_view()),
    path("sensor_detail/<int:pk>/", SensorDetailView.as_view()),
    path("sensor_last_days/<int:sensor_id>/<int:data_type>/<int:days>", SensorLastDays.as_view()),

    path("tmp/", tmpView.as_view()),
    path("connect/", Connect.as_view()),

]
