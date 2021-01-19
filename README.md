<<<<<<< HEAD
web_stb_override

## installation
Since flask can defenitely get issues like the latter one 
use a Venv

move inside the project folder
python3 -m venv venv
source venv/bin/activate


## common inssues
#### Socket-IO
ImportError: No module named socketio

 -> Delete the VEnv is 99% the culprit

https://github.com/miguelgrinberg/Flask-SocketIO/issues/164
https://github.com/miguelgrinberg/Flask-SocketIO/issues/1105
another issue that existed but got fixed by the provided requirements, pinning the Werkzeug==0.16.1 
https://github.com/jarus/flask-testing/issues/143

## for development on a PC
- it will run without GPIOs or emulator

## notes
- checkboxes do submit an empty dict when set on true
- UWSGI.ini with enable-threads = true is crucial to get threading running, 
    glad you found out now bec have fun finding that information
- FLASK_ENV=development flask run
- FLASK_ENV=production flask run
- since browsers do not update stylesheets you may get frustrated till you find the manual reload button combo ctrl-shift-r
=======
web_stb_override beta

## installation
Since flask can defenitely get issues like the latter one 
use a Venv

move inside the project folder
python3 -m venv venv
source venv/bin/activate


## common inssues
#### Socket-IO
ImportError: No module named socketio

 -> Delete the VEnv is 99% the culprit

https://github.com/miguelgrinberg/Flask-SocketIO/issues/164
https://github.com/miguelgrinberg/Flask-SocketIO/issues/1105
another issue that existed but got fixed by the provided requirements, pinning the Werkzeug==0.16.1 
https://github.com/jarus/flask-testing/issues/143

## for development on a PC
- The Venv deliberately doesnt contain fakeRPiGPIO since this library is on conflict with the RPi GPIO library.
    therefore you should install it manually when working on a PC

## notes
- checkboxes do submit an empty dict when set on true
- UWSGI.ini with enable-threads = true is crucial to get threading running, 
    glad you found out now bec have fun finding that information
- FLASK_ENV=development flask run
- FLASK_ENV=production flask run
- since browsers do not update stylesheets you may get frustrated till you find the manual reload button combo ctrl-shift-r
- glob is a standard python library and may only be needed to be installed on RPi, handle manually if needed

>>>>>>> 9c772b57fe931a547d418b577dc88bbf694c26da
