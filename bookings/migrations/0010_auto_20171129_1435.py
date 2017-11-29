# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-11-29 14:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0009_resourcecategory_default_duration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='number',
            field=models.PositiveIntegerField(default=1, verbose_name='quantité'),
        ),
    ]
