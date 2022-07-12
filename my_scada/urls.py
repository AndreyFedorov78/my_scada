"""my_scada URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path , include
from scada.views import Index, OldIpad, Clock, Connect, ButtonTest

#from rest_framework import routers
#import scada

urlpatterns = [
    path("", Index.as_view()),
    path("ipad", OldIpad.as_view()),
    path("connect/", Connect.as_view()),
    path("clock", Clock.as_view()),
    path("bt", ButtonTest.as_view()),
    path('admin/', admin.site.urls),
    path('api/',include('rest_framework.urls')),
    path('scada_api/', include('scada.urls')),
    path('accounts/', include('django.contrib.auth.urls'))
]
