"""
Final exam. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

from socket import socket, AF_INET, SOCK_STREAM

BUFF_SIZE = 1024

addr = ('127.0.0.1', 50505)

if __name__ == '__main__':
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(addr)

    while True:
        try:
            str_in = input('Enter a string: ')
            sock.send(str_in.encode())
            result = sock.recv(BUFF_SIZE)
            print("Hash: ", result.decode())
        except KeyboardInterrupt:
            sock.close()
            exit()
