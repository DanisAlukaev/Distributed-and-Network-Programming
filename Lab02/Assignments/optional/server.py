"""
Lab-02. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

import socket
import json
import binascii
import time

HOST = '127.0.0.1'
PORT = 65432
ADDRESS = (HOST, PORT)
BUFFER = 100


def get_crc_checksum(file_contents):
    """
    Computes cyclic redundancy check (CRC) checksum for a given byte sequence.

    :param file_contents: byte sequence.
    :return: CRC checksum.
    """
    file_contents = (binascii.crc32(file_contents) & 0xFFFFFFFF)
    return "%08X" % file_contents


def server():
    """
    Server side of UDP application transferring image.
    Receives information about the file to be transferred.
    Sends size of the buffer for client to transfer byte sequence in portions.
    Receives file and checks whether the checksum is valid.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(ADDRESS)
        while True:
            # receive file_info
            message, address = sock.recvfrom(BUFFER)
            try:
                # decode message
                message = message.decode()
                # convert string representation to dictionary
                file_info = json.loads(message)
            except Exception as e:
                # send exception method
                response = e.message if hasattr(e, 'message') else "Unresolved exception occurred."
                sock.sendto(response.encode(), address)
                continue

            print(f"Address of connected client: {address}.")
            print(f"Received dictionary: {file_info}.")

            # send buffer size to client
            sock.sendto(str(BUFFER).encode(), address)

            # iteratively append packets received from client
            # resultant byte sequence is the expected image
            file = b''
            start = time.time()
            # repeat until the file is accepted or it took much time since the last reception
            while len(file) < file_info['size'] and time.time() - start < 1:
                start = time.time()
                message, address = sock.recvfrom(BUFFER)
                file += message

            # check whether data is corrupted
            if file_info['checksum'] == get_crc_checksum(file):
                # write received data to new file
                name = 'new_' + file_info['name']
                path = 'images_server/' + name
                with open(path, 'wb+') as output:
                    output.write(file)

                time.sleep(5)
                # inform about successful reception of file
                sock.sendto("OK".encode(), address)
                continue
            sock.sendto("ERR".encode(), address)


if __name__ == '__main__':
    server()
