#!/bin/sh
python manage.py migrate
/usr/local/bin/gunicorn --user=webapp --config=gunicorn.conf.py webapp.wsgi
