#!/usr/bin/env python
import socket


def print_arr(arr):
   for i in arr:
       print(hex(i), end=" ")
   print()


SITE = 'localhost'
PORT = 1883


client_sock = socket.socket()
client_sock.connect((SITE, PORT))

server_sock = socket.socket()
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # порт будет сразу освобождаться по завершении программы
server_sock.bind(('', 9090))
server_sock.listen(1)
conn, addr = server_sock.accept()

while True:
    data = conn.recv(1024)
    if not data:
        break
    print (f"client -> {data}")
    print_arr(data)
    client_sock.send(data)
    result = client_sock.recv(1024)
    print(f"server -> {result}")
    conn.send(result)
conn.close()


