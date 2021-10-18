"""
Lab-04. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

import sys
import socket
import random
import time
from threading import Thread

HOST = '127.0.0.1'
MAX_CONNECTIONS = 2


def treat_client(port):
    """
    Worker function supposed to run in the thread.
    Creates new socket and binds to it using the same host, but different port number provided as argument.
    Waits for the client connection for 5 seconds.
    Sends welcome message with game rules.
    Accepts the range of numbers, in which user will guess. Checks for validity of the range.
    User has 5 attempts to guess the number.
    In the loop, function:
    1. Sends attempts left.
    2. Accepts the guess.
    3. Sends whether the number is greater or less.
    In case the number is guessed, the user won. If the all attempts are used, the user lost.

    :param port: port to establish new socket.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # try to bind to the provided port and localhost address
        try:
            sock.bind((HOST, port))
            sock.listen(1)
        except:
            print("Error while binding to the random port")
            return

        # wait for 5 seconds for incoming connection
        sock.settimeout(5)
        try:
            connection, host = sock.accept()

            # send welcome message
            connection.send("Welcome to the number guessing game!\nEnter the range:".encode())
            # accept the range of numbers and randomly select number within the interval
            num_range = map(int, connection.recv(1024).decode().split(' '))
            number = random.randint(*num_range)

            ATTEMPTS = 0
            while True:
                # attempts left
                connection.send(f"You have {5 - ATTEMPTS} attempts".encode())
                # accept user's guess
                guess = int(connection.recv(1024).decode())
                ATTEMPTS += 1

                # check whether the number is guessed, greater or less than original
                if guess == number:
                    connection.send("You win!".encode())
                    break

                if ATTEMPTS == 5:
                    connection.send("You lose".encode())
                    break

                if guess < number:
                    connection.send("Greater".encode())

                if guess > number:
                    connection.send("Less".encode())

                # the program was tested on Windows, Mac and Ubuntu
                # the latter OS tend to concatenate two messages (this behavior is not observed anywhere else)
                # to avoid this issue, one can use delay
                time.sleep(0.00001)
            connection.close()
        except:
            # ends if no connection
            return


def get_free_port():
    """
    Auxiliary function used to generate random free port for the thread workers.
    Binds to the socket with port 0, which specifies to the OS that we allocate any free port.
    Get the port and close the socket.

    :return: port number.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        port = sock.getsockname()[1]
        sock.close()
    return port


def server():
    """
    Server side of TCP guessing game.
    Reads command line argument corresponding to the port number for the server. Parse it and check for validity.
    Creates new socket and binds to it using the address specified by programmer (default: 127.0.0.1) and port specified
    by user.
    The user can finish the routine by Keyboard Interrupt.
    In the loop waits for a new connection. If number of client is greater than number specified by the programmer
    (default: 2), then server responds that it is full. Otherwise, it generates new port number and runs the thread worker
    in the separate thread.
    """
    # parse command line argument
    if len(sys.argv) != 2:
        print("Usage example: python ./server.py <port>")
        return
    port = int(sys.argv[-1])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

        # try to bind to the provided port and localhost address
        try:
            sock.bind((HOST, port))
            sock.listen(MAX_CONNECTIONS)
        except:
            print("Error while binding to the specified port")
            return
        print(f"Starting the server on {HOST}:{port}")

        # continuously wait for incoming connections
        try:
            threads = []
            while True:
                # waiting for incoming connection
                print("Waiting for a connection")
                connection, host = sock.accept()

                # remove threads that are not alive
                threads = list(filter(lambda x: x.is_alive(), threads))

                # check if the number of live threads not more than the max number of connections
                if len(threads) == MAX_CONNECTIONS:
                    connection.send("The server is full".encode())
                    continue
                print("Client connected")

                # create new thread in which the game logic will run
                while True:
                    # generate available port
                    new_port = get_free_port()

                    # create and run thread
                    thread = Thread(target=treat_client, args=(new_port,))
                    threads.append(thread)
                    try:
                        threads[-1].start()
                        break
                    except:
                        continue

                # send new port to the client and close connection
                connection.send(str(new_port).encode())
                connection.close()

        except KeyboardInterrupt:
            # print("Keyboard Interrupt, exiting")
            return


if __name__ == "__main__":
    server()
