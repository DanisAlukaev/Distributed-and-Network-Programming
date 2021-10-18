"""
Lab-06. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

import sys
import xmlrpc.client

from configs import HOST, REGISTRY_PORT
from registry import Registry
from node import Node


def parse_arguments():
    """
    Function used to parse and validate command line arguments.
    :return: length of identifiers in chord, range of port numbers.
    """
    args = sys.argv[1:]

    if len(args) != 3:
        raise Exception('Main program accepts three arguments: m, first_port, last_port.')

    try:
        m, first_port, last_port = list(map(int, args))
    except:
        raise Exception('Command line arguments should be numeric.')

    if first_port > last_port:
        raise Exception('First port should be less than or equal to the second port.')

    if REGISTRY_PORT in range(first_port, last_port + 1):
        raise Exception(f'Port {REGISTRY_PORT} is allocated for registry.')

    return m, first_port, last_port


def keys_int(dict):
    # convert keys to int (XML-RPC prohibits numeric keys in dictionaries)
    return {int(k): v for k, v in dict.items()}


if __name__ == '__main__':
    # parse command line arguments
    try:
        result = parse_arguments()
    except Exception as e:
        print(e)
        sys.exit()
    m, first_port, last_port = result

    # create and run Registry object
    registry = Registry(m)
    registry.start()

    # create and start Node processes
    nodes = [Node(port) for port in range(first_port, last_port + 1)]
    [node.start() for node in nodes]

    print(f'Registry and {m} nodes are created.')
    # create RPC proxies for registry and nodes
    node_proxies = {port: xmlrpc.client.ServerProxy(f"http://{HOST}:{port}/") for port in
                    range(first_port, last_port + 1)}
    registry_proxy = xmlrpc.client.ServerProxy(f"http://{HOST}:{REGISTRY_PORT}/")

    while True:
        try:
            command = input('> ').split(' ')
            if command[0] == 'get_chord_info':
                print(keys_int(registry_proxy.get_chord_info()))
            elif command[0] == 'get_finger_table':
                chord = registry_proxy.get_chord_info()
                port_node = int(command[1])

                if port_node in chord.values():
                    print(keys_int(node_proxies[port_node].get_finger_table()))
                    continue

                print(f'There is no node with id {port_node} in the chord.')
            elif command[0] == 'quit':
                chord = registry_proxy.get_chord_info()
                port_node = int(command[1])

                if port_node in chord.values():
                    success, message = node_proxies[int(command[1])].quit()
                    print(message)

                    if success:
                        chord = registry_proxy.get_chord_info()
                        # update finger tables for each node that is left
                        for port_node in chord.values():
                            success, message = node_proxies[port_node].update_finger_table()
                            # if the error occurred
                            if not success:
                                print(message)
                    continue

                print(f'There is no node with port {port_node} in the chord.')
            else:
                print(f"Command {command[0]} is not supported.")
        except KeyboardInterrupt:
            print('Keyboard Interrupt: stopping main.py.')
            break

    # kill processes by calling join for each of them
    registry.terminate()
    [node.terminate() for node in nodes]
