# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-18 14:15
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='oauthtoken',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tokens', to=settings.AUTH_USER_MODEL, verbose_name='utilisateur'),
        ),
    ]
