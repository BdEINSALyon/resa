# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-26 15:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0021_auto_20161026_1529'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcelock',
            name='reason',
            field=models.CharField(default='', max_length=150),
            preserve_default=False,
        ),
    ]