import socket
from time import sleep
from threading import Thread


class SocketClient:
    def __init__(self, ip, port, timeout=8):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.buffer = []
        thread = Thread(target=self.__run_socket_client)
        thread.start()

    def __connect(self):
        try:
            self.s.connect((self.ip, self.port))
        except socket.error as msg:
            print('socket not found! \n exiting')
            self.s.close()
            return False
        return True

    def __received(self):
        try:
            line = self.s.recv(1024)
            if type(line) is not str:
                line = line.decode()
                if line:
                    # Todo: buffer overflow? mby have a ringbuffer? limited size?
                    self.buffer.append(line)
                    print(line)
            return True
        except socket.timeout:
            return False

    def __run_socket_client(self):
        while True:
            s = socket.socket()
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.settimeout(self.timeout)
            self.s = s
            while True:
                if not self.__connect():
                    break
                while self.__received():
                    pass
                sleep(1)
            
    def read_buffer(self):
        ret = self.buffer
        self.buffer = []
        return ret


if __name__ == "__main__":
    print("not imported")
    SocketClient('127.0.0.1', 12345)


'''
from serial_brain.socket_client import SocketClient
test = SocketClient('127.0.0.1', 12345)

test.read_buffer()
'''