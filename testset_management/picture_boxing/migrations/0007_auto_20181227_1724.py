# Generated by Django 2.1.1 on 2018-12-27 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('picture_boxing', '0006_source_valid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='box',
            name='label',
            field=models.IntegerField(choices=[(0, 'word'), (1, 'picture'), (2, 'graph')]),
        ),
    ]
