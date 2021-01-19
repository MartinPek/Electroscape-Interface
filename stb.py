# Author Martin Pek
# 2CP - TeamEscape - Engineering

# from random import random
import json
# from datetime import datetime as dt
from serial_brain.socket_client import SocketClient
from serial_brain.socketServer import SocketServer
from pcf8574 import PCF8574
from time import sleep
from threading import Thread

# TODO:
'''
log receiving relay actions aswell
- Except PCF with not for an override
    raise IOError(ffi.errno)
    OSError: 121
    its caused by disconnected or malfunctioning PCF hardware -> 
    link to instructions to ???
- self.sock.bind(("127.0.0.1", port))
    OSError: [Errno 98]
    Address already in use
    either with reset protocol or socket shutdown when script is turned off/crashes
    or timeout?
'''

rpi_env = True

'''
    don't ask, everything on the frontend get smeared into strings
    bool_dict = {"true": True, "false": False}
    bool_convert = {"True": "false", "Talse": "true"}
'''
bool_dict = {"on": True, "off": False}
serial_socket = None
cmd_socket = None
# counter = 0


# if the threading here doesnt work move it to app into the updater thread
def brain_restart_thread(gpio, reset_pins):
    for reset_pin in reset_pins:
        gpio.output(reset_pin, True)
    print("Restarting ...")
    sleep(0.5)
    for reset_pin in reset_pins:
        gpio.output(reset_pin, False)
    print("Done")


class Settings:
    def __init__(self, room_name, serial_limit):
        self.room_name = room_name
        self.is_rpi_env = True
        self.serial_limit = serial_limit


class Relay:

    def __set_frontend_auto(self):
        # since the label is Auto for the checkbox its reverse
        if self.auto:
            self.auto_frontend = "true"
        else:
            self.auto_frontend = "false"

    def set_auto(self, auto):
        self.auto = auto
        self.__set_frontend_auto()

    def __set_frontend_status(self):
        print("setting status for frontend for relay {}".format(self.name))
        if self.status:
            self.status_frontend = "On"
        else:
            self.status_frontend = "Off"

    def set_status(self, status):
        self.status = status
        if self.status:
            self.btn_clr_frontend = "green"
        else:
            self.btn_clr_frontend = "red"
        self.__set_frontend_status()

    def __init__(self, name, active_high, auto, hidden, brain_association, index):
        self.name = name
        self.active_high = active_high
        self.auto = auto
        self.auto_frontend = "true"
        # this just is a function used to set the frontend to the same as backend,
        # just here to init the latter
        self.set_auto(self.auto)
        self.hidden = hidden
        self.brain_association = brain_association
        self.status = False
        # since its going to be a pain in the ass on frontend even converting bools...
        self.btn_clr_frontend = 'green'
        self.set_status(self.status)
        self.index = index
        self.auto_default = self.auto


class Brain:
    def __init__(self, name, relays, brain_no, reset_pin):
        self.name = name
        associated_relays = []
        for relay in relays:
            if relay.brain_association == brain_no + 1:
                associated_relays.append(relay)
        self.associated_relays = associated_relays
        self.reset_pin = reset_pin

    def reset_relay_modes(self):
        for relay in self.associated_relays:
            relay.set_auto(relay.auto_default)


