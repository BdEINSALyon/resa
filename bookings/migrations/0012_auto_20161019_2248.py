# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-19 22:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0011_resource_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='description',
            field=models.CharField(blank=True, max_length=500, verbose_name='description'),
        ),
    ]
