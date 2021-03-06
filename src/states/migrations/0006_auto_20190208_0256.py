# Generated by Django 2.1.3 on 2019-02-08 02:56

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('states', '0005_auto_20190205_2230'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcessQueue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('queued', 'Queued'), ('running', 'Running'), ('done', 'Done'), ('fail', 'Failed')], max_length=7)),
                ('payload', django.contrib.postgres.fields.jsonb.JSONField()),
                ('queued', models.DateTimeField(auto_now_add=True)),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='states.Run')),
            ],
        ),
        migrations.AlterField(
            model_name='event',
            name='type',
            field=models.CharField(choices=[('move', 'Move'), ('fail', 'Move Failure'), ('weight', 'Weight Update'), ('burn end', 'End Burn in')], max_length=13),
        ),
    ]
