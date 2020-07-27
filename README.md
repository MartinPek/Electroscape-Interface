web_stb_override


## for development on a PC
- it will run without GPIOs or emulator

## notes
- UWSGI.ini with enable-threads = true is crucial to get threading running, 
    glad you found out now bec have fun finding that information
- FLASK_ENV=development flask run
- FLASK_ENV=production flask run
- since browsers do not update stylesheets you may get frustrated till you find the manual reload button combo ctrl-shift-r