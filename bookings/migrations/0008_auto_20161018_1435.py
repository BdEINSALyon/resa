# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-18 14:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0007_auto_20161018_1315'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='details',
            field=models.TextField(blank=True, verbose_name='détails'),
        ),
    ]
