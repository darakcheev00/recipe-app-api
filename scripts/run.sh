#!/bin/sh

# any commands that fail in the script, make sure the entire script crashes
set -e 

# wait for db to setup
python manage.py wait_for_db

# collect all the static files and put them in the configured static files directory (all in same directory)
python manage.py collectstatic --noinput

# run any migrations automatically coming from updates to the server
python manage.py migrate

# running uwsgi service
# socket port 9000 : for nginx server to connect to our app
# workers 4: 4 wsgi workers (a good number)
# master: set uwsgi daemon as main thread
# enable threads: allows multithreading
# module: run the app.wsgi file, dont need to specify .py
uwsgi --socket :9000 --workers 4 --master --enable-threads --module app.wsgi