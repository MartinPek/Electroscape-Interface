# Author Martin Pek
# 2CP - TeamEscape - Engineering

'''
Todo:
fringe case where we dont restart the pi with the socket....
OSError: [Errno 98] Address already in use
https://stackoverflow.com/questions/6380057/python-binding-socket-address-already-in-use
'''

import socket
from threading import Thread


class SocketServer:
    def __init__(self, port):
        self.clients = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # this fixes socket.error: [Errno 98] Address already in use
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # empty IP means its will accept from any connection, we could predefine some later
        # for now its only used on the Pi and GM potentially in the future
        self.sock.bind(("127.0.0.1", port))
        # maximum of 5 connection allowed
        self.sock.listen(5)
        # sock.settimeout(5)
        thread = Thread(target=self.__manage_sockets)
        thread.start()

    def __manage_sockets(self):
        print('starting to seek connection on the socket')
        while True:
            client, address = self.sock.accept()
            self.clients.append(client)
            print('Got connection from', address)

    def transmit(self, line):
        line = line.encode()
        for client in self.clients:
            try:
                client.send(line)
            except socket.error as msg:
                print("Socket transmission Error: {}".format(msg))
                print("a client dropped")
                self.clients.remove(client)
