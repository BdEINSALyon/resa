# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-13 11:42
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
                ('name', models.CharField(max_length=150, verbose_name='nom')),
                ('details', models.TextField(verbose_name='détails')),
            ],
            options={
                'verbose_name_plural': 'réservations',
                'verbose_name': 'réservation',
            },
        ),
        migrations.CreateModel(
            name='BookingCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
            ],
            options={
                'verbose_name_plural': 'catégories de réservation',
                'verbose_name': 'catégorie de réservation',
            },
        ),
        migrations.CreateModel(
            name='BookingOccurrence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField(verbose_name='date et heure de début')),
                ('end', models.DateTimeField(verbose_name='date et heure de fin')),
                ('is_valid', models.BooleanField(default=True, verbose_name='valide')),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bookings.Booking')),
            ],
        ),
        migrations.CreateModel(
            name='BookingOwner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='nom')),
                ('barcode', models.CharField(max_length=20, verbose_name='code barre')),
            ],
            options={
                'verbose_name_plural': 'propriétaires de réservation',
                'verbose_name': 'propriétaire de réservation',
            },
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='nom')),
                ('available', models.BooleanField(verbose_name='disponible')),
                ('granularity', models.PositiveIntegerField(verbose_name='granularité')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'ressources',
                'verbose_name': 'ressource',
            },
        ),
        migrations.CreateModel(
            name='ResourceCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='nom')),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bookings.ResourceCategory', verbose_name='catégorie parente')),
            ],
            options={
                'verbose_name_plural': 'catégories de ressource',
                'verbose_name': 'catégorie de ressource',
            },
        ),
        migrations.CreateModel(
            name='RessourceLock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField(verbose_name='date de début')),
                ('end', models.DateTimeField(verbose_name='date de fin')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bookings.Resource')),
            ],
        ),
        migrations.AddField(
            model_name='resource',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bookings.ResourceCategory', verbose_name='catégorie'),
        ),
        migrations.AddField(
            model_name='booking',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bookings.BookingCategory', verbose_name='catégorie de réservation'),
        ),
        migrations.AddField(
            model_name='booking',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bookings.BookingOwner', verbose_name='propriétaire'),
        ),
        migrations.AddField(
            model_name='booking',
            name='resource',
            field=models.ManyToManyField(to='bookings.Resource', verbose_name='ressource'),
        ),
    ]
