"""
Lab-06. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import multiprocessing
import threading
import time
import os
import sys
import signal
import zlib

from configs import HOST, REGISTRY_PORT


class Node(multiprocessing.Process):
    """
    Class for p2p node of chord overlay.
    Inherits from the Process class.
    """

    def __init__(self, port):
        super().__init__()
        # set port number
        self.port = port
        # initialize finger table
        self.registry = xmlrpc.client.ServerProxy(f"http://{HOST}:{REGISTRY_PORT}/")
        self.id = -1
        self.m = -1
        # initialize finger table and predecessor
        self.finger_table = {}
        self.predecessor = (-1, -1)
        self.successor = (-1, -1)

        # objects for auxiliary threads
        self.finger_table_updater = None
        self.process_killer = None

        # flag to check whether quit was executed
        self.terminated = False

        # list of files stored in node
        self.filenames = []

        # create RPC object to serve requests
        self.server_obj = SimpleXMLRPCServer((HOST, self.port), logRequests=False)
        self.server_obj.register_function(self.get_finger_table)
        self.server_obj.register_function(self.quit)
        self.server_obj.register_function(self.save_file)
        self.server_obj.register_function(self.get_file)
        self.server_obj.register_function(self.process_chord_changes)

    def run(self):
        # register node in the chord
        self.id, _ = self.registry.register(self.port)
        # get number of node registered in node
        self.m = self.registry.get_m()
        time.sleep(1)
        # populate finger table
        self.finger_table, self.predecessor = self.registry.populate_finger_table(self.id)
        # update successor
        self.successor = list(self.finger_table.items())[0]

        # run auxiliary thread to update finger table
        self.finger_table_updater = threading.Thread(target=self._observe)
        self.finger_table_updater.start()

        # run auxiliary thread to kill the process
        self.process_killer = threading.Thread(target=self._update_finger_table)
        self.process_killer.start()

        # run RPC server
        self.server_obj.serve_forever()

    def _observe(self):
        """
        Method that checks whether the process was terminated from quit.
        """
        while True:
            time.sleep(1e-5)
            if self.terminated:
                os.kill(self.pid, signal.SIGTERM)
                sys.exit()

    def _update_finger_table(self):
        """
        Method that update finger table and predecessor every 1 second.
        """
        while True:
            time.sleep(1)
            self.finger_table, self.predecessor = self.registry.populate_finger_table(self.id)
            self.successor = list(self.finger_table.items())[0]

    def get_finger_table(self):
        """
        Method that return the finger table of the node.

        :return: dictionary with finger table.
        """
        return self.finger_table

    def quit(self):
        """
        Method used by node to quit from the chord.

        :return: (True, success message) if successfully deregiestered, (False, error message) otherwise.
        """
        success, message = self.registry.deregister(self.id)
        if success:
            # update successor's predecessor and transfer filenames to it
            successor_proxy = xmlrpc.client.ServerProxy(f"http://{HOST}:{self.successor[1]}/")
            successor_proxy.process_chord_changes(self.predecessor, self.filenames, False)

            # update predecessor's successor
            predecessor_proxy = xmlrpc.client.ServerProxy(f"http://{HOST}:{self.predecessor[1]}/")
            predecessor_proxy.process_chord_changes(False, False, self.successor)

            self.terminated = True
        return success, message

    def save_file(self, filename):
        """
        Method used to save files in chord.
        Computes hash value of the file name and correspondent id of target node to store it.
        Considers several cases:
        1. target_id belongs to (pred_id, curr_id]
            Saves file in current node.
        2. target_id belongs to (curr_id, succ_id]
            Saves file in successor node. Invokes save_file method of successor.
        3. else
            Searches for farthest node from the current that doesn't overstep current.
            Invokes save_file method of found node.

        :param filename: name of the file.
        :return: (True, success message) if successfully saved, (False, error message) otherwise.
        """

        def generate_set(a, b, m):
            # generate set of values in between a and b considering 2^m entries
            return [*range(a, b + 1)] if a <= b else [*range(a, 2 ** m)] + [*range(0, b + 1)]

        # get hash value for filename
        hash_value = zlib.adler32(filename.encode())
        # calculate id of target node
        target_id = hash_value % 2 ** self.m

        # retrieve predecessor and successor for current node
        predecessor_id, _ = self.predecessor
        successor_id, successor_port = self.successor

        if target_id in generate_set(int(predecessor_id) + 1, int(self.id), self.m):
            # filename should be saved in current node
            if filename not in self.filenames:
                self.filenames.append(filename)
                return True, f'{filename} is saved in Node {self.id}'
            return False, f'{filename} already exists in Node {self.id}'

        if target_id in generate_set(int(self.id) + 1, int(successor_id), self.m):
            # filename should be saved to successor node
            print(f"node {self.id} passed {filename} to node {successor_id}")
            target_proxy = xmlrpc.client.ServerProxy(f"http://{HOST}:{successor_port}/")
            return target_proxy.save_file(filename)

        # find farthest node from the current that doesn't overstep target
        nodes = list(self.finger_table.items())
        # consider the interval between the last and first entries
        if target_id in generate_set(int(nodes[-1][0]), int(nodes[0][0]), self.m):
            print(f"node {self.id} passed {filename} to node {nodes[-1][0]}")
            target_proxy = xmlrpc.client.ServerProxy(f"http://{HOST}:{nodes[-1][1]}/")
            return target_proxy.save_file(filename)

        for idx in range(len(nodes) - 1):
            if target_id in generate_set(int(nodes[idx][0]), int(nodes[idx + 1][0]), self.m):
                print(f"node {self.id} passed {filename} to node {nodes[idx][0]}")
                target_proxy = xmlrpc.client.ServerProxy(f"http://{HOST}:{nodes[idx][1]}/")
                return target_proxy.save_file(filename)

    def get_file(self, filename):
        """
        Method used to check whether file name is in chord.
        Computes hash value of the file name and correspondent id of target node to store it.
        Considers several cases:
        1. target_id belongs to (pred_id, curr_id]
            Requests file in current node.
        2. target_id belongs to (curr_id, succ_id]
            Requests file in successor node. Invokes get_file method of successor.
        3. else
            Searches for farthest node from the current that doesn't overstep current.
            Invokes get_file method of found node.

        :param filename: name of the file.
        :return: (True, success message) if found, (False, error message) otherwise.
        """

        def generate_set(a, b, m):
            # generate set of values in between a and b considering 2^m entries
            return [*range(a, b + 1)] if a <= b else [*range(a, 2 ** m)] + [*range(0, b + 1)]

        # get hash value for filename
        hash_value = zlib.adler32(filename.encode())
        # calculate id of target node
        target_id = hash_value % 2 ** self.m

        # retrieve predecessor and successor for current node
        predecessor_id, _ = self.predecessor
        successor_id, successor_port = self.successor

        if target_id in generate_set(int(predecessor_id) + 1, int(self.id), self.m):
            # filename should be saved in current node
            if filename in self.filenames:
                return True, f'Node {self.id} has {filename}'
            return False, f"Node {self.id} doesn't have {filename}"

        if target_id in generate_set(int(self.id) + 1, int(self.successor[0]), self.m):
            # filename should be saved to successor node
            print(f"node {self.id} passed request to node {successor_id}")
            target_proxy = xmlrpc.client.ServerProxy(f"http://{HOST}:{successor_port}/")
            return target_proxy.get_file(filename)

        # find farthest node from the current that doesn't overstep target
        nodes = list(self.finger_table.items())
        # consider the interval between the last and first entries
        if target_id in generate_set(int(nodes[-1][0]), int(nodes[0][0]), self.m):
            print(f"node {self.id} passed request to node {nodes[-1][0]}")
            target_proxy = xmlrpc.client.ServerProxy(f"http://{HOST}:{nodes[-1][1]}/")
            return target_proxy.get_file(filename)

        for idx in range(len(nodes) - 1):
            if target_id in generate_set(int(nodes[idx][0]), int(nodes[idx + 1][0]), self.m):
                print(f"node {self.id} passed request to node {nodes[idx][0]}")
                target_proxy = xmlrpc.client.ServerProxy(f"http://{HOST}:{nodes[idx][1]}/")
                return target_proxy.get_file(filename)

    def process_chord_changes(self, predecessor, filenames, successor):
        """
        Apply changes in the chord. Invoked to quitted node.

        :param predecessor: tuple of predecessors' id and port.
        :param filenames: list of filename to be moved.
        :param successor: tuple of successors' id and port.
        :return: True if changes applied successfully, False - otherwise.
        """

        try:
            if predecessor:
                self.predecessor = predecessor
            if filenames:
                self.filenames.extend(filenames)
            if successor:
                self.successor = successor
            return True
        except:
            return False
