# Author Martin Pek

# Flask examples
# https://www.youtube.com/watch?v=_sgVt16Q4O4
# https://github.com/greyli/flask-examples
# https://github.com/greyli/catchat
# https://www.tutorialspoint.com/flask/flask_environment.htm
# https://html.developreference.com/article/12618302/CSS+Background+Images+with+Flask

# basics on post and get...

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


from stb import STB
from flask import Flask, render_template, request
from threading import Thread, Timer
from time import time, sleep

stb = STB()
app = Flask('STB-Override')


@app.route("/login", methods=["POST", "GET"])
def login():
    print()


@app.route('/', methods=['GET', 'POST'])
def index():
    print("index")
    brains = stb.settings.brains
    relays = stb.settings.relays
    room_name = stb.settings.room_name

    if request.method == 'GET':
        return render_template('index.html', brains=brains, room_name=room_name, relays=relays)
    elif request.method == 'POST':
        print("post returned: {}".format(request.form))
        return render_template('index.html', brains=brains, room_name=room_name, relays=relays)
    else:
        return "something went wrong with the request, reload with F5"


'''
@app.before_first_request
def create_stb_backend():
    print()
'''


def updater(start_time):
    print("updated")
    while start_time + 0.5 > time():
        pass
    while True:
        stb.update_stb()
        if stb.updated:
            print("me want update!")
            app.route(route="/")
            stb.updated = False
        # sleep(0.05)
        sleep(5)


def main():
    # args is a bit weird ... don't ask it, needs a terminator
    stb_thread = Thread(target=updater, args=(time(), ))
    stb_thread.start()
    app.run(debug=True)
    # Thread(target=app.run).start()


if __name__ == '__main__':
    main()
