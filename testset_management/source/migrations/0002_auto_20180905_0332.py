# Generated by Django 2.0.7 on 2018-09-05 03:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('source', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ocrsearchrequestsource',
            name='grade_category',
            field=models.IntegerField(blank=True, choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4')], null=True),
        ),
    ]
