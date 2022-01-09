# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class Sensor(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    sensorId = models.IntegerField('Датчик', blank=True, null=True, default=None)
    type = models.IntegerField('тип данных', blank=True, null=True, default=None)
    data = models.IntegerField('данные', blank=True, null=True, default=0)
    date = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Данные'
        verbose_name_plural = 'Данные'
        ordering = ['-date']

    def __str__(self):
        return str(self.date)+' id='+str(self.sensorId)+' type='+str(self.type)+' data='+str(self.data)
