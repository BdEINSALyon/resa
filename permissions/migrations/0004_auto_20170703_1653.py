# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-07-03 16:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('permissions', '0003_auto_20170318_1545'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='azure_groups',
            field=models.ManyToManyField(blank=True, related_name='users', to='permissions.AzureGroup'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_fetched_groups',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]
