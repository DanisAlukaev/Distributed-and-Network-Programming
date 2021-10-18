"""
Lab-05. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

import sys
from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import os

FILEPATH = 'server_files/'


class DivisionByZeroError(Exception):
    """
    Error class for division by zero operations.
    """

    def __init__(self, message="Division by zero"):
        self.message = message
        super().__init__(self.message)


def server():
    """
    Server side of XML-RPC application.
    Allows to work with file structure:
    - delete files
    - list files
    - save files
    - send files
    Performs evaluating of expressions. Supports operations *, /, -, +, >, <, >=, <=.
    Parses command line arguments: host address and port number.
    Established XML RPC server using the provided information.
    Registers functions send_file, list_files, delete_file, get_file, calculate.
    Serve the incoming connections until Keyboard interrupt.
    """

    def send_file(filename, data):
        """
        Function saving the file with a given name and data.
        Check whether there is a file with the same name.
        Saves the file with received binary data.

        :param filename: name of file.
        :param data: binary data for the file to be saved.
        :return: True if file is saved, False - otherwise.
        """
        # check if there is file with the same name
        if os.path.isfile(FILEPATH + filename):
            print(f"{filename} not saved")
            return False

        # save the file
        with open(FILEPATH + filename, "wb") as file:
            file.write(data.data)
        print(f"{filename} saved")
        return True

    def list_files():
        # Returns list of filenames in the server directory.
        return os.listdir(FILEPATH)

    def delete_file(filename):
        """
        Function removing the file with a given name.
        Check whether there is a file with the same name.
        Deletes the file if found.

        :param filename: name of file.
        :return: True if file is deleted, False - otherwise.
        """
        # check whether file is in server directory
        if not os.path.isfile(FILEPATH + filename):
            print(f"{filename} not deleted")
            return False
        # remove the file
        os.remove(FILEPATH + filename)
        print(f"{filename} deleted")
        return True

    def get_file(filename):
        """
        Function returning the binary data of file to the client.
        Check whether there is a file with the same name.
        Reads and returns the file with received name.

        :param filename: name of file.
        :return: True if file is sent, False - otherwise
        """
        # check if file exists
        if not os.path.isfile(FILEPATH + filename):
            print(f"No such file: {filename}")
            return False
        # read the file and send it client
        with open(FILEPATH + filename, "rb") as file:
            binary = xmlrpc.client.Binary(file.read())
        print(f"File send: {filename}")
        return binary

    def calculate(expression):
        """
        Function evaluating expression in the form <operator> <left operand> <right operand>.
        Splits up the expression in the tokens and checks whether there are three of them.
        Check if the operator is supported and operands are numeric.
        For simplicity there is used dictionary to use for computations.
        Tokens passed to the correspondent function in dictionary.
        Operation of division is safe and check whether denominator is zero.
        To inform the client about problem with command, function sends the error message if problem occurred.

        :param expression: string in the form <operator> <left operand> <right operand>.
        :return: <True/False>, <None/Error>
        """

        def safe_division(a, b):
            """
            Performs division of two numbers.
            Raise exception if division is by zero.
            :param a: left operand.
            :param b: right operand.
            :return: result of division.
            """
            if b != 0:
                return a / b
            raise DivisionByZeroError()

        def valid_operator(operator):
            """
            Checks whether the symbol is supported by application.
            :param operator: symbol passed by user at the operator position.
            :return: True if string is valid operator, False - otherwise.
            """
            if operator in ['*', '/', '-', '+', '>', '<', '>=', '<=']:
                return True
            return False

        def is_float(operand):
            """
            Checks whether string represents number with floating point.
            Performs the conversion of symbol to float and catch the exception if necessary.
            :param operand: symbol passed by user at the operand position.
            :return: True if string represents float, False - otherwise.
            """
            try:
                float(operand)
                return True
            except:
                return False

        tokens = expression.split(" ")
        if len(tokens) != 3:
            return False, "Wrong expression"

        # parse expression
        operator, left_operand, right_operand = tokens
        if not valid_operator(operator) or not is_float(left_operand) or not is_float(right_operand):
            print(f"{expression} -- not done")
            return False, "Wrong expression"

        # dictionary with operators as keys and functions as values
        # simplifies the program architecture
        operations = {
            '*': lambda a, b: a * b,
            '/': safe_division,
            '-': lambda a, b: a - b,
            '+': lambda a, b: a + b,
            '>': lambda a, b: a > b,
            '<': lambda a, b: a < b,
            '>=': lambda a, b: a >= b,
            '<=': lambda a, b: a <= b,
        }

        # parse operands
        left_operand, right_operand = float(left_operand), float(right_operand)
        # using dictionary operations compute the result
        try:
            result = operations[operator](left_operand, right_operand)
        except DivisionByZeroError:
            print(f"{expression} -- not done")
            return False, "Division by zero"
        except Exception as e:
            print(f"{expression} -- not done")
            return False, str(e)

        # convert float with zero after the point to int
        if isinstance(result, float) and result.is_integer():
            result = int(result)

        print(f"{expression} -- done")
        return True, result

    # parse command line argument
    if len(sys.argv) != 3:
        print("Usage example: python server.py <address> <port>")
        return
    host = sys.argv[1]
    port = int(sys.argv[-1])

    # catch Keyboard Interrupt exception
    try:
        with SimpleXMLRPCServer((host, port), logRequests=False) as server_obj:
            # register functions that respond to XML-RPC requests
            server_obj.register_introspection_functions()
            server_obj.register_function(send_file)
            server_obj.register_function(list_files)
            server_obj.register_function(delete_file)
            server_obj.register_function(get_file)
            server_obj.register_function(calculate)
            # run server
            server_obj.serve_forever()
    except KeyboardInterrupt:
        print("Server is stopping")


if __name__ == "__main__":
    server()
