from glob import glob
import serial
import serial.rs485
from time import sleep

print("v0.3")
baud = 9600

# ports = glob('/dev/serial0')

try:
    ser = serial.Serial(
        port='/dev/serial0',
        baudrate = 9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
    )

    '''
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
    '''

    # ser.rs485_mode = serial.rs485.RS485Settings(...)
except OSError as err:
    if err.errno == 13:
        print("Permission error")
    print(err)
    exit()


print("found serial")
while True:
    ser.write(b'Hello this is 51 Wallie\n')
    line = ser.read(256)
    # line = ser.readline()
    print(line)
    if line:
        try:
            line = line.decode()
            print(line)
        except Exception as e:
            print(e)
            continue
