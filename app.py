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
- Log for GM shall be one log for all brains, simply add a tag of the affected relays from the given broadcasting brain
- Verify double post of hidden elements is not causing problems?
post returned: ImmutableMultiDict([('relayOverride_0', 'on'), ('relayOverride_0', '')])
- rename set_relay ad set_override to flip? maybe differentiation here with another func?

'''


from stb import STB
from flask import Flask, render_template, request
from threading import Thread, Timer
from time import time, sleep
from flask_socketio import SocketIO, emit
from re import split


stb = STB()
app = Flask('STB-Override')

async_mode = None
socketio = SocketIO(app, async_mode=async_mode)
stb_thread = None


@app.route("/login", methods=["POST", "GET"])
def login():
    return "login"


@socketio.on('broadcast', namespace='/test')
def test_message(message):
    "@socketio braodcast receive myevent: ".format(message)


def interpreter(immuteable):
    form_dict = immuteable.to_dict()
    action_dict = {
        "relayOverride": stb.set_override,
        "relaySetStatus": stb.set_relay
    }

    for key in form_dict.keys():
        action, part_index = split("_", key)
        part_index = int(part_index)
        print("action is {}".format(action))
        # careful with the functions they values
        # passed are all strings since it comes from jsons
        # TODO: define how we pass stuff, this could limit us in the future
        action_dict[action](part_index, form_dict[key], form_dict.keys())

    '''
    if action == "relayOverride":
        stb.set_override(part_index, value)
    '''


@app.route('/', methods=['GET', 'POST'])
def index():
    print("index")
    global stb_thread
    if stb_thread is None:
        stb_thread = socketio.start_background_task(updater)
    room_name = stb.settings.room_name

    if request.method == 'GET':
        brains = stb.brains
        relays = stb.relays
        return render_template('index.html', brains=brains, room_name=room_name, relays=relays,
                               async_mode=socketio.async_mode)
    elif request.method == 'POST':
        print("post returned: {}".format(request.form))
        interpreter(request.form)
        brains = stb.brains
        relays = stb.relays
        return render_template('index.html', brains=brains, room_name=room_name, relays=relays,
                               async_mode=socketio.async_mode)
    else:
        return "something went wrong with the request, reload with F5"


'''
@app.before_first_request
def create_stb_backend():
    print()
'''


def updater():
    try:
        while True:
            stb.update_stb()
            if len(stb.updates) > 0:
                print("STB relays have updated with {}".format(stb.updates))
                # https://stackoverflow.com/questions/18478287/making-object-json-serializable-with-regular-encoder/18561055
                socketio.emit('relay_update', {'updates': stb.updates}, namespace='/test', broadcast=True)
                stb.updates = []
            if len(stb.serial_buffer) > 0:
                socketio.emit('serial_update', {'lines': stb.serial_buffer}, namespace='/test', broadcast=True)
                stb.serial_buffer = []
            socketio.sleep(0.1)
    finally:
        stb.cleanup()


def main():
    socketio.run(app, debug=False)
    # app.run(debug=True)


if __name__ == '__main__':
    main()
