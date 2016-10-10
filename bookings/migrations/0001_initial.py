# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-10 17:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('details', models.TextField()),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='BookingCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
            ],
        ),
        migrations.CreateModel(
            name='Planning',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='PlanningSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', models.CharField(choices=[('Mon', 'Lundi'), ('Tue', 'Mardi'), ('Wed', 'Mercredi'), ('Thu', 'Jeudi'), ('Fri', 'Vendredi'), ('Sat', 'Samedi'), ('Sun', 'Dimanche')], max_length=3)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('available', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='ResourceCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
            ],
        ),
        migrations.AddField(
            model_name='resource',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bookings.ResourceCategory'),
        ),
        migrations.AddField(
            model_name='planning',
            name='slots',
            field=models.ManyToManyField(to='bookings.PlanningSlot'),
        ),
        migrations.AddField(
            model_name='booking',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bookings.BookingCategory'),
        ),
        migrations.AddField(
            model_name='booking',
            name='resource',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bookings.Resource'),
        ),
    ]
