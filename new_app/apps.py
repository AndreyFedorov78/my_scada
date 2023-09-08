from django.apps import AppConfig


class NewAppConfig(AppConfig):
    name = 'new_app'

    def ready(self):
        pass
"""
        from .mqtt import connect_mqtt,subscribe
        client = connect_mqtt()  # Изменение значения клиента
        subscribe(client)  # Подписка на MQTT
        client.loop_start()

"""
