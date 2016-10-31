#!/bin/bash
python manage.py migrate && python manage.py collectstatic --noinput && gunicorn resa.wsgi --log-file -
