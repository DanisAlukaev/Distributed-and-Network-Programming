"""
Lab-02. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

import socket

HOST = '127.0.0.1'
PORT = 65432
ADDRESS = (HOST, PORT)
BUFFER = 100


class NoSuchOperatorError(Exception):
    """
    Error class for cases when symbol is not supported by the application.
    """

    def __init__(self, message="No such operator found."):
        self.message = message
        super().__init__(self.message)


class NonNumericOperandError(Exception):
    """
    Error class for cases when operand is not numeric.
    """

    def __init__(self, message="Operand should be a number."):
        self.message = message
        super().__init__(self.message)


class DivisionByZeroError(Exception):
    """
    Error class for division by zero operations.
    """

    def __init__(self, message="Division by zero"):
        self.message = message
        super().__init__(self.message)


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


def calculate_result(operator, left_operand, right_operand):
    """
    Computes the result for combination of operator, left and right operand.
    Checks whether operator and operands are valid (supported for computation).
    Automatically performs conversion to suitable type.

    :param operator: symbol passed by user at the operator position.
    :param left_operand: symbol passed by user at the left operand position.
    :param right_operand: symbol passed by user at the right operand position.
    :return:
    """
    if not valid_operator(operator):
        raise NoSuchOperatorError(f"No such operator found: {operator}")
    if not is_float(left_operand):
        raise NonNumericOperandError(f"Operand should be numeric: {left_operand}")
    if not is_float(right_operand):
        raise NonNumericOperandError(f"Operand should be numeric: {right_operand}")

    # parse operands
    left_operand, right_operand = float(left_operand), float(right_operand)
    # using dictionary operations compute the result
    result = operations[operator](left_operand, right_operand)

    # convert float with zero after the point to int
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return result


def server():
    """
    Server side of client-server calculator.
    Continually ready to receive command from the client application.
    Determines type of the operation to perform and compute the result.
    If the operation cannot be performed server catches exception and send exception message to client.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(ADDRESS)
            print("Waiting for a new request.")
            while True:
                # receive user command
                message, address = sock.recvfrom(BUFFER)
                message = message.decode()
                print(f"Request from {address}: {message}")
                try:
                    # parse tokens and try to calculate the result
                    operator, left_operand, right_operand = message.split(' ')
                    result = calculate_result(operator, left_operand, right_operand)
                except Exception as e:
                    # set exception message as the result
                    result = e.message if hasattr(e, 'message') else "Unresolved exception occurred."
                print(f"Result: {result}\n")
                # send the result to client
                sock.sendto(str(result).encode(), address)
    except KeyboardInterrupt:
        print("Keyboard interrupt, server is shutting down.")


if __name__ == '__main__':
    server()
