

from django.contrib.auth.models import User
from subprocess import run

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender=User)
def update_password(sender, instance, **kwargs):
    #update_mosquitto_password(instance.username, instance.password)
    print('---')
    if instance._password is not None:
        if kwargs['created']:
                print(f' Создаем пользователя {instance.username} с паролем {instance._password}')
        else:
                print(f' Меняем пароль пользователя {instance.username} на {instance._password}')


@receiver(post_delete, sender=User)
def delete_user_from_masquitto(sender, instance, **kwargs):
    print(f'перехват удаления пользователя  {instance.username}')
    #delete_user_from_masquitto(User, instance)




"""

def update_mosquitto_password(username, password):
    print(f'!! {username} {password}')
    result = 0 # run(['mosquitto_passwd', '-b', '/etc/mosquitto/password', username, password], stdout=subprocess.PIPE)
    #if result.returncode != 0:
        # handle error
    #    pass

def update_user_password(sender, instance, **kwargs):
    if instance.password:
        update_mosquitto_password(instance.username, instance.password)

def save(self, *args, **kwargs):
    print(f'save')
    is_new = self.pk is None
    super(User, self).save(*args, **kwargs)
    if is_new:
        update_user_password(User, self)
    else:
        update_user_password(User, self)
User.save = save"""