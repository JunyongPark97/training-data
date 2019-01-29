# Generated by Django 2.1.1 on 2018-12-26 11:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Box',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='box')),
                ('left', models.DecimalField(decimal_places=4, max_digits=5)),
                ('top', models.DecimalField(decimal_places=4, max_digits=5)),
                ('right', models.DecimalField(decimal_places=4, max_digits=5)),
                ('bottom', models.DecimalField(decimal_places=4, max_digits=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('mathpix_latex', models.CharField(blank=True, max_length=500)),
                ('latex', models.CharField(blank=True, max_length=500)),
                ('valid', models.NullBooleanField(default=None)),
            ],
        ),
        migrations.CreateModel(
            name='BoxTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=200)),
                ('value', models.CharField(max_length=200)),
                ('box', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='picture_boxing.Box')),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('search_request_id', models.CharField(max_length=100)),
                ('image_key', models.UUIDField()),
                ('user_id', models.IntegerField()),
                ('grade', models.IntegerField(blank=True, null=True)),
                ('grade_category', models.IntegerField(blank=True, choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4')], null=True)),
            ],
        ),
        migrations.AddField(
            model_name='box',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boxes', to='picture_boxing.Source'),
        ),
    ]
