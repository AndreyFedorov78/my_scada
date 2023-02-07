from django.apps import AppConfig

class NewAppConfig(AppConfig):
    name = 'new_app'

    def ready(self):
        from new_app import mqtt
        from new_app import user
        #from .user import save
        #mqtt.client.loop_forever()
        mqtt.client.loop_start()
        #mqtt.client.is_connected()
