"""
Lab-06. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

from xmlrpc.server import SimpleXMLRPCServer
import multiprocessing
import random
from itertools import cycle

from configs import HOST, REGISTRY_PORT


class Registry(multiprocessing.Process):
    """
    Class used to register and deregister the nodes.
    Inherits from the Process class.
    """

    def __init__(self, m):
        super().__init__()

        # dictionary storing ids and corresponding ports for them
        self.node_dict = {}
        # length of identifiers
        self.m = m

        # create RPC object to serve requests
        self.server_obj = SimpleXMLRPCServer((HOST, REGISTRY_PORT), logRequests=False)
        # register functions
        self.server_obj.register_function(self.register)
        self.server_obj.register_function(self.deregister)
        self.server_obj.register_function(self.get_chord_info)
        self.server_obj.register_function(self.populate_finger_table)
        self.server_obj.register_function(self.get_m)

    def run(self):
        # run RPC server
        self.server_obj.serve_forever()

    def register(self, port):
        """
        Method that registers node with the the given port number in the chord.
        Randomly assigns id from the identifier space [0, 2^m-1].
        Invoked by node to register itself in the chord.

        :param port: port number of the node.
        :return: identifier of the node.
        """
        # check if chord is full
        if len(self.node_dict) == 2 ** self.m:
            return -1, 'Chord is full.'

        # set up the random seed
        random.seed(0)
        # generate new identifier for the node
        new_id = random.randint(0, 2 ** self.m - 1)
        # if node with generated id is already in the chord, take another try
        while str(new_id) in self.node_dict:
            new_id = random.randint(0, 2 ** self.m - 1)
        # map node's id to the port (XML-RPC allows to pass dictionary with string keys)
        self.node_dict[str(new_id)] = port

        return new_id, f'Network size is {len(self.node_dict)}.'

    def deregister(self, id):
        """
        Method that deregisters node with the given id from the chord.
        Invoked by node to deregister itself in the chord.

        :param id: node identifier.
        :return: tuple (True, success message) if deregistered successfully, (False, error message) otherwise.
        """
        # delete element from the dictionary and check if there was element with such key
        port = self.node_dict[str(id)]
        success = self.node_dict.pop(str(id), None)
        if not success:
            return False, f'Node {id} with port {port} is not registered'
        return True, f'Node {id} with port {port} was deregistered'

    def get_chord_info(self):
        """
        Method that returns dictionary describing the chord.

        :return: dictionary describing the chord.
        """
        return self.node_dict

    def _successor(self, k):
        """
        Auxiliary method to get successor's identifier for a given id.
        :param k: identifier of node which successor should be found.
        :return: successor's identifier.
        """
        # initialize successor as the maximal id
        successor = 2 ** self.m
        # sort set of identifiers in the chord
        nodes = sorted(map(int, self.node_dict.keys()))
        # iteratively find smallest identifier that greater than the given id
        for id in nodes:
            if successor > id >= k:
                successor = id
        # if successor is not found, set it to the smallest id in the chord
        if successor == 2 ** self.m:
            successor = nodes[0]
        return successor

    def populate_finger_table(self, id):
        """
        Method that generates dictionary of ids and port numbers that the requesting node can communicate and predecessor.

        :param id: identifier of the node.
        :return: finger table dictionary and predecessor of the node.
        """
        finger_table = {}
        for i in range(1, self.m + 1):
            successor = self._successor((id + 2 ** (i - 1)) % 2 ** self.m)
            finger_table[str(successor)] = self.node_dict[str(successor)]

        # create circular list of nodes sorted by id in decreasing order
        nodes_circular = cycle(sorted(self.node_dict.items(), key=lambda x: int(x[0]))[::-1])
        # repeat until received node reached
        for node_id, _ in nodes_circular:
            if node_id == str(id):
                break
        # take next item in sequence that is exactly the predecessor
        predecessor = next(nodes_circular)
        return finger_table, predecessor

    def get_m(self):
        """
        Method that return number of bits allocated for ids of nodes in chord.
        :return: parameter m.
        """
        return self.m
