"""
Lab-06. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import multiprocessing
import time

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
        # initialize finger table
        self.finger_table = {}

        # create RPC object to serve requests
        self.server_obj = SimpleXMLRPCServer((HOST, self.port), logRequests=False)
        self.server_obj.register_function(self.get_finger_table)
        self.server_obj.register_function(self.quit)
        self.server_obj.register_function(self.update_finger_table)

    def run(self):
        # register node in the chord
        self.id, _ = self.registry.register(self.port)
        time.sleep(1)
        # populate finger table
        self.finger_table = self.registry.populate_finger_table(self.id)
        # run RPC server
        self.server_obj.serve_forever()

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
            self.close()
        return success, message

    def update_finger_table(self):
        """
        Method used to rebuild finger table for node.
        Invoked from the main.

        :return: (True, success message) if successfully updated, (False, error message) otherwise.
        """
        try:
            self.finger_table = self.registry.populate_finger_table(self.id)
        except:
            return False, f'Unable to update finger table for node {self.id}.'
        return True, f'Successfully updated finger table for node {self.id}.'
