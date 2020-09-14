# Author Martin Pek
# 2CP - TeamEscape - Engineering
# Serial Data logger for Rpi and Arduino

from config import Settings as cfg
import serial
import re
from collections import deque
from datetime import datetime
from time import sleep
import os
import io
import subprocess
import socket
from io import BytesIO




'''
Todo: 
- pass a parameter to run logging without restart??
- detect nonresponsive arduino after a while
- verfiy traffic limits of this, dunno if that is too much traffic potentially

- ~~dump triggered from gamemaster?~~ 



'''
# debug flags and other things that may be modified
debug_mode = False

#

script_dir = os.getcwd()

# --- global const var from the config

# settings import ... really not happy with this... should be a function and json
# is a candidate for a refractoring
# usb_port = cfg["usb_port"]
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


# *** global Vars

header_open = False
setup_open = False
globals_open = False

header_sequence = -1

# *** all the buffers
buffer = deque(maxlen=buffer_lines)
# just for safety precaution, we don't want to buffer overflow in case header tags are missing
header = deque(maxlen=20)
setup = deque(maxlen=20)

socket_process = None
series_no = 0


def write_to_buffers(line):

    if header_open:
        header.append(line)
    if setup_open:
        setup.append(line)
    if globals_open:
        print("globals open WIP")

    buffer.append(line)


def reset_logger_flags():
    global header_open, setup_open, globals_open
    header_open = True
    setup_open = False
    globals_open = False


def generate_log_name():
    date = datetime.now()
    date = date.strftime('%Y-%m-%d__%H_%M')
    return log_prefix + "__" + date + "__s_" + str(series_no) + ".txt"


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
    if re.match(tag_character, line) is not None:
        # print("tagged line found")
        return True
    elif re.match(legacy_character, line) is not None:
        print()
        # print("WIP for backwards compatibility")
    return False

'''
class Arduino:
    def __init__(self, name, s, trigger_state):
        self.name = self.name
        self.socket = self.s
        self.last_response = datetime.now().timestamp()
'''


def filter_keywords(line):
    keyword_found = False
    global header_open, setup_open, globals_open, header_sequence

    for i, keyword in enumerate(header_keywords):
        if re.match(keyword, line) is not None:
            header_open = not bool(i)
            if header_open:
                print("incrementing header_sequence")
                header_sequence += 1
            return

    for i, keyword in enumerate(setup_keywords):
        if re.match(keyword, line) is not None:
            setup_open = not bool(i)
            return

    for i, keyword in enumerate(globals_keywords):
        if re.match(keyword, line) is not None:
            globals_open = not bool(i)
            return

    if re.match(event_call_keyword, line):
        event_call(line)


# expand this if you need multiple events
def event_call(line):
    print("eventcall, WIP")


def monitor(line):

    global header_sequence
    global last_response
    last_response = datetime.now().timestamp()
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


def create_socket_client():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.settimeout(arduino_timeout)
    try:
        s.connect(('127.0.0.1', socket_port))
    except socket.error as msg:
        print('socket not found! \n exiting')
        s.close()
        return False

    while True:
        try:
            line = s.recv(1024)
            monitor(line)
        except socket.timeout:
            global header_sequence
            header_sequence = 1
            monitor('!!! Arduino did get stuck')
            restart_arduino()
            header_sequence = -1
            sleep(1)
            return False


def restart_arduino():
    print('restarting the arduino')
    global socket_process
    if socket_process is not None:
        socket_process.kill()

    socket_process = create_socket_server()


def create_socket_server():
    try:
        os.chdir(script_dir)
        proc = subprocess.Popen(["python3", "usbSocketServer.py"])
    except subprocess.CalledProcessError as e:
        print('failure to launch usb_socket.py')
        print(e)
        exit()
    sleep(1)
    return proc


def main():

    restart_arduino()

    while True:
        create_socket_client()
        reset_logger_flags()
        sleep(0.1)


# allows me to import into test.py without running the main to test functions
if __name__ == "__main__":
    main()

