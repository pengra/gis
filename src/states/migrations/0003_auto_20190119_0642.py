# Generated by Django 2.1.3 on 2019-01-19 06:42

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('states', '0002_county'),
    ]

    operations = [
        migrations.AlterField(
            model_name='censusblock',
            name='poly',
            field=django.contrib.gis.db.models.fields.GeometryField(srid=4326),
        ),
        migrations.AlterField(
            model_name='county',
            name='poly',
            field=django.contrib.gis.db.models.fields.GeometryField(srid=4326),
        ),
        migrations.AlterField(
            model_name='statesubsection',
            name='poly',
            field=django.contrib.gis.db.models.fields.GeometryField(srid=4326),
        ),
    ]
