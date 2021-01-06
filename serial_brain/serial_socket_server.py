# Author Martin Pek
# 2CP - TeamEscape - Engineering

from socketServer import SocketServer
import json
from glob import glob
import serial
from time import sleep

try:
    with open('serial_config.json') as json_file:
        cfg = json.loads(json_file.read())
        baud = cfg["baud"]
        socket_port = cfg["serial_port"]
except ValueError as e:
    print('failure to read serial_config.json')
    print(e)
    exit()


def handle_serial(ser):
    print("starting to monitor")
    while ser is not None and ser.is_open:
        line = read_serial(ser)
        if not line and type(line) is bool:
            print("serial connection lost")
            return
        if line:
            print(line)
            sock.transmit(line)


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


def connect_serial():
    while True:
        ports = glob('/dev/ttyUSB[0-9]') + glob('/dev/serial0')
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


sock = SocketServer(socket_port)


def main():
    while True:
        ser = connect_serial()
        handle_serial(ser)
        # sleep(0.1)


main()



