"""
Lab-02. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

import socket
import binascii
import os
import json
import time

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432
SERVER_ADDRESS = (SERVER_HOST, SERVER_PORT)
PATH = "images_client/innopolis.jpg"


def get_crc_checksum(file_contents):
    """
    Computes cyclic redundancy check (CRC) checksum for a given byte sequence.

    :param file_contents: byte sequence.
    :return: CRC checksum.
    """
    file_contents = (binascii.crc32(file_contents) & 0xFFFFFFFF)
    return "%08X" % file_contents


def client(path):
    """
    Client side of UDP application transferring image.
    Opens image with specified path in binary mode and reads the content.
    Calculates CRC checksum for an image and puts it in the dictionary. Besides, the dictionary includes fields 'name'
    and 'size'.
    Serialized dictionary transferred to the server.
    Client waits for the buffer size desired by the server. There was set timeout for receiving data of 1 second.
    The byte sequence of image is splitted in packets of the buffer size.
    Finally, waits for the response from server, whether the data was transferred without errors. If it is not so,
    client resend the image again.

    :param path: path to the image.
    """
    # open image in binary mode and read the content
    with open(path, 'rb') as image:
        data = image.read()

        # compute checksum for desired file
        checksum = get_crc_checksum(data)
        _, name = os.path.split(path)
        # it is conventional to have size of file in Bytes
        size = os.path.getsize(path)

        file_info = {
            'checksum': checksum,
            'name': name,
            'size': size
        }

        # serialize file information
        file_info_serial = json.dumps(file_info)

        # continually send information and file until server informs about reception
        message = ""
        while message != "OK":
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                # send dictionary to server
                sock.sendto(file_info_serial.encode(), SERVER_ADDRESS)
                # set timeout for waiting for response
                sock.settimeout(1)

                # receive buffer size from server
                try:
                    buffer_size, address = sock.recvfrom(100)
                    buffer_size = int(buffer_size.decode())
                except:
                    print("The server isn't available.")
                    break

                # split up bytes sequence on tokens of buffer size and send each of them independently
                tokens = [data[idx:idx + buffer_size] for idx in range(0, len(data), buffer_size)]
                for token in tokens:
                    time.sleep(0.0000000001)
                    sock.sendto(token, SERVER_ADDRESS)

                # wait for notification about successful reception of file
                try:
                    message, address = sock.recvfrom(buffer_size)
                    message = message.decode()
                    print(f"Server response: {message}")
                except:
                    continue


if __name__ == '__main__':
    client(PATH)
