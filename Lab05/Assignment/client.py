"""
Lab-05. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

import xmlrpc.client
import sys
import os

FILEPATH = 'client_files/'


def client():
    """
    Client side of XML-RPC application.
    Allows to perform remote procedure call on the server machine.
    Change its file structure:
    - delete files
    - list files
    - save files
    - send files
    Evaluate expressions.
    Parses command line arguments: host address and port number.
    Connects to XML RPC server using the provided information.
    Accepts commands from the user. Checks whether the command is valid.
    Quits if the command is 'quit' or after Keyboard Interrupt.
    """

    def send_file(filename):
        """
        Function sending file with a given name to the client.
        Checks if the file with given name exists.
        Opens the file in binary format.
        Sends content to the client.
        Checks whether it was saved.
        Returns False, error message if problem occurred.

        :param filename: name of file.
        :return: <True/False>, <None/error>
        """
        # check if file exists
        if not os.path.isfile(FILEPATH + filename):
            return False, "No such file"
        # open the file in binary format
        with open(FILEPATH + filename, "rb") as file:
            binary = xmlrpc.client.Binary(file.read())
        # send the binary data
        success = proxy.send_file(filename, binary)
        # check if file was saved
        if not success:
            return False, "File already exists"
        return True, None

    def list_files(arguments):
        """
        Function printing filenames in server directory.
        Accepts list of file from the server.
        Prints name of each file on the new line.
        """
        files = proxy.list_files()
        for file in files:
            print(file)
        return True, None

    def delete_file(filename):
        """
        Function deleting file from server directory by name.
        Invokes function deleting file on the server side.
        Returns False, error message if problem occurred.

        :param filename: name of file.
        :return: <True/False>, <None/error>
        """
        # pass filename to the server
        success = proxy.delete_file(filename)
        # check if deleted successfully
        if not success:
            return False, "No such file"
        return True, None

    def get_file(arguments):
        """
        Function saving file from server with a given name.
        Invokes method to get file.
        Check if the file with given name exists in server directory.
        Check if file already exists in client directory.
        Save the received binary data as file.

        :param arguments: filename, new filename (optional).
        :return: <True/False>, <None/error>
        """
        # parse file name
        filename = arguments[0]
        # get the data from server
        binary = proxy.get_file(filename)

        # if False received return error message
        if not binary:
            return False, "No such file"

        # if name to save file specified use it
        if len(arguments) == 2:
            filename = arguments[1]
        # compose path to file
        filename = FILEPATH + filename
        # check if file exists
        if os.path.isfile(filename):
            return False, "File already exists"
        # save the file
        with open(filename, "wb") as file:
            file.write(binary.data)
        return True, None

    def calculate(arguments):
        """
        Function receiving the result of evaluation of expression.

        :param arguments: expression to be evaluated.
        :return: <True/False>, <result/error>
        """
        success, misc = proxy.calculate(arguments)
        if success:
            print(misc)
            return True, None
        return False, misc

    # parse command line argument
    if len(sys.argv) != 3:
        print("Usage example: python client.py <address> <port>")
        return
    host_server = sys.argv[1]
    port_server = int(sys.argv[-1])

    # create proxy object
    proxy = xmlrpc.client.ServerProxy(f"http://{host_server}:{port_server}/")
    # define set of operations supported by server
    methods = {
        'send': send_file,
        'list': list_files,
        'delete': delete_file,
        'get': get_file,
        'calc': calculate
    }
    # define how to parse the line for different methods
    treat_arguments = {
        'send': lambda s: s.replace("send ", ""),
        'list': lambda s: s.replace("list ", ""),
        'delete': lambda s: s.replace("delete ", ""),
        'get': lambda s: s.replace("get ", "").split(" "),
        'calc': lambda s: s.replace("calc ", "")
    }

    while True:
        # accept commands from the prompt until the KeyboardInterrupt or 'quit' message
        try:
            command = input("\nEnter the command:\n> ")
            operation = command.split(" ")[0]

            # check if client wants to quit
            if operation == 'quit':
                print("Client is stopping")
                break

            # validate the command
            if operation not in methods:
                print("Not completed\nWrong command")
                continue

            # perform the command
            success, error = methods[operation](treat_arguments[operation](command))
            # print the auxiliary information
            if success:
                print("Completed")
                continue
            print(f"Not completed\n{error}")

        except KeyboardInterrupt:
            print("Client is stopping")
            break


if __name__ == "__main__":
    client()
