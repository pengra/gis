# Generated by Django 2.1.3 on 2018-12-04 01:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('states', '0007_auto_20181201_0041'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='statesubsection',
            name='multi_polygon',
        ),
        migrations.AddField(
            model_name='statesubsection',
            name='geoid',
            field=models.CharField(max_length=255, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='statesubsection',
            name='has_siblings',
            field=models.BooleanField(default=False, help_text='has siblings?'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='redistricting',
            name='queue_index',
            field=models.IntegerField(default=0, editable=False),
        ),
    ]
