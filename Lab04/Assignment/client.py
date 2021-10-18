"""
Lab-04. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

import socket
import sys


def client():
    """
    Client side of TCP guessing game.
    Reads command line arguments corresponding to the port number and address of the server. Parse them and check for
    validity.
    Connects to the server using the provided address and port. If it is not available, notify the user.
    Waits the message from the server, it is either
    1. Warning "The server is full"
    2. New port.
    If the server is full, the connection is closed. Otherwise, connects to the new port of server.
    Game starts. Accepts welcome message from the server.
    Reads the range of numbers from the command prompt and send it to the server.
    In the loop, function:
    1. Sends the guess number.
    2. Accepts the correctness of guess.
    3. Finishes the process if the there are no attempts or the user won.
    """
    # parse command line argument
    if len(sys.argv) != 3:
        print("Usage example: python ./client.py <address> <port>")
        return
    server_host = sys.argv[1]
    server_port = int(sys.argv[-1])

    try:
        # connect to the server with provided address and port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((server_host, server_port))
            except:
                print("Server is unavailable")
                return
            # either "Server is full" or new port number
            response = sock.recv(1024).decode()
            if response == "The server is full":
                print(response)
                return

        # connect to the server with new port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((server_host, int(response)))
            except:
                print("Server is unavailable")
                return

            # accept welcome message
            message = sock.recv(1024).decode()
            print(message)

            num_range = input("> ")
            # read and check for validity range of numbers
            while True:
                try:
                    a, b = map(int, num_range.split(' '))
                    # first number should be less
                    assert (a < b)
                    break
                except:
                    num_range = input("Enter the range:\n> ")
                    continue
            # send the range of numbers
            try:
                sock.send(num_range.encode())
            except:
                print("Connection lost")
                return

            while True:
                # number of attempts
                message = sock.recv(1024).decode()
                print(message)

                try:
                    guess = input("> ")
                    sock.send(guess.encode())
                except:
                    print("Connection lost")
                    return

                # correctness of guess
                response = sock.recv(1024).decode()
                print(response)
                if response not in ["Greater", "Less"]:
                    break
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    client()
