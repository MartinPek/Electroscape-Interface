# Author Martin Pek
# 2CP - TeamEscape - Engineering

'''

def start_server():
    host = "127.0.0.1"
    port = 8888         # arbitrary non-privileged port

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
        socket_port = cfg["socket_port"]
except ValueError as e:
    print('failure to read serial_config.json')
    print(e)
    exit()

global sock
clients = []


def scan_serial():
    ports = glob.glob('/dev/ttyUSB[0-9]')
    for usb_port in ports:
        try:
            ser = serial.Serial(usb_port, baud)
            print("serial found!")
            return ser
        except (OSError) as e:
            if e.errno == 13:
                print("Permission error")
            print(e)
    print("no Serial plugged in, exiting application")
    exit()


def setup_socket():

    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # this fixes socket.error: [Errno 98] Address already in use
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Socket successfully created")

    # empty IP means its will accept from any connection, we could predefine some later
    # for now its only used on the Pi and GM potentially in the future
    sock.bind(("127.0.0.1", socket_port))

    # maximum of 5 connection allowed
    sock.listen(5)
    # sock.settimeout(5)


def transmit(line):
    line = line.encode()
    for client in clients:
        try:
            client.send(line)
        except socket.error as msg:
            print("Socket transmission Error: {}".format(msg))
            print("a client dropped")
            clients.remove(client)


def read_serial(ser):
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


def handle_serial(ser):

    print("starting to monitor")
    while ser.is_open is not None and ser.is_open:
        line = read_serial(ser)
        if not line and type(line) is bool:
            print("serial connection lost")
            return
        if line:
            transmit(line)


# for now limited to a single client, would like to expand this in the future but for now
# this has to do
def manage_sockets():
    print('waiting for connection on the socket')
    global clients
    while True:
        client, address = sock.accept()
        clients.append(client)
        print('Got connection from', address)
        client.send(b'hello there, you will be listening to the Arduino\n')


def main():
    setup_socket()
    ser = scan_serial()
    thread = Thread(target=manage_sockets)
    thread.start()
    while True:
        handle_serial(ser)


if __name__ == '__main__':
    main()
