# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-10-07 16:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0008_remove_booking_contact_va'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcecategory',
            name='default_duration',
            field=models.PositiveIntegerField(default=0, help_text='en minutes', verbose_name='durée par défaut'),
            preserve_default=False,
        ),
    ]
