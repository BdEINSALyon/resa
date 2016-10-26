# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-26 15:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0019_auto_20161026_1150'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resourcelock',
            name='resource',
        ),
        migrations.AddField(
            model_name='resourcelock',
            name='resources',
            field=models.ManyToManyField(to='bookings.Resource', verbose_name='ressources'),
        ),
    ]