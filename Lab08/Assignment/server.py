"""
Lab-07. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

import datetime
import time
from xmlrpc.server import SimpleXMLRPCServer
import multiprocessing
import xmlrpc.client
import threading
from multiprocessing.pool import ThreadPool
import random
import sys
import os
from enum import Enum
from datetime import datetime as dt


class State(Enum):
    FOLLOWER = 0
    CANDIDATE = 1
    LEADER = 2


class Server(multiprocessing.Process):
    """
    Class representing node in RAFT protocol.
    Requires config.conf file in home directory of project.

    Comprises three threads for
    a. Accepting requests and resetting timer
    b. Sending requests
    c. Changing state if triggered
    """

    def __init__(self, server_id):
        super().__init__()
        self.id = server_id

        self.config = {}
        self.proxies = []
        self.host = None
        self.port = -1

        self.term = -1
        self.timeout = -1
        self.votes = []
        self.update_timer = False

        self.state = None
        self.voted = False
        self.leader = -1

        self.blocked = False

        self.rpc_server_thread = None
        self.rpc_client_thread = None
        self.timer_trigger_thread = None

    def __load_config(self):
        """
        Method loading information about nodes using RAFT protocol.
        Requires config.conf file in home directory.
        """
        # check if file exists in home directory
        path = './config.conf'
        if not os.path.isfile(path):
            print("Config file not found.\nTerminating node...\n")
            sys.exit()

        # dictionary representing network
        config = {}
        with open(path, 'r') as config_file:
            # treat each line in config file
            for line in config_file:
                # create new entry with id as a key and address, port as value
                node_id, node_address, node_port = line.split()
                config[int(node_id)] = {
                    'address': node_address,
                    'port': int(node_port)
                }
        # save config dictionary
        self.config = config

    def __bind_node(self):
        """
        Method initializing object as server using XML-RPC.
        Registers public methods of class for remote usage.
        :return:
        """
        # set address and port of node
        metadata = self.config[self.id]
        self.host = metadata['address']
        self.port = metadata['port']

        # create RPC object to serve requests
        self.server_obj = SimpleXMLRPCServer((self.host, self.port),
                                             logRequests=False,
                                             allow_none=True)
        self.server_obj.register_function(self.request_vote)
        self.server_obj.register_function(self.append_entries)
        self.server_obj.register_function(self.get_leader)
        self.server_obj.register_function(self.suspend)
        print(f"Server is started at {self.host}:{self.port}")

    def __get_proxies(self):
        """
        Method generating set of proxies to other nodes.
        """
        for node_id, metadata in self.config.items():
            if node_id == self.id:
                continue
            host, port = metadata['address'], metadata['port']
            new_proxy = xmlrpc.client.ServerProxy(f"http://{host}:{port}/",
                                                  allow_none=True)
            self.proxies.append(new_proxy)

    def __startup(self):
        """
        Method performing actions of startup stage, i.e., setting term number,
        timer, and binding node to address and port.
        :return:
        """
        self.__load_config()
        self.term = 0
        self.timeout = random.randint(150, 300)
        self.__bind_node()
        self.__get_proxies()
        self.state = State.FOLLOWER

    def run(self):
        # initialise all components
        self.__startup()

        # initialize and run threads
        self.rpc_server_thread = threading.Thread(target=self.__rpc_server)
        self.rpc_client_thread = threading.Thread(target=self.__rpc_client)
        self.timer_trigger_thread = threading.Thread(
            target=self.__trigger_timer)

        print(f"I am follower. Term: {self.term}")
        self.rpc_server_thread.start()
        self.rpc_client_thread.start()
        self.timer_trigger_thread.start()

    def __rpc_server(self):
        """
        Method accepting requests from other nodes.
        Performs in endless loop. Can be blocked if client used suspend
        command.
        """
        while True:
            if self.blocked:
                continue
            self.server_obj.handle_request()

    def __rpc_client(self):
        """
        Method sending heartbeat messages to each node if the current server is
        leader. Performs in endless loop. Can be blocked if client used suspend
        command.
        """
        while True:
            if self.blocked:
                continue

            # leader behaviour
            if self.state == State.LEADER:
                # send heartbeat messages to each node
                heartbeat_threads = []
                for proxy in self.proxies:
                    proxy_thread = threading.Thread(
                        target=self.__heartbeat_node, args=(proxy,))
                    heartbeat_threads.append(proxy_thread)
                [thread.start() for thread in heartbeat_threads]
                [thread.join() for thread in heartbeat_threads]
                time.sleep(0.05)

    def __trigger_timer(self):
        """
        Method checking that the timeout ended since the last accepted message.
        Implements follower and candidate logic.
        Performing in endless loop. Can be blocked if client used suspend
        command.
        """
        timestamp = dt.now()
        while True:
            if self.blocked:
                continue

            # check if timer should be updated
            if self.update_timer:
                timestamp = dt.now()
                self.update_timer = False

            # check if timer is up
            elif (dt.now() - timestamp).total_seconds() * 1000 > self.timeout:
                if self.state == State.FOLLOWER:
                    # follower behaviour
                    self.state = State.CANDIDATE
                    print("The leader is dead")
                    print(f"I am candidate. Term: {self.term}")
                    # start election
                    self.term += 1
                    self.votes = []

                    # send voting messages to each node
                    self.voted = True
                    self.votes.append(True)
                    election_threads = []
                    for proxy in self.proxies:
                        thread_proxy = threading.Thread(
                            target=self.__call_vote,
                            args=(proxy,))
                        election_threads.append(thread_proxy)
                    [thread.start() for thread in election_threads]

                elif self.state == State.CANDIDATE:
                    # candidate behaviour
                    print("Votes received")
                    # compute the results of voting
                    agree = self.votes.count(True) + 1
                    disagree = self.votes.count(False)
                    if self.state == State.CANDIDATE and agree > disagree:
                        self.update_timer = True
                        self.state = State.LEADER
                        print(f"I am leader. Term: {self.term}")
                    else:
                        timestamp = dt.now()
                        self.state = State.FOLLOWER
                        self.timeout = random.randint(150, 300)
                        print(f"I am follower. Term: {self.term}")

                else:
                    # leader behaviour
                    self.update_timer = True

    def __heartbeat_node(self, proxy):
        """
        Method-worker performing rpc of append_entries method over proxy.
        :param proxy: proxy XML-RPC object.
        :return: success.
        """
        if self.blocked:
            return
        try:
            term, success = proxy.append_entries(self.term, self.id)
        except:
            return
        if term > self.term:
            self.term = term
            self.state = State.FOLLOWER
            print(f"I am follower. Term: {self.term}")
        return success

    def __call_vote(self, proxy):
        """
        Method-worker performing rpc of request_vote method over proxy.
        :param proxy: proxy XML-RPC object.
        :return: result of voting.
        """
        try:
            term, success = proxy.request_vote(self.term, self.id)
        except:
            return
        if term > self.term:
            self.term = term
            self.state = State.FOLLOWER
            print(f"I am follower. Term: {self.term}")
        self.votes.append(success)

    def request_vote(self, term, candidate_id):
        """
        Method publicly available through RPC proxy. Intended to be used by
        Candidate during elections to collect votes.

        :param term: term of candidate server.
        :param candidate_id: id of candidate server.
        :return: node's term and the result of voting.
        """
        if self.blocked:
            return

        # update timer
        self.update_timer = True
        if term > self.term:
            # update term
            self.term = term
            self.voted = False
        # check first condition
        result = self.__decide_vote(term, candidate_id)
        return self.term, result

    def __decide_vote(self, term, candidate_id):
        """
        Implementation of first condition from specification.
        Checks whether terms are equal and node didn't vote in this term yet.

        :param term: term of candidate server.
        :param candidate_id: id of candidate server.
        :return: result of voting.
        """
        if self.term == term and not self.voted:
            self.voted = True
            print(f"Voted for node {candidate_id}")
            # change status of Candidate and Leader servers to Follower
            self.state = State.FOLLOWER
            self.leader = candidate_id
            return True
        return False

    def append_entries(self, term, leader_id):
        """
        Method accepting heartbeat messages from the leader.
        :param term: term of leader server.
        :param leader_id: id of leader server.
        :return: term of current server, success of accept.
        """
        if self.blocked:
            return

        # update the timer
        self.update_timer = True
        success = True if term >= self.term else False
        if success:
            if self.state != State.FOLLOWER:
                print(f"I am follower. Term: {self.term}")
            self.state = State.FOLLOWER
            self.leader = leader_id
        return self.term, success

    def get_leader(self):
        """
        Method returning the leader node's id and its address.
        """
        if self.blocked:
            return

        print("Command from client: getleader")
        leader_id = self.leader if self.state != State.LEADER else self.id
        if leader_id != -1:
            metadata = self.config[leader_id]
            address = f"{metadata['address']}:{metadata['port']}"
            print(f"{leader_id} {address}")
            return leader_id, address

    def suspend(self, period):
        """
        Method blocking the execution of all threads of server process for a
        given number of seconds.

        :param period: time of suspending, in seconds.
        """
        if self.blocked:
            return

        print(f"Command from client: suspend {period}")
        self.blocked = True
        print(f"Sleeping for {period} seconds.")
        time.sleep(period)
        self.blocked = False
        return True


if __name__ == '__main__':
    # check formatting of command
    if len(sys.argv) != 2:
        print("Use format: python server.py <id>")
    try:
        arg_id = int(sys.argv[-1])
    except:
        print("Parameter id should be numeric.")
        sys.exit()

    node = Server(arg_id)
    try:
        node.start()
    except KeyboardInterrupt:
        print("Server ends")
