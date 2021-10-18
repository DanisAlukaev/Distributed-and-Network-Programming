"""
Final exam. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import hashlib

BUFF_SIZE = 1024
HOST = '127.0.0.1'
PORT = 50505
ADDRESS = (HOST, PORT)


def calc_hash(str_in: str):
    return hashlib.md5(str_in.encode('utf-8')).hexdigest()


def treat_client(conn, _):
    try:
        while True:
            data = conn.recv(BUFF_SIZE).decode()
            print("Message: ", data)
            hash_data = calc_hash(data)
            conn.sendall(hash_data.encode())
    except:
        pass
    print("Client disconnected")
    conn.close()


def server():
    with socket(AF_INET, SOCK_STREAM) as sock:
        sock.bind(ADDRESS)
        sock.listen()
        while True:
            conn, addr = sock.accept()
            t = Thread(target=treat_client, args=(conn, addr))
            t.start()


if __name__ == '__main__':
    server()
