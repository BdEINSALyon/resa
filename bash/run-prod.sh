#!/bin/bash
python manage.py migrate && python manage.py collectstatic --noinput && gunicorn resa.wsgi -b 0.0.0.0:8000
