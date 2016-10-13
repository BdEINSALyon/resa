# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-13 13:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_auto_20161013_1242'),
    ]

    operations = [
        migrations.RenameField(
            model_name='booking',
            old_name='resource',
            new_name='resources',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='name',
        ),
        migrations.AddField(
            model_name='booking',
            name='reason',
            field=models.CharField(default='', max_length=150, verbose_name='raison'),
            preserve_default=False,
        ),
    ]
