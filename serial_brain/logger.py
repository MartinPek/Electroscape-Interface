# Author Martin Pek
# 2CP - TeamEscape - Engineering
# Serial Data logger for Rpi and Arduino

import json
from re import split, match
from collections import deque
from datetime import datetime as dt
from time import sleep
import os
import io
try:
    from serial_brain.socket_client import SocketClient
except ModuleNotFoundError:
    from socket_client import SocketClient

try:
    import RPi.GPIO as GPIO
    print("Running on RPi")
    GPIO.setmode(GPIO.BCM)
except (RuntimeError, ModuleNotFoundError):
    print("Running without GPIOs on non Pi ENV / non RPi.GPIO installed machine")
    from fakeRPiGPIO import GPIO
    GPIO.VERBOSE = False
except OSError as e:
    print("sth went terribly wrong with GPIO import \n{}".format(e))
    exit()


'''
Todo: 
- adding of timestamps?
- pass a parameter to run logging without restart??
- detect nonresponsive arduino after a while
- verfiy traffic limits of this, dunno if that is too much traffic potentially

for usage inside the arduinocode simply define brain_name and 
void brainPrint(char* msg) {
    Serial.println(brain_name + ": " + msg);
}

'''

# debug flags and other things that may be modified
debug_mode = False
script_dir = os.getcwd()
brains = []
# --- global const var from the config

try:
    with open('serial_config.json') as json_file:
        cfg = json.loads(json_file.read())
        baud = cfg["baud"]
        log_prefix = cfg["log_prefix"]
        cmd_port = cfg["cmd_port"]

        if debug_mode:
            log_path = os.path.join(script_dir, "testlogs/more logs/more logs")
        else:
            log_path = cfg["log_path_relative"]
            log_path = os.path.join(script_dir, log_path)
        tag_character = cfg["tag_character"]
        legacy_character = cfg["legacy_character"]

        boot_keyword = cfg["boot_keyword"]
        globals_keywords = cfg["globals_keywords"]
        header_keywords = cfg["header_keywords"]
        setup_keywords = cfg["setup_keywords"]
        event_call_keyword = cfg["event_call_keyword"]

        buffer_lines = cfg["buffer_lines"]
        serial_port = cfg["serial_port"]
        arduino_timeout = cfg["arduino_timeout"]
        brain_tag = cfg["brain_tag"]
    with open('../config.json') as json_file:
        cfg = json.loads(json_file.read())
        brains = cfg["Brains"]
except ValueError as e:
    print('failure to read config files')
    print(e)
    exit()


class Brain:
    def __init__(self, name, pin):
        self.name = name
        self.header_open = False
        self.setup_open = False
        self.header_sequence = 0
        self.header = deque(maxlen=20)
        self.setup = deque(maxlen=20)
        self.series_no = 0
        self.last_response = dt.now().timestamp()
        self.pin = pin
        self.__init_brain_gpio()

    def handle_line(self, line):
        print("{} is handling line: {}".format(self.name, line))
        self.__filter_keywords(line)
        if self.header_open:
            self.header.append(line)
        if self.setup_open:
            self.setup.append(line)
        print("header sequence is {}".format(self.header_sequence))
        if self.header_sequence > 0:
            create_log(self.name)
            self.__reset_flags()

    def __reset_flags(self):
        self.header_open = True
        self.setup_open = False
        self.header_sequence = 0
        self.header.clear()
        self.setup.clear()

    def __filter_keywords(self, line):
        for i, keyword in enumerate(header_keywords):
            if match(keyword, line) is not None:
                self.header_open = not bool(i)
                if self.header_open:
                    print("incrementing header_sequence")
                    self.header_sequence += 1
                return

        for i, keyword in enumerate(setup_keywords):
            if match(keyword, line) is not None:
                self.setup_open = not bool(i)
                return

    def __init_brain_gpio(self):
        GPIO.setup(self.pin, GPIO.OUT)


serial_socket = SocketClient('127.0.0.1', serial_port)
if cmd_port:
    cmd_socket = SocketClient('127.0.0.1', cmd_port)
else:
    cmd_port = None
buffer = deque(maxlen=buffer_lines)


