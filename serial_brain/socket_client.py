import socket
from time import sleep


class SocketClient:
    def __init__(self, ip, port, timeout=8):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.buffer = []
        self.__run_socket_client()

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
            # Todo: buffer overflow? mby have a ringbuffer? limited size?
            self.buffer.append(line)
            print(line)
            return True
        except socket.timeout:
            return False

    def __run_socket_client(self):
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(self.timeout)
        self.s = s
        while True:
            if self.__connect():
                while self.__received():
                    pass
            sleep(1)
            
    def read_buffer(self):
        return self.buffer


if __name__ == "__main__":
    SocketClient('127.0.0.1', 12345)
