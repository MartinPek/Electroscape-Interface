# Author Martin Pek
# 2CP - TeamEscape - Engineering
# Serial Data logger for Rpi and Arduino

import json
import re
from re import split, match
from collections import deque
from datetime import datetime as dt
from time import sleep
import os
import io
import subprocess
import socket
from io import BytesIO
from serial_brain.socket_client import SocketClient




'''
Todo: 
- adding of timestamps?
- pass a parameter to run logging without restart??
- detect nonresponsive arduino after a while
- verfiy traffic limits of this, dunno if that is too much traffic potentially

- ~~dump triggered from gamemaster?~~ 

'''

serial_socket = SocketClient('127.0.0.1', 12346)

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
        socket_port = cfg["socket_port"]
        arduino_timeout = cfg["arduino_timeout"]
        brain_tag = cfg["brain_tag"]
except ValueError as e:
    print('failure to read serial_config.json')
    print(e)
    exit()

serial_socket = SocketClient('127.0.0.1', socket_port)
cmd_socket = None
buffer = deque(maxlen=buffer_lines)


class Brain:
    def __init__(self, name):
        self.name = name
        self.header_open = False
        self.setup_open = False
        self.header_sequence = -1
        self.header = deque(maxlen=20)
        self.setup = deque(maxlen=20)
        self.series_no = 0
        self.last_response = dt.now().timestamp()

    def handle_lines(self, line):
        self.__filter_keywords(line)
        if self.header_open:
            self.header.append(line)
        if self.setup_open:
            self.setup.append(line)

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


def generate_log_name():
    date = dt.now()
    date = date.strftime('%Y-%m-%d__%H_%M')
    return log_prefix + "__" + date + "__s_" + str(series_no) + ".txt"


# return the brain object, or creates it if it's a new one
def filter_brain(line):
    if not match(brain_tag, line):
        print("message received without braintag")
        return None
    line_split = split("_", line)

    if len(line_split) > 1:
        for brain in brains:
            current_name = line_split[1]
            if match(brain.name, current_name):
                return brain
        brain = Brain(current_name)
        global brains
        brains.append(brain)
        return brain

    return None


# now needs to incoorperate all brain headers etc
def create_log():
    final_dir = log_path + "/" + log_prefix

    if os.getcwd() is not log_path:
        if not os.path.exists(final_dir):
            os.makedirs(final_dir)
        os.chdir(final_dir)

    name = generate_log_name()
    print("creating " + name + " in folder " + final_dir)

    with io.open(name, "w+", encoding="utf-8") as file:
        file.write("Header\n\n\n")
        for line in header:
            file.write(line + "\n")
        file.write('\n\nsetup\n\n\n')
        for line in setup:
            file.write(line + "\n")
        file.write("\n\nBuffer before crash\n\n\n")
        for line in buffer:
            file.write(line + "\n")
        file.write('\n\n\nEND')
        file.close()

    buffer.clear()
    # we could add this to the next one too
    # write_to_buffers(line)
    setup.clear()
    header.clear()
    global header_sequence, series_no
    header_sequence = 0
    series_no += 1
    reset_logger_flags()


def tag_character_present(line):
    if match(tag_character, line) is not None:
        # print("tagged line found")
        return True
    elif match(legacy_character, line) is not None:
        print()
        # print("WIP for backwards compatibility")
    return False


# WIP
def check_timeouts():
    for brain in brains:
        print(brain)

# depricated now
def monitor(line):

    if type(line) is not str:
        line = line.decode()
    print(line)
    write_to_buffers(line)

    if tag_character_present(line):
        filter_keywords(line)

        if header_sequence > 0:
            print("!restart event detected, triggering Log generation")
            create_log()

    if debug_mode == 2:
        print("header: " + str(header_open) + " | Setup: " + str(setup_open) + " | globals: " + str(globals_open))


def restart_arduino():
    print("WIP till STB is defined, restart wont be serial anymore")


def handle_serial(lines):
    global buffer
    buffer.append(*lines)
    for line in lines:
        brain = filter_brain(line)
        if brain is not None:
            return
        brain.handle_line(line)


def handle_cmds(lines):
    print(lines)


# use
# if type(line) is not str:
#         line = line.decode()
# in case the lines is a bit garbled or contains /*
def run_logger(cmd_port=None):
    global cmd_socket
    if cmd_port is not None:
        cmd_socket = SocketClient('127.0.0.1', cmd_port)

    while True:
        serial_lines = serial_socket.read_buffer()
        if serial_lines is not None:
            continue
        handle_serial(serial_lines)
        if cmd_socket is not None:
            handle_cmds(cmd_socket.read_buffer())
        sleep(0.1)


# allows me to import into test.py without running the main to test functions
if __name__ == "__main__":
    run_logger(12346)

