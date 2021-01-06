# Author Martin Pek

# Flask examples
# https://github.com/greyli/flask-examples
# https://www.tutorialspoint.com/flask/flask_environment.htm
# https://html.developreference.com/article/12618302/CSS+Background+Images+with+Flask


# basics on get and post
# https://stackoverflow.com/questions/10434599/get-the-data-received-in-a-flask-request

# ## doing parallel threads to update the STB data on the frontend:

# Asyncio is not yet supported by flask
# gap between 3.6 and 3.7 versions, their examples are based on the latter, may use it for future prohects
# as it needs to be ironed out and established

# socketio for JS websockets, i don't need another language... can i run socketio with a python script being called?

# threading package seems the most promising, its also a fairly easy module I used before instead of asnycio
# https://stackoverflow.com/questions/14384739/how-can-i-add-a-background-thread-to-flask

# flaskappsheduler... well it let me down on jobs example out of their repo being borked already,
# however its native to flask mby try backgroundsheduler
# https://github.com/viniciuschiele/flask-apscheduler


'''
TODO:

Questions:
Where to take the starttime from for CSV?

adjust timeouts for logger, mby ping here?

ImportError: cannot import name 'dump_csp_header' when launching from terminal only
https://stackoverflow.com/questions/60156202/flask-app-wont-launch-importerror-cannot-import-name-cached-property-from-w


- socket cleanup https://stackoverflow.com/questions/409783/socket-shutdown-vs-socket-close
- clear up questions for future requirements to make sure
the interpreter wont need to run exceptions
- customized and colourized button status buttons inside json
- add frontendaction report to (both?) logs aswell, having both requires a modification to the seriallogger
- collapsible elements?
- import socket ip and port as cfg? its used multiple times so best define it properly


- Verify double post of hidden elements is not causing problems?
post returned: ImmutableMultiDict([('relayOverride_0', 'on'), ('relayOverride_0', '')])
Answer to that: a dict with duplicate keys will return only the key once with for key in test_dict.keys():
aswell as return the value of the last key duplicate so for our application we're fine since i do
all the work backend so far, if that changes we know how to do deal with duplicates.

- rename set_relay ad set_ovpyterride to flip? maybe differentiation here with another func?

# may be useful to monitor processes for restarts? Pkill python may not be the most elegant solution
proc = subprocess.Popen(["python3", "usbSocketServer.py"])
socket_process.kill()
'''


from stb import STB
from flask import Flask, render_template, request
from threading import Thread, Timer
from flask_socketio import SocketIO, emit
from re import split
from werkzeug.utils import cached_property
import sys

print("Current python environment is being ran from: {}".format(sys.prefix))

stb = STB()
app = Flask('STB-Override')

async_mode = None
socketio = SocketIO(app, async_mode=async_mode)
stb_thread = None


@app.route("/login", methods=["POST", "GET"])
def login():
    return render_template('login.html')


@socketio.on('serial_buffer_request', namespace='/test')
def serial_buffer_request():
    print("sending back to the req")
    for line in reversed(stb.serial_buffer):
        emit('serial_update', {'lines': line}, namespace='/test')


def interpreter(immuteable):
    form_dict = immuteable.to_dict()
    action_dict = {
        "relayOverride": stb.set_override,
        "relaySetStatus": stb.set_relay,
        "reset_room": stb.restart_all_brains,
        "login": stb.login,
        "extend_relays": stb.extend_relays,
        "logout": stb.logout
    }

    for key in form_dict.keys():
        print("key is {}".format(key))
        try:
            action, part_index = split("_", key)
            part_index = int(part_index)
        except ValueError:
            action = key
            part_index = None
        print("action is {}".format(action))
        # careful with the functions they values
        # passed are all strings since it comes from jsons
        # TODO: define how we pass stuff with abdullah, this could limit us in the future
        try:
            action_dict[action](part_index, form_dict[key], form_dict.keys())
        except KeyError as key_e:
            # TODO: pass this error to the frontend
            print("We got a keyerror")
            print(key_e)

    '''
    if action == "relayOverride":
        stb.set_override(part_index, value)
    '''


@app.route('/', methods=['GET', 'POST'])
def index():
    global stb_thread
    room_name = stb.settings.room_name
    if stb_thread is None:
        stb_thread = socketio.start_background_task(updater)

    if request.method == 'POST':
        print("post returned: {}".format(request.form))
        interpreter(request.form)
    if not stb.user:
        return render_template('login.html', room_name=room_name, username=stb.user)

    brains = stb.brains
    relays = stb.relays
    return render_template('index.html', brains=brains, room_name=room_name, relays=relays,
                           async_mode=socketio.async_mode, username=stb.user,
                           extended_relays=stb.extended_relays, serial_limit=stb.settings.serial_limit)


def updater():
    # may need a second
    socketio.sleep(5)
    try:
        while True:
            stb.update_stb()
            if len(stb.updates) > 0:
                print("STB relays have updated with {}".format(stb.updates))
                # https://stackoverflow.com/questions/18478287/making-object-json-serializable-with-regular-encoder/18561055
                socketio.emit('relay_update', {'updates': stb.updates}, namespace='/test', broadcast=True)
                stb.updates = []
            if len(stb.serial_updates) > 0:
                socketio.emit('serial_update', {'lines': stb.serial_updates}, namespace='/test', broadcast=True)
                stb.serial_updates = []
            socketio.sleep(0.1)
    finally:
        stb.cleanup()


def main():
    socketio.run(app, debug=False, host='0.0.0.0')
    # app.run(debug=True)


if __name__ == '__main__':
    main()
