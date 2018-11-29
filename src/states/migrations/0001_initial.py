# Generated by Django 2.1.3 on 2018-11-29 08:07

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
                ('id', models.IntegerField(help_text='id', primary_key=True, serialize=False, unique=True)),
                ('population', models.IntegerField()),
                ('housing_units', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Redistrcting',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('queue_index', models.IntegerField(default=1, editable=False)),
                ('visualization', models.ImageField(upload_to='')),
                ('shape_file', models.FileField(upload_to='')),
                ('steps', models.IntegerField(default=0)),
                ('total_runtime', models.FloatField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='SeedRedistrictMap',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('initial_visualization', models.ImageField(upload_to='')),
                ('initial_file', models.FileField(upload_to='')),
            ],
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=2, unique=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('voting_shape_file', models.FileField(null=True, upload_to='')),
                ('block_shape_file', models.FileField(null=True, upload_to='')),
                ('block_dictionary', models.FileField(null=True, upload_to='')),
                ('fast_visualization', models.ImageField(null=True, upload_to='')),
            ],
        ),
        migrations.CreateModel(
            name='StateSubsection',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=20)),
                ('county', models.IntegerField()),
                ('multi_polygon', models.BooleanField()),
                ('is_precinct', models.BooleanField()),
                ('land_mass', models.IntegerField()),
                ('water_mass', models.IntegerField()),
                ('perimeter', models.FloatField()),
                ('area', models.FloatField()),
                ('poly', django.contrib.gis.db.models.fields.GeometryField(geography=True, srid=4326)),
                ('state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='states.State')),
            ],
        ),
        migrations.AddField(
            model_name='seedredistrictmap',
            name='state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='states.State'),
        ),
        migrations.AddField(
            model_name='redistrcting',
            name='initial',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='states.SeedRedistrictMap'),
        ),
        migrations.AddField(
            model_name='censusblock',
            name='subsection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='states.StateSubsection'),
        ),
    ]