# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-25 15:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0014_auto_20161025_1511'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bookings.BookingCategory', verbose_name='catégorie de réservation'),
        ),
    ]