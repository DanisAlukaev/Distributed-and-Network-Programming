"""
Lab-02. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

import socket

HOST = '127.0.0.1'
PORT = 65432
SERVER_ADDRESS = (HOST, PORT)
BUFFER = 100


def client():
    """
    Client side of client-server calculator.
    Reads from the standard input command for calculation.
    Command should be in the form of 'operator left_operand right_operand'.
    Uses UDP connection to transfer command to server and receive the result.
    User can quit from application using KeybordInterrupt or by typing 'quit' in any cases.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        while True:
            try:
                # read command
                data = input('Input command for calculation: ')
                # check whether user wants to quit the application
                if data.lower() == 'quit':
                    print("User has quit.")
                    break
            except KeyboardInterrupt:
                print("Keyboard interrupt, user has quit.")
                break
            # send command
            sock.sendto(data.encode(), SERVER_ADDRESS)
            # receive result of computation from server
            message, address = sock.recvfrom(BUFFER)
            print(f"Result: {message.decode()}\n")


if __name__ == '__main__':
    client()
