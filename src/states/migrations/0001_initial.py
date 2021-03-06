# Generated by Django 2.1.3 on 2019-01-13 04:43

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CensusBlock',
            fields=[
                ('id', models.BigIntegerField(help_text='id', primary_key=True, serialize=False, unique=True)),
                ('population', models.IntegerField()),
                ('housing_units', models.IntegerField()),
                ('poly', django.contrib.gis.db.models.fields.GeometryField(geography=True, srid=4326)),
            ],
        ),
        migrations.CreateModel(
            name='SeedRedistrictMap',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('districts', models.IntegerField()),
                ('initial_file', models.FileField(null=True, upload_to='redist/nx/')),
            ],
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=2, unique=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('nodes', models.IntegerField(default=0)),
                ('edges', models.IntegerField(default=0)),
                ('voting_shape_file', models.FileField(null=True, upload_to='state/shp/vtd/')),
                ('block_shape_file', models.FileField(null=True, upload_to='state/shp/bg/')),
                ('graph_representation', models.FileField(null=True, upload_to='state/nx/')),
            ],
        ),
        migrations.CreateModel(
            name='StateSubsection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('geoid', models.CharField(max_length=255, null=True)),
                ('name', models.CharField(max_length=255)),
                ('county', models.IntegerField()),
                ('has_siblings', models.BooleanField(help_text='has siblings?')),
                ('is_precinct', models.BooleanField()),
                ('land_mass', models.BigIntegerField()),
                ('water_mass', models.BigIntegerField()),
                ('perimeter', models.FloatField()),
                ('area', models.FloatField()),
                ('poly', django.contrib.gis.db.models.fields.GeometryField(geography=True, srid=4326)),
                ('population', models.BigIntegerField(null=True)),
                ('state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='states.State')),
            ],
        ),
        migrations.AddField(
            model_name='seedredistrictmap',
            name='state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='states.State'),
        ),
        migrations.AddField(
            model_name='censusblock',
            name='subsection',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='states.StateSubsection'),
        ),
    ]
