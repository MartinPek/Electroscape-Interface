# Author Martin Pek
# 2CP - TeamEscape - Engineering

# Controls the relay that has been connected over PCF8574 (I2C) to the RPi

from pcf8574 import PCF8574

read_address = 0x38
write_address = 0x3f

# port is 1 for any but very first models of RPi
pcf_read = PCF8574(1, read_address)
pcf_write = PCF8574(1, write_address)


def main():
    print(pcf_read.port)
    print(pcf_write.port)
    for i in range(8):
        print(i)
        pcf_write.port[i] = False

    print(pcf_read.port)
    print(pcf_write.port)

    for i in range(8):
        print(i)
        pcf_write.port[i] = True

    print(pcf_read.port)
    print(pcf_write.port)


main()





