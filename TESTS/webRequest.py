#!/usr/bin/env python
import socket


def print_arr(arr):
   for i in arr:
       print(hex(i), end=" ")
   print()


SITE = '192.168.2.2'
#SITE = 'crm.fedorov.team'
PORT = 80


print('1')
client_sock = socket.socket()
client_sock.connect((SITE, PORT))
print('2')

server_sock = socket.socket()
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # порт будет сразу освобождаться по завершении программы
server_sock.bind(('', 8080))
print('3')
server_sock.listen(1)
print('4')
conn, addr = server_sock.accept()
print('!!!')
while True:
    data = conn.recv(1024)
    if not data:
        break
    print (f"client -> {data}\n")
    print(f"client -> {data.__len__()}")
    # print_arr(data)
    client_sock.send(data)
    result = client_sock.recv(1024)
    print(f"server -> {result}")
    print(f"client -> {result.__len__()}")
    conn.send(result)
conn.close()


