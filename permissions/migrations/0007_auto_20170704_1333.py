# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-07-04 13:33
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('permissions', '0006_azuregroup_azure_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='azuregroup',
            old_name='azure_id',
            new_name='_azure_id',
        ),
        migrations.RemoveField(
            model_name='azuregroup',
            name='azure_name',
        ),
    ]
