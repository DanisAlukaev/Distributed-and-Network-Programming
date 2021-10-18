"""
Final exam. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

from xmlrpc.server import SimpleXMLRPCServer
import multiprocessing

from configs import HOST, PORT


class MyQueue(multiprocessing.Process):

    def __init__(self):
        super().__init__()
        # set port number
        self.port = PORT

        self.queue = []

        # create RPC object to serve requests
        self.server_obj = SimpleXMLRPCServer((HOST, self.port),
                                             logRequests=False,
                                             allow_none=True)
        self.server_obj.register_function(self.put)
        self.server_obj.register_function(self.pick)
        self.server_obj.register_function(self.pop)
        self.server_obj.register_function(self.size)

    def run(self):
        # run RPC server
        self.server_obj.serve_forever()

    def put(self, str):
        self.queue.append(str)
        return True

    def pick(self):
        if len(self.queue) == 0:
            return None
        return self.queue[0]

    def pop(self):
        if len(self.queue) == 0:
            return None
        return self.queue.pop(0)

    def size(self):
        return len(self.queue)


if __name__ == '__main__':
    my_queue = MyQueue()
    my_queue.start()
