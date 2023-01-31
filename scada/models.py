# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User


class Widget(models.Model):
    id = models.IntegerField(primary_key=True, auto_created=True)
    title = models.CharField('Наименование', blank=False, null=False, max_length=100, default='-')
    filename = models.CharField('Имя файла', blank=False, null=False, max_length=100, default='-')

    class Meta:
        verbose_name = 'Виджет'
        verbose_name_plural = 'Виджеты'
        ordering = ['title']

    def __str__(self):
        return self.title


class DataTypes(models.Model):
    id = models.IntegerField(primary_key=True, auto_created=True)
    subtitle = models.CharField('Имя в датчике', blank=False, null=False, max_length=10, default='-')
    title = models.CharField('Наименование', blank=False, null=False, max_length=100, default='--')
    units = models.CharField('Ед Измерения', blank=True, null=True, max_length=5, default='')
    divider = models.IntegerField('Делитель',  blank=False, null=False, default=1)
    sort = models.IntegerField('Индекс Сортировки', blank=False, null=False, default=9999)

    class Meta:
        verbose_name = 'Вид измерения'
        verbose_name_plural = 'Виды измерений'
        ordering = ['title']

    def __str__(self):
        return self.title


class SensorList(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField('Наименование', blank=False, null=False, max_length=150, default='неизвестнвый датчик')
    sort = models.IntegerField('Индекс Сортировки', blank=False, null=False, default=9999)
    active = models.BooleanField('Включен', blank=False, null=False, default=False)
    widget = models.ForeignKey(Widget, on_delete=models.CASCADE, blank=True, null=True, default=None)
    date = models.DateTimeField('Создано', auto_now_add=True)


    class Meta:
        verbose_name = 'Датчик'
        verbose_name_plural = 'Датчики'
        ordering = ['sort', 'title']

    def __str__(self):
        return f"{self.title}"


class Sensor(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    sensorId = models.ForeignKey(SensorList, on_delete=models.CASCADE, default=0)
    type = models.ForeignKey(DataTypes, on_delete=models.DO_NOTHING,   blank=True, null=True, default=None)
    data = models.IntegerField('данные', blank=True, null=True, default=0)
    date = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Данные'
        verbose_name_plural = 'Данные'
        ordering = ['-date']

    def __str__(self):
        return f"{self.sensorId}, {self.type}:{self.data} от  {self.date:%X (%d-%m-%y)}"

class SensorArhive (models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    sensorId = models.ForeignKey(SensorList, on_delete=models.CASCADE, default=0)
    type = models.ForeignKey(DataTypes, on_delete=models.DO_NOTHING,   blank=True, null=True, default=None)
    data = models.IntegerField('данные', blank=True, null=True, default=0)
    date = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Архив'
        verbose_name_plural = 'Архив'
        ordering = ['-date']

    def __str__(self):
        return f"{self.sensorId}, {self.type}:{self.data} от  {self.date:%X (%d-%m-%y)}"




class MyWidgets(models.Model):
    id = models.AutoField(primary_key=True)
    userId = models.ForeignKey(User, on_delete=models.CASCADE)
    sensor = models.ForeignKey(SensorList, on_delete=models.CASCADE)
    title = models.CharField('Наименование', blank=False, null=False, max_length=150, default='')
    sort = models.IntegerField('Индекс Сортировки', blank=False, null=False, default=9999)



class tmp(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    data = models.TextField('Прилетело', blank=True, null=True)
    date = models.DateTimeField('Создано', auto_now_add=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Помойка'
        verbose_name_plural = 'Помойка'
        ordering = ['-id']

    def __str__(self):
        return str(self.id) + ' ' + str(self.data) + ' ' + str(self.date)
