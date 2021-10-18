"""
Final exam. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

from server import MyQueue
import xmlrpc.client

from configs import HOST, PORT

if __name__ == '__main__':
    queue_proxy = xmlrpc.client.ServerProxy(f"http://{HOST}:{PORT}/",
                                            allow_none=True)
    while True:
        try:
            command = input('Enter command: ').split(' ')

            if command[0] == 'put':
                if len(command) == 2:
                    queue_proxy.put(command[1])
                else:
                    print('Specify argument.')
            elif command[0] == 'pick':
                print(queue_proxy.pick())
            elif command[0] == 'pop':
                print(queue_proxy.pop())
            elif command[0] == 'size':
                print(queue_proxy.size())
            else:
                print(f"Command {command[0]} is not supported.")
        except KeyboardInterrupt:
            print('Closing')
            break
