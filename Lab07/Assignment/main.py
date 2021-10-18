"""
Lab-06. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

import sys
import xmlrpc.client
import zlib

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


def get_str_identifier(str, m):
    # get hash value for filename
    hash_value = zlib.adler32(str.encode())
    # calculate id of target node
    return hash_value % 2 ** m


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
                if len(command) != 2:
                    print('Specify the port number of node which finger table requested.')

                port_node = int(command[1])
                chord = registry_proxy.get_chord_info()

                if port_node in chord.values():
                    print(keys_int(node_proxies[port_node].get_finger_table()))
                    continue

                print(f'There is no node with id {port_node} in the chord.')
            elif command[0] == 'quit':
                if len(command) != 2:
                    print('Specify the port number of node which finger table requested.')

                chord = registry_proxy.get_chord_info()
                port_node = int(command[1])

                if port_node in chord.values():
                    print(node_proxies[port_node].quit())
                    continue

                """
                I cannot understand for what case message '(False, “Node 6 with port 5000 isn’t part of the network”), 
                if the node exists, but not a part of the system.' stands for. In the problem statement in description
                of quit() function it's clearly stated that the Node firstly invoke deregister function, and then shuts 
                down. This phrase has no other meaning than to terminate the process or thread.
                So the message ruins logic of the application, it literally says that we need to keep track of nodes 
                that were in the chord and don't delete them.
                Therefore, I think that this message is not suitable and should be removed from the specification.                
                """

                error = False, f"Node with {port_node} isn't available."
                print(error)

            elif command[0] == 'save':
                if len(command) != 3:
                    print('Specify the port number of node and filename.')

                chord = registry_proxy.get_chord_info()
                m = len(chord.values())
                port_node = int(command[1])
                filename = command[2]

                print(f"{filename} has identifier {get_str_identifier(filename, m)}")

                if port_node in chord.values():
                    print(node_proxies[port_node].save_file(filename))
                    continue

            elif command[0] == 'get':
                if len(command) != 3:
                    print('Specify the port number of node and filename.')

                chord = registry_proxy.get_chord_info()
                port_node = int(command[1])
                filename = command[2]
                m = len(chord.values())

                print(f"{filename} has identifier {get_str_identifier(filename, m)}")

                if port_node in chord.values():
                    print(node_proxies[port_node].get_file(filename))
                    continue

            else:
                print(f"Command {command[0]} is not supported.")
        except KeyboardInterrupt:
            print('Keyboard Interrupt: stopping main.py.')
            break

    # kill processes by calling join for each of them
    registry.terminate()
    [node.terminate() for node in nodes]
