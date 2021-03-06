# Generated by Django 2.0.7 on 2018-11-16 08:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('source', '0002_auto_20180905_0332'),
    ]

    operations = [
        migrations.CreateModel(
            name='OCRSearchRequestBoxTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=200)),
                ('value', models.CharField(max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='ocrsearchrequestbox',
            name='valid',
            field=models.NullBooleanField(default=None),
        ),
        migrations.AddField(
            model_name='ocrsearchrequestboxtag',
            name='box',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='source.OCRSearchRequestBox'),
        ),
    ]
