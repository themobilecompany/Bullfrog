# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-21 15:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('aps', '0007_auto_20161121_1539'),
    ]

    operations = [
        migrations.AlterField(
            model_name='circle',
            name='super_circle',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sub_circle', to='aps.Circle'),
        ),
    ]
