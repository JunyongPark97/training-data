# Generated by Django 2.0.7 on 2018-08-31 18:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testset', '0002_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='box',
            name='unicode_value',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
