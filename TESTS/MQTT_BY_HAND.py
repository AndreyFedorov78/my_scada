#!/usr/bin/env python
import socket


def make_message(msg,topic):
    result = topic+msg
    result = '\x00'+chr(len(topic))+result
    result = '0'+chr(len(result))+result
    result = b''+bytearray(result, 'utf-8')
    return result



message_string=make_message("hi form andrey",'test')
#message_string=make_message('testmessages:1234567890')
SITE = 'fedorov.team'
PORT = 1883


client_sock = socket.socket()
client_sock.connect((SITE, PORT))

print('Тест отправки сообщения')
connect_string = b'\x10\x1b\x00\x04MQTT\x04\x02\x00<\x00\x0fpython-mqtt-123'
"""
\x10 - запрос подключения
\x1b - длинная пакета 
\x00 -или Packet identifier или 0
\x04MQTT - протакол с указанием длинны
\x04 - версия протокола
\x02 - флаги
\x00 - 
<    - 
\x00 - 
\x0f - 
python-mqtt-123'
"""


print(message_string)
client_sock.send(connect_string)
result = client_sock.recv(1024)
print(result)
client_sock.send(message_string)


print('Тест подписки')



"""
print(f'string type: {type(connect_string)} {connect_string[0]}')
print(f'string len: {len(connect_string)} {connect_string[1]}')
print(f'string len: {len(message_string)} {message_string[1]}')
"""



"""

while True:
    data = conn.recv(1024)
    if not data:
        break
    print (f"client -> {data}")
    client_sock.send(data)
    result = client_sock.recv(1024)
    print(f"server -> {result}")
    conn.send(result)
conn.close()

"""


"""

подписка


client -> b'\x10\x1b\x00\x04MQTT\x04\x02\x00<\x00\x0fpython-mqtt-123'
0x10 0x1b 0x0 0x4 0x4d 0x51 0x54 0x54 0x4 0x2 0x0 0x3c 0x0 0xf 0x70 0x79 0x74 0x68 0x6f 0x6e 0x2d 0x6d 0x71 0x74 0x74 0x2d 0x31 0x32 0x33 
server -> b' \x02\x00\x00'
client -> b'\x82\t\x00\x01\x00\x04test\x00'
0x82 0x9 0x0 0x1 0x0 0x4 0x74 0x65 0x73 0x74 0x0 
server -> b'\x90\x03\x00\x01\x00'
client -> b'\xc0\x00'
0xc0 0x0 
server -> b'0\x11\x00\x04testmessages: 00\x11\x00\

"""