"""
Lab-07. Distributed and Network Programming.
Author: Danis Alukaev
Email: d.alukaev@innopolis.university
Group:  B19-DS-01
"""

import xmlrpc.client


def client():
    try:
        proxy = None
        print("The client starts")
        while True:
            command = input("> ").split(' ')
            keyword = command[0]

            if keyword == 'connect':
                # check if the command has desired number of arguments
                if len(command) != 3:
                    print("Use format: connect <address> <port>")
                    continue
                address, port = command[1:]
                proxy = xmlrpc.client.ServerProxy(f"http://{address}:{port}/",
                                                  allow_none=True)

            elif keyword == 'getleader':
                # check if the command has desired number of arguments
                if len(command) != 1:
                    print("Use format: getleader")
                    continue
                if proxy:
                    id, address = proxy.get_leader()
                    print(f"{id} {address}")

            elif keyword == 'suspend':
                # check if the command has desired number of arguments
                if len(command) != 2:
                    print("Use format: suspend <period>'")
                    continue
                if proxy:
                    proxy.suspend(int(command[1]))

            elif keyword == 'quit':
                print("The client ends")
                break

    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    client()
