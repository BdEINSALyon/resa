# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-03-15 17:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0043_auto_20170315_1728'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequiredInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='nom')),
                ('categories', models.ManyToManyField(related_name='required_infos', to='bookings.ResourceCategory', verbose_name='catégories')),
            ],
            options={
                'verbose_name': 'information requise',
                'verbose_name_plural': 'informations requises',
            },
        ),
    ]
