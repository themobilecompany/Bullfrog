# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-28 18:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aps', '0010_auto_20161124_1218'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='contract_fte',
            field=models.FloatField(default=1.0),
        ),
    ]