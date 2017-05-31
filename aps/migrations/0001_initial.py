# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-18 21:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Circle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('glassfrog_id', models.IntegerField(unique=True)),
                ('glassfrog_url', models.CharField(max_length=200)),
                ('last_imported', models.DateTimeField()),
                ('attention_points', models.FloatField(default=0)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('glassfrog_id', models.IntegerField(unique=True)),
                ('glassfrog_url', models.CharField(max_length=200)),
                ('last_imported', models.DateTimeField()),
                ('contract_fte', models.FloatField(default=0.0)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('glassfrog_id', models.IntegerField(unique=True)),
                ('glassfrog_url', models.CharField(max_length=200)),
                ('last_imported', models.DateTimeField()),
                ('circle_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aps.Circle')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RoleFiller',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attention_points', models.FloatField()),
                ('person_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aps.Person')),
                ('role_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aps.Role')),
            ],
        ),
    ]
