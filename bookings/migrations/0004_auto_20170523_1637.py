# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-23 16:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_auto_20170322_1433'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='category',
        ),
        migrations.AlterField(
            model_name='occurrenceresourcecount',
            name='count',
            field=models.PositiveIntegerField(blank=True, default=1),
        ),
        migrations.DeleteModel(
            name='BookingCategory',
        ),
    ]