from django.contrib import admin

# Register your models here.
from scada.models import Sensor, SensorList, DataTypes, tmp, Widget, SensorArhive


class SensorAdmin(admin.ModelAdmin):
    # list_display = ( 'date', 'user_id', 'worktime' ,'project_id')
    # sensorId  type data  date
    list_filter = ('sensorId', 'type')
    date_hierarchy = 'date'
    #inlines = ('type',)
    # search_fields = ('user_id__name', 'project_id__title')


admin.site.register(Sensor, SensorAdmin)
admin.site.register(SensorArhive, SensorAdmin)
admin.site.register(tmp)
admin.site.register(Widget)
admin.site.register(SensorList)
admin.site.register(DataTypes)