class STB:
    def __init__(self):
        self.updates = []
        self.serial_buffer = ["line1\n", "line2\n", "line3\n"]
        self.serial_updates = []
        self.settings, self.relays, self.brains = self.__load_stb()
        self.GPIO = self.__gpio_init()
        self.pcf_read, self.pcf_write = self.__pcf_init()
        self.user = False
        self.admin_mode = False
        self.update_stb()
        print("stb init done")

    def __load_stb(self):
        try:
            with open('config.json') as json_file:
                cfg = json.loads(json_file.read())
                room_name = cfg["Room_name"]
                relays = cfg["Relays"]
                brains = cfg["Brains"]
                serial_limit = cfg["Serial_line_limit"]
        except ValueError as e:
            print('failure to read config.json')
            print(e)
            exit()

        try:
            with open('serial_brain/serial_config.json') as json_file:
                cfg = json.loads(json_file.read())
                serial_port = cfg["serial_port"]
                cmd_port = cfg["cmd_port"]
        except ValueError as e:
            print('failure to read serial_config.json')
            print(e)
            exit()

        global serial_socket, cmd_socket
        serial_socket = SocketClient('127.0.0.1', serial_port)
        cmd_socket = SocketServer(cmd_port)

        for i, relay in enumerate(relays):
            relays[i] = Relay(*(relay + [i]))

        for i, brain_data in enumerate(brains):
            brain, reset_pin = brain_data
            brains[i] = Brain(brain, relays, i, reset_pin)

        settings = Settings(room_name, serial_limit)
        return settings, relays, brains

    def __pcf_init(self):
        pcf_read = PCF8574(1, 0x38)
        pcf_write = PCF8574(1, 0x3f)
        return pcf_read, pcf_write

    def __gpio_init(self):
        try:
            import RPi.GPIO as GPIO
            print("Running on RPi")
        except (RuntimeError, ModuleNotFoundError):
            print("Running without GPIOs on non Pi ENV / non RPi.GPIO installed machine")
            self.settings.is_rpi_env = False
            # from fakeRPiGPIO import GPIO
            # GPIO.VERBOSE = False
            from GPIOEmulator.EmulatorGUI import GPIO
        except OSError as e:
            print(e)
            print("sth went terribly wrong with GPIO import")
            exit()

        GPIO.setmode(GPIO.BCM)
        for brain in self.brains:
            GPIO.setup(brain.reset_pin, GPIO.OUT, initial=False)
        return GPIO

    def set_override(self, relay_index, value, test):
        # do yourself a favour and dont pass values into html merely JS,
        # converting bools into 3 different languages smeared into json is not fun
        # function only flips existing variable
        relay = self.relays[int(relay_index)]
        relay.set_auto(not relay.auto)
        self.__log_action("User {} has set relay_no {} override to {}".format(
            self.user, relay.index, relay.auto))

    # changes form the frontend applied to the GPIO pins
    def set_relay(self, part_index, status=None, test=None):
        print("set_relay vars {} {} {}".format(part_index, status, test))
        relay = self.relays[part_index]
        # if we pass nothing we flip the relay
        if status is None or type(status) is not bool:
            status = not relay.status
        print("setting relay {} to status {}".format(part_index, status))
        relay.set_status(status)
        self.pcf_write.port[relay.index] = relay.status
        self.__log_action("User {} has flipped {} status {} to {}".format(
            self.user, relay.name, not status, status))
        # takes the cake for the unsexiest variable
        cmd_socket.transmit("!log: {}".format(self.brains[relay.brain_association].name))

    def restart_all_brains(self, *_):
        txt = "\n\nroom has been reset by user {}\n\n".format(self.user)
        print(txt)
        cmd_socket.transmit(txt)

        pins = []
        for brain in self.brains:
            brain.reset_relay_modes()
            pins.append(brain.reset_pin)
        thread = Thread(target=brain_restart_thread, args=(self.GPIO, pins,))
        thread.start()

    def restart_brain(self, brain):
        pins = [brain.reset_pin]
        brain.reset_relay_modes()
        thread = Thread(target=brain_restart_thread, args=(self.GPIO, pins,))
        thread.start()

    def log_brain(self, part_index, *_):
        try:
            brain = self.brains[part_index]
            print("attempting to restart brain {}".format(brain.name))
            cmd_socket.transmit("!log: {}".format(brain.name))
        except IndexError:
            print("Invalid brain selection on restart_brain: {}".format(part_index))

        print()

    # *_ dumps unused variables
    def login(self, *args):
        user = args[1]
        msg = "loggig in user {}".format(user)
        print(msg)
        cmd_socket.transmit("!login: {}".format(user))
        self.user = user

    def __log_action(self, message):
        self.__add_serial_lines([message])
        cmd_socket.transmit(message)

    def set_admin_mode(self, *_):
        self.admin_mode = True

    def logout(self, *_):
        cmd_socket.transmit("!logout: {} ".format(self.user))
        self.user = False
        self.admin_mode = False

    '''
    # question is if we need to create a seperate thread or handle pausing differently
    # need to check likely we need to consider flasks limitations
    def reset_brains(self, brains):
        for brain in brains:
            self.GPIO.output(brain.reset_pin, True)
        
        sleep(0.5)
        for brain in brains:
            self.GPIO.output(brain.reset_pin, False)
    '''

    def __add_serial_lines(self, lines):
        for line in lines:
            # if we have problems with line termination for whatever reason we can edit them here
            self.serial_updates.insert(0, line)
            self.serial_buffer.insert(0, line)
            new_size = min(len(self.serial_buffer), self.settings.serial_limit)
            self.serial_buffer = self.serial_buffer[:new_size]

    # reads and updates the STB and sets/mirrors states
    def update_stb(self):
        for relay_no, relay in enumerate(self.relays):
            # auto = true, manual = false
            if relay.auto:
                new_status = bool(self.pcf_read.port[relay_no])
                if new_status != relay.status:
                    relay.set_status(new_status)
                    relay_msg = "Relay {} has been switched to {} by the brain ".format(relay.name, relay.status)
                    if self.admin_mode or not relay.hidden:
                        self.__log_action(relay_msg)
                    else:
                        cmd_socket.transmit(relay_msg)
                    self.updates.insert(0, [relay_no, relay.status_frontend, relay.btn_clr_frontend])
                self.pcf_write.port[relay_no] = new_status

        # self.__add_serial_lines(["counter is at {}".format(counter)])
        ser_lines = serial_socket.read_buffer()
        if ser_lines is not None:
            ser_lines = reversed(ser_lines)
            self.__add_serial_lines(ser_lines)

    def cleanup(self):
        self.GPIO.cleanup()

# https://www.shanelynn.ie/asynchronous-updates-to-a-webpage-with-flask-and-socket-io/
# https://flask-socketio.readthedocs.io/en/latest/
# following didnt work iirc
# https://realpython.com/flask-by-example-implementing-a-redis-task-queue/


# just here fore testing when running stb.py, usually this is imported
if __name__ == "__main__":
    print("")






