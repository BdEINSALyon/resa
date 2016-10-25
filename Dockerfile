FROM python:3.5

RUN apt-get update && apt-get install -y gettext

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY . /app

RUN python manage.py compilemessages -l en -l fr