def generate_log_name(brain_name):
    date = dt.now()
    date = date.strftime('%Y-%m-%d__%H_%M')
    log_name = log_prefix + "__" + date + "__"
    if brain_name:
        log_name = log_name + brain_name
    log_name = log_name + ".txt"
    return log_name


# now needs to incoorperate all brain headers etc
def create_log(brain_name=""):
    final_dir = log_path + "/" + log_prefix

    if os.getcwd() is not log_path:
        if not os.path.exists(final_dir):
            os.makedirs(final_dir)
        os.chdir(final_dir)

    name = generate_log_name(brain_name)
    print("creating " + name + " in folder " + final_dir)

    with io.open(name, "w+", encoding="utf-8") as file:

        if brain_name:
            file.write("crash has been detected in brain {}\n\n".format(brain_name))
        file.write("setups of all brains:\n")
        global brains
        print("so many brains {}".format(len(brains)))
        for brain in brains:
            file.write("=== Setup of brain {} ===\n".format(brain.name))

            file.write("Header\n")
            for line in brain.header:
                file.write(line + "\n")
            file.write('\nsetup\n')
            for line in brain.setup:
                file.write(line + "\n")

        file.write("\n\nBuffer before crash\n\n\n")
        for line in buffer:
            file.write(line + "\n")
        file.write('\n\n\nEND OF LOG')
        file.close()


# WIP
def check_timeouts():
    now = dt.now().timestamp()
    for brain in brains:
        if now - brain.last_response > arduino_timeout:
            print("brain {} timed out restart is WIP since PINs need TBD".format(brain.name))
        brain.last_response = arduino_timeout


# return the brain object, or creates it if it's a new one
def filter_brain(line):
    if not match(brain_tag, line):
        print("message received without braintag")
        return None
    line_split = split("_", line, maxsplit=1)

    # think this trough, i don't want missed tags
    if len(line_split) > 1:
        splitted = split(":", line_split[1], maxsplit=1)
        current_name = splitted[0]
        if len(splitted) > 1:
            line = splitted[1].strip()
        if not current_name:
            return None

        global brains
        print("filterbrain")
        print(current_name)
        for brain in brains:
            print(brain.name)
            if match(brain.name, current_name):
                brain.handle_line(line)
                return brain
        brain = Brain(current_name)
        brains.append(brain)
        print("\n\n")
        return brain

    return None


def handle_serial(lines):
    global buffer

    '''
    print("\n\n\n buffer content:")
    for line in buffer:
        print(line)
    '''

    for line in lines:
        buffer.append(line)
        print(line)
        if line:
            print("received line {}".format(line))
            filter_brain(line)

# --- fncs to be called via the stb


def user_login(user_name):
    print("userlogin {}".format(user_name))


# move to brain? not really its predefined???
def restart_brain(brain_name):
    print("WIP till STB is defined, restart wont be serial anymore")


# *_ dumps all parameters
def restart_all(*_):
    # Todo: decide on how we reset brains and not log them? have a seperate restartall?
    for brain in brains:
        GPIO.output(brain.pin, True)
    print("resetall cmd")


commands = {
    "!log": create_log,
    "!login": user_login,
    "!reset_all": restart_all,
    "!reset_brain": restart_brain
}


def handle_stb(lines):
    if lines:
        print("received cmd form frontend: {}".format(lines))
        for line in lines:
            print("checking cmd tag with {}".format(line))
            buffer.append(line)
            if match("!", line):
                print("found command tag")
                handle_cmd(line)


def handle_cmd(line):
    print("interpreting command")
    for cmd in commands.keys():
        if match(cmd, line):
            try:
                _, value = split(":", line, 1)
                # remove left whitespace
                value = value.lstrip()
            except ValueError:
                value = line
            commands[cmd](value)


# initializing the brains
for i, brain in enumerate(brains):
    brains[i] = Brain(*brain)


# use
# if type(line) is not str:
#         line = line.decode()
# in case the lines is a bit garbled or contains /*
def run_logger():
    try:
        while True:
            serial_lines = serial_socket.read_buffer()
            if len(serial_lines) > 0:
                print("serial lines {}".format(serial_lines))
                handle_serial(serial_lines)
            if cmd_socket is not None:
                handle_stb(cmd_socket.read_buffer())
    finally:
        GPIO.cleanup()


# allows me to import into test.py without running the main to test functions
if __name__ == "__main__":
    run_logger()

