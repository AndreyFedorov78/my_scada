#!/usr/bin/env python
# Библеотека работы с Blynk, написана для использования с Django и DjangoRestFramework
# При этом сериализация в JSON происходит силами джанго
# Весь обмен данными с Blynk происходит методом get

import requests
import re


class Blynk:

    def __init__(self):
        self.key = 'fEMKjdL0qCSFaRpozBMJMVEST74eaNqx'  # сюда надо подставить ключ Blynk
        self.path = 'http://blynk-cloud.com/' + self.key  # путь к управлению Blynk

        self.struct = [
            # структура полей name: имя параметра для обмена с основной программой
            # v: соответствующая переменная в Blynk
            # write: разрешение на запись
            # max, min - ограничение при записи
            {'name': 'speed', 'v': 'V1', 'write': True, 'min': 1, 'max': 4},
            {'name': 'heat', 'v': 'V2', 'write': True, 'min': 0, 'max': 5},
            {'name': 'rotor', 'v': 'V10', 'write': False},
            {'name': 'heating', 'v': 'V6', 'write': False},
            {'name': 't_from_out', 'v': 'V8', 'write': False},
            {'name': 't_from_in', 'v': 'V0', 'write': False},
            {'name': 't_to_in', 'v': 'V9', 'write': False},
            {'name': 't_to_out', 'v': 'V7', 'write': False},
            {'name': 't_heater', 'v': 'V3', 'write': False},
            {'name': 'reg', 'v': 'V5', 'write': True, 'min': 0, 'max': 5000},
            {'name': 'reg_val', 'v': 'V4', 'write': True, 'min': -500, 'max': 500},
        ]
        # self.data = {}  # сюда загружаются все данные
        # self.get_all()  # чтение данных
        return

    def get_all(self):  # чтение всех данных описанных в структуре
        for i in self.struct:
            self.data[i['name']] = self.get_value(i['v'])
        return self.data

    def put_data(self, data):  # отправка данных
        for i in self.struct:
            if i['name'] in data and i['write']:
                x = data[i['name']]
                if i['min'] <= x <= i['max']:
                    self.data[i['name']] = x
                    self.put_value(i['v'], x)
        return

    def put_value(self, v, value):  # получение одного значения
        result = requests.get(self.path + '/update/' + v + '?value=' + str(value))
        return result

    def get_value(self, v):  # отправка одного значения
        result = requests.get(self.path + '/get/' + v)
        return re.findall('[0-9]+', result.text)[0]

    def __str__(self):
        return str(self.data)


if __name__ == '__main__':  # Пример
    b = Blynk()
    print(b)
    b.put_data({'heat': 0})
