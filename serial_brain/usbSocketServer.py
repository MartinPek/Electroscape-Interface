# Author Martin Pek
# 2CP - TeamEscape - Engineering

'''
Todo:
make this importable and useable by the stb.py
fringe case where we dont restart the pi with the socket....
OSError: [Errno 98] Address already in use
https://stackoverflow.com/questions/6380057/python-binding-socket-address-already-in-use
'''

import socket
from time import sleep
import json
import glob
import serial
from threading import Thread

try:
    with open('serial_config.json') as json_file:
        cfg = json.loads(json_file.read())
        baud = cfg["baud"]
        socket_port = cfg["serial_port"]
except ValueError as e:
    print('failure to read serial_config.json')
    print(e)
    exit()

global sock
clients = []


class SocketServer:
    def __init__(self, port):
        self.clients = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # this fixes socket.error: [Errno 98] Address already in use
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # empty IP means its will accept from any connection, we could predefine some later
        # for now its only used on the Pi and GM potentially in the future
        self.sock.bind(("127.0.0.1", socket_port))
        # maximum of 5 connection allowed
        self.sock.listen(5)
        # sock.settimeout(5)
        thread = Thread(target=self.__manage_sockets)
        thread.start()
        self.__main()

    def __connect_serial(self):
        while True:
            ports = glob.glob('/dev/ttyUSB[0-9]')
            for usb_port in ports:
                try:
                    ser = serial.Serial(usb_port, baud)
                    print("serial found!")
                    return ser
                except OSError as err:
                    if err.errno == 13:
                        print("Permission error")
                    print(err)
            print("no serial found, checking again")
            sleep(0.5)

    def __manage_sockets(self):
        print('starting to seek connection on the socket')
        while True:
            client, address = self.sock.accept()
            self.clients.append(client)
            print('Got connection from', address)
            client.send(b'hello there, you will be listening to the Arduino\n')

    def __transmit(self, line):
        line = line.encode()
        for client in self.clients:
            try:
                client.send(line)
            except socket.error as msg:
                print("Socket transmission Error: {}".format(msg))
                print("a client dropped")
                self.clients.remove(client)

    def __handle_serial(self, ser):
        print("starting to monitor")
        while ser is not None and ser.is_open:
            line = self.__read_serial(ser)
            if not line and type(line) is bool:
                print("serial connection lost")
                return
            if line:
                self.__transmit(line)

    def __read_serial(self, ser):
        try:
            line = str(ser.readline())[2:][:-5]
            return line
        except ValueError as e:
            print("ValueError")
            print(e)
            return False
        except Exception as e:
            print("unexpected exception")
            print(e)
            ser.close()
            return False

    def __main(self):
        # this loops back when the serial connection breaks, so in case of a disconnect it reconnects
        while True:
            ser = self.__connect_serial()
            self.__handle_serial(ser)


if __name__ == '__main__':
    SocketServer(socket_port)
