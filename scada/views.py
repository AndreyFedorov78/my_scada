import datetime
import pytz

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import View
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import SensorList, DataTypes, Widget, MyWidgets, SensorArhive
from .serialalizers import MyWidgetsSerializer, GetWidgetsListSerializer
from . import current
from new_app import mqtt

#mqtt.mqtt_start()

class ButtonTest(LoginRequiredMixin, View):
    @staticmethod
    def get(request):
        return render(request, 'scada/bt.html')


class Index(LoginRequiredMixin, View):
    @staticmethod
    def get(request):
        widgets = Widget.objects.all()
        return render(request, 'scada/index.html', {'widgets': widgets})


class Clock(View):
    @staticmethod
    def get(request):
        return render(request, 'scada/clock.html')


class DevManage(APIView):
    @staticmethod
    def get(request):
        return Response(status=201)

    @staticmethod
    def post(request):
        if request.user.username != 'tester':
            if (type(request.data.get('id', "error")) != int or
                    request.data.get('val', "") == "" or
                    request.data.get('name', "") == ""):
                print("error")
                return Response(status=300)
            id = request.data['id'] % 256
            router = request.data['id'] - id
            val = request.data['val']
            name = request.data['name']
            topic = f'{mqtt.ROOT_TOPIC}RX/{router}/{id}/{name}'
            client = mqtt.connect_mqtt()
            client.publish(topic, val)
            client.disconnect()
            return Response(status=201)
        return Response(status=300)


class SensorView(APIView):
    @staticmethod
    def get(request):
        return Response(current.readings(SensorList.objects.all())[:200])


class SensorDataView(LoginRequiredMixin, APIView):
    @staticmethod
    def post(request, pk, data_type):
        sensor = SensorList.objects.filter(id=pk).first()
        data_type_obj = DataTypes.objects.filter(subtitle=data_type).order_by('id').first()
        if sensor is None or data_type_obj is None:
            return Response(None)
        found = [r for r in current.readings([sensor], {data_type: data_type_obj}) if r['type']]
        return Response(found[0] if found else None)


class AllSensors(LoginRequiredMixin, APIView):
    @staticmethod
    def get(request):
        return Response(current.readings(SensorList.objects.all()))


class SensorLastDays(APIView):
    @staticmethod
    def get(request, sensor_id, data_type, days):
        start_date = timezone.now() - datetime.timedelta(days=days)
        sensor = SensorArhive.objects.all().order_by('date').filter(sensorId=sensor_id, type=data_type,
                                                                    date__gt=start_date)
        sensor_new = []
        actual_date = timezone.now() - datetime.timedelta(days=days)
        dat = 0
        counter = 0

        for i in sensor:
            sensor_new.append({'date': i.date, 'data': i.data})
        """    if not (i.date.date() == actual_date.date() and i.date.hour == actual_date.hour):
                if counter != 0:
                    sensor_new.append({'date': actual_date, 'data': dat / counter})
                actual_date = i.date
                counter = 0
                dat = 0
            dat += i.data
            counter += 1
        sensor_new.append({'date': actual_date, 'data': dat / counter if counter != 0 else 0})
        """

        return Response(sensor_new)


# Работа со списком доступных датчиков конкретного пользователя

