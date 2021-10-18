"""
Lab-03. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

import socket
import time

HOST = '127.0.0.1'
PORT = 65432
ADDRESS = (HOST, PORT)
BUFFER = 100


def split_byte(byte_seq, sep=b'|', no_occur=2):
    """
    Function used to split the byte sequence by a separator.
    Built-in function split tend to give wrong results when byte sequence contain separator that not intended to be.
    For instance, it useful while processing data received by a socket. The data bytes might contain '|' symbol that
    is separator.

    :param byte_seq: byte sequence to be splitted.
    :param sep: byte by which the sequence should be splitted.
    :param no_occur: expected number of separators.
    :return: list of byte sequences.
    """

    # determine indexes of separator occurrences
    idxs = []
    for idx, _byte in enumerate(byte_seq):
        if _byte == 124:
            idxs.append(idx)
        if len(idxs) == no_occur:
            break

    # split the byte sequence basing on obtain indexes
    splitted = []
    for i, idx in enumerate(idxs):
        if idx == idxs[0]:
            # first occurrence
            splitted.append(byte_seq[0:idx])
            splitted.append(byte_seq[idx + 1:idxs[i + 1]])
        elif idx == idxs[-1]:
            # last occurrence
            splitted.append(byte_seq[idx + 1:])
        else:
            # occurrence in the middle
            splitted.append(byte_seq[idxs[i] + 1:idxs[i + 1]])

    return splitted


def server():
    """
    Server side of UDP application transferring image.
    Handles start message containing sequence number, extension and size of file. Create new entry in dictionary of
    active sessions. Acknowledges arrival by message containing descriptor 'a', sequence number and buffer size.
    Handles data message containing sequences number and data bytes. Concatenate data bytes with the current version of
    file. Ignores repeated data bytes. Acknowledges arrival by message containing descriptor 'a' and sequence number.
    Stores information about each session. If session is inactive (for 3 seconds) or successfully finished more
    than 1 second ago, delete the information. For successfully finished sessions saves file.
    """
    sessions = {}

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(ADDRESS)
        sock.settimeout(0.5)
        while True:
            # check whether information about successfully finished sessions should be removed
            for host in list(sessions.keys()):
                current_file = sessions[host]['file']
                expected_size = sessions[host]['expected_size']
                last_message = sessions[host]['time_reception']
                if len(current_file) == expected_size and time.time() - last_message >= 1:
                    info = sessions.pop(host)
                    # save file
                    name = f"{host}.{info['extension']}"
                    path = 'files_server/' + name
                    with open(path, 'wb+') as output:
                        output.write(info['file'])
                    print(f"Successfully finished session with host {host} was deleted (1 second timeout).")

            # check whether the client is active for three seconds
            for host in list(sessions.keys()):
                last_message = sessions[host]['time_reception']
                if time.time() - last_message >= 3:
                    sessions.pop(host)
                    print(f"Session with host {host} is inactive for 3 seconds, erase information.")

            try:
                # receive file_info
                message, address = sock.recvfrom(BUFFER)
                # either 's' or 'd', start or data message respectively
                descriptor = message[:1].decode()
            except:
                # in order to constantly check if sessions' information should be deleted, timeout was set to 0.5
                continue

            if descriptor == 's':
                # start message

                # split byte sequence and decode each piece
                message = split_byte(message, no_occur=3)
                message[0] = message[0].decode()
                message[1] = message[1].decode()
                message[2] = message[2].decode()
                message[3] = message[3].decode()
                # create an entry with information about the session
                sessions[address[0]] = {
                    'extension': message[2],
                    'seqn': int(message[1]),
                    'expected_size': int(message[3]),
                    'time_reception': time.time(),
                    'file': b""
                }

                # increment sequence number
                sessions[address[0]]['seqn'] += 1
                # compose and send ack response
                ack_message = f"a|{sessions[address[0]]['seqn']}|{BUFFER}"
                sock.sendto(ack_message.encode(), address)

            if descriptor == 'd':
                # data message
                # split byte sequence and decode descriptor and sequence number
                message = split_byte(message, no_occur=2)
                message[0] = message[0].decode()
                # sequence number
                message[1] = message[1].decode()

                # update time of last reception
                sessions[address[0]]['time_received'] = time.time()

                if int(message[1]) > sessions[address[0]]['seqn']:
                    # not a duplicate message

                    # update sequence number
                    sessions[address[0]]['seqn'] = int(message[1])
                    # append new packet
                    sessions[host]['file'] += message[2]
                    # increment sequence number
                    sessions[address[0]]['seqn'] += 1
                    # compose and send ack response
                    ack_message = f"a|{sessions[address[0]]['seqn']}"
                    sock.sendto(ack_message.encode(), address)


if __name__ == '__main__':
    server()
