# https://www.youtube.com/watch?v=_sgVt16Q4O4

# more examples
# https://github.com/greyli/flask-examples
# https://github.com/greyli/catchat
# https://www.tutorialspoint.com/flask/flask_environment.htm
# https://html.developreference.com/article/12618302/CSS+Background+Images+with+Flask

# basics on post and get...

# basics on get and post
# https://stackoverflow.com/questions/10434599/get-the-data-received-in-a-flask-request

from stb import STB
from flask import Flask, render_template, request

stb = STB()
app = Flask('STB-Override')


@app.route("/login", methods=["POST", "GET"])
def login():
    print()


@app.route('/', methods=['GET', 'POST'])
def index():
    brains = stb.settings.brains
    relays = stb.settings.relays
    room_name = stb.settings.room_name

    if request.method == 'GET':
        return render_template('index.html', brains=brains, room_name=room_name, relays=relays)
    elif request.method == 'POST':
        print("post returned: {}".format(request.form))
        return render_template('index.html', brains=brains, room_name=room_name, relays=relays)
    else:
        return "whoops"


def main():
    app.run(debug=True)


main()
