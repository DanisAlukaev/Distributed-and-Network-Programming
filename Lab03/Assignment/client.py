"""
Lab-03. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

import socket
import os

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432
SERVER_ADDRESS = (SERVER_HOST, SERVER_PORT)
PATH = "files_client/innopolis.jpg"


def client(path):
    """
    Client side of UDP application transferring image.
    Opens image with specified path in binary mode and reads the content.
    Initialize connection by sending start message containing descriptor 's', sequence number, extension and size of
    file to be transferred. To do so there are allowed 5 attempts. Otherwise, the program finishes.
    The byte sequence of image is splitted in packets of the buffer size. Each packet is sent to the server until each
    packet arrival is acknowledged. The data message contains descriptor 'd' and data bytes. The timeout is set to 0.5
    seconds, failing which starts retransmission of file.

    :param path: path to the file to be transferred.
    """
    # open image in binary mode and read the content
    with open(path, 'rb') as image:
        data = image.read()

        # take the name and extract an extension
        _, name = os.path.split(path)
        extension = name.split('.')[1]
        # it is conventional to have size of file in Bytes
        size = os.path.getsize(path)

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(0.5)
            # initiate sequence number
            seqnum = 0

            # initiate number of attempts made
            ATTEMPTS = 0
            # wait for response on start message until program made 5 attempts
            while ATTEMPTS < 5:
                ATTEMPTS += 1
                # compose and send the start message
                start_message = f"s|{seqnum}|{extension}|{size}"
                sock.sendto(start_message.encode(), SERVER_ADDRESS)

                try:
                    # receive response from server
                    response, address = sock.recvfrom(100)
                    response = response.decode().split('|')

                    # acceptable response is only ack
                    if response[0] != 'a':
                        continue

                    # set maximal size of message
                    maxsize = int(response[2])
                    # update sequence number
                    seqnum = int(response[1])
                    break
                except:
                    continue

            if ATTEMPTS == 5:
                print("Server is not available. ")
                return

            # increment sequence number
            seqnum += 1
            # to transfer each packet there is quota of 5 attempts
            ATTEMPTS = 0
            # index of byte from which will start next message
            last_idx = 0
            while last_idx < len(data) and ATTEMPTS < 5:
                # send until whole byte sequence is not transferred or number attempts is greater than 5

                ATTEMPTS += 1
                # encode string part of the message
                data_message = f"d|{seqnum}|".encode()
                # number of data bytes that are to be transferred
                bytes_left = len(data[last_idx:])
                # number of bytes that are reserved for separators, descriptor ('s'/'d') and sequence number
                aux_bytes = len(data_message)
                # segment size is either the number of left data bytes or number of bytes left in the message
                segment_size = min(maxsize - aux_bytes, bytes_left)
                # segment
                segment = data[last_idx: last_idx + segment_size]
                # compose data message
                data_message += segment
                # send data message
                sock.sendto(data_message, SERVER_ADDRESS)
                try:
                    # receive response from server
                    response, address = sock.recvfrom(100)
                    response = response.decode().split('|')

                    # acceptable response is only ack
                    if response[0] != 'a':
                        continue

                    # update last index to index of next byte
                    last_idx += segment_size
                    # increment sequence number
                    seqnum = int(response[1]) + 1
                    # reset number of attempts
                    ATTEMPTS = 0
                except:
                    continue
            if ATTEMPTS == 5:
                print("Server is not available.")
                return
            print("File was successfully sent!")


if __name__ == "__main__":
    client(PATH)