class UserWidgets(LoginRequiredMixin, APIView):
    @staticmethod
    def get(request, id=None):
        all_widgets = MyWidgets.objects.filter(userId_id=request.user).order_by('sort')
        serializer = MyWidgetsSerializer(all_widgets, many=True)
        serializer.data[0]['online'] = True
        return Response(serializer.data)

    @staticmethod
    def post(request, id=None):

        if id is None:
            all_widgets = MyWidgets.objects.filter(userId_id=request.user).select_related('sensor').order_by('sort')
            serializer = MyWidgetsSerializer(all_widgets, many=True)
            sensors = {w.sensor_id: w.sensor for w in all_widgets}
            values = current.get_many(sensors)
            rows = current.readings(sensors.values(), values=values)
            now = timezone.now()
            for i in serializer.data:
                sensor_id = i['sensor']['id']
                i['data'] = [r for r in rows if r['sensorId']['id'] == sensor_id]
                i['data'].sort(key=lambda x: x['type']['sort'] if x['type'] else 9999)
                i['online'] = True
                i['date'] = "--"
                if values.get(sensor_id):
                    last = max(date for _, date in values[sensor_id].values())
                    local = timezone.localtime(last)
                    if (now - last).total_seconds() > 600:
                        i['online'] = False
                    if (now - last).total_seconds() > 24 * 60 * 60:
                        i['date'] = f"{local.day}/{local.month}/{local.year}"
                    else:
                        i['date'] = f"{local:%H:%M}"
            return Response(serializer.data)
        else:  # двигаем виджет
            title = request.data.get('title')
            if title is not None:
                object1 = MyWidgets.objects.get(pk=id)
                object1.title = title
                object1.save()
                return Response(status=201)
            step = request.data.get('step')
            if step is None:
                return Response(status=201)
            object1 = MyWidgets.objects.get(pk=id)
            if 1 == step:
                object2 = MyWidgets.objects.filter(sort__gt=object1.sort).order_by('sort')
            else:
                object2 = MyWidgets.objects.filter(sort__lt=object1.sort).order_by('-sort')
            if len(object2) == 0:
                return Response(status=201)
            object2 = object2[0]
            object1.sort, object2.sort = object2.sort, object1.sort
            object2.save()
            object1.save()

            return Response(status=201)

    @staticmethod
    def delete(request, id):
        MyWidgets.objects.filter(pk=id).delete()
        return Response(status=201)

    # добавление датчика в список
    @staticmethod
    def put(request, id=None):

        user = request.user
        if id is None:
            return Response(status=204)  # если не найден id в запросе
        if len(MyWidgets.objects.filter(userId=user).filter(sensor__id=id)) > 0:
            return Response(status=203)  # если такая запись уже существует
        sensor = SensorList.objects.filter(id=id)
        if len(sensor) == 0:
            return Response(status=203)  # если не существует такого датчика
        # если все нормально создаем новую запись
        sort = 0
        my_list = MyWidgets.objects.filter(userId_id=request.user).order_by('-sort')
        if len(my_list) > 0:
            sort = my_list[0].sort + 1
        sensor = sensor[0]
        widget = MyWidgets()
        widget.userId = user
        widget.sensor = sensor
        widget.title = sensor.title
        widget.sort = sort
        widget.save()
        return Response(status=201)


class GetWidgetsList(LoginRequiredMixin, APIView):
    @staticmethod
    def post(request):
        my_sensors = MyWidgets.objects.filter(userId=request.user).values('sensor')
        new_sensors = SensorList.objects.exclude(id__in=my_sensors).filter(active=True)
        result = GetWidgetsListSerializer(new_sensors, many=True).data
        # так как java не работает по умолчанию с 64разрядными целыми
        # переодим id в строку
        for item in result:
            item['id']=f"{item['id']}"
        return Response(result)


class Home(LoginRequiredMixin, View):
    @staticmethod
    def get(request):
        data = {}
        return render(request, 'scada/home.html', data)



class OldIpad(View):
    @staticmethod
    def get(request):
        alarm_level = 35
        kolodez = current.client().hgetall(current.KEY.format(1953992294))
        water = current.parse(kolodez['W'])[0]
        waterCM, water_date = current.parse(kolodez['WCM'])
        delta = (timezone.now() - water_date).total_seconds()

        #pool = SensorList.objects.filter(title='Бассеин')[0]
        pool = 0

        temp_types = list(DataTypes.objects.filter(title="Температура").values_list('subtitle', flat=True))

        def temperature_of(title):
            sensor = SensorList.objects.filter(title=title)[0]
            fields = current.client().hgetall(current.KEY.format(sensor.id))
            subtitle = next(t for t in temp_types if t in fields)
            return current.parse(fields[subtitle])[0] / 10

        temperature = temperature_of('Улица дача')
        temperature2 = temperature_of('Гостинная дача')

        pressure = "" # all_data.filter(type__title="Давление")[0].data
        humidity = "" # all_data.filter(type__title="Влажность")[0].data / 10
        hour = datetime.datetime.now(pytz.timezone('Europe/Moscow')).hour
        minute = datetime.datetime.now(pytz.timezone('Europe/Moscow')).minute

        online = (delta < 600)
        data = {
            'alarm': water < alarm_level,
            'pool': pool,
            'hour': f"{hour:02}",
            'minute': f"{minute:02}",
            'level': int(water / 100 * 350 + 50),
            'water': water,
            'waterCM': waterCM/100,
            'online': online,
            'temperature': temperature,
            'temperature2': temperature2,
            'pressure': pressure,
            'humidity': humidity
        }
        return render(request, 'scada/ipad2.html', data)


class Connect(LoginRequiredMixin, APIView):
    @staticmethod
    def get(request):
        answer = mqtt.client is not None and mqtt.client.is_connected()
        # mqtt.client.enable_logger()
        # subscribe=mqtt.client.
        return Response({'connect': answer})


"""
Спарвочник ответов http :
200 OK («хорошо»)[2][3];
201 Created («создано»)[2][3][4];
202 Accepted («принято»)[2][3];
203 Non-Authoritative Information («информация не авторитетна»)[2][3];
204 No Content («нет содержимого»)[2][3];
205 Reset Content («сбросить содержимое»)[2][3];
206 Partial Content («частичное содержимое»)[2][3];
207 Multi-Status («многостатусный»)[5];
208 Already Reported («уже сообщалось»)[6];
226 IM Used («использовано IM»).
"""
