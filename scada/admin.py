from django.contrib import admin

# Register your models here.
from scada.models import Sensor

admin.site.register(Sensor)
