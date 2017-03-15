# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-03-15 17:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0039_auto_20170313_2331'),
    ]

    operations = [
        migrations.CreateModel(
            name='Paragraph',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500, verbose_name='titre')),
                ('content', models.TextField(verbose_name='contenu')),
                ('categories', models.ManyToManyField(related_name='paragraphs', to='bookings.ResourceCategory', verbose_name='catégories')),
            ],
            options={
                'verbose_name': 'paragraphe',
                'verbose_name_plural': 'paragraphes',
            },
        ),
    ]