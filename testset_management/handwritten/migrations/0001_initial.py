# Generated by Django 2.0.7 on 2019-01-02 10:29

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
                ('input_text', models.CharField(help_text='Boxing UI에서 입력한 값', max_length=200)),
                ('unicode_value', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='BoxTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=200)),
                ('value', models.CharField(max_length=200)),
                ('box', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='handwritten.Box')),
            ],
        ),
        migrations.CreateModel(
            name='HandwrittenBox',
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
            name='HandwrittenBoxTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=200)),
                ('value', models.CharField(max_length=200)),
                ('box', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='handwritten.HandwrittenBox')),
            ],
        ),
        migrations.CreateModel(
            name='HandwrittenSource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_reply_id', models.CharField(max_length=100)),
                ('image_key', models.UUIDField()),
                ('user_id', models.IntegerField()),
                ('valid', models.NullBooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='HandwrittenTestset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_url', models.URLField()),
                ('mathpix_latex', models.CharField(blank=True, max_length=500)),
                ('latex', models.CharField(blank=True, max_length=500)),
                ('valid', models.NullBooleanField(default=None)),
                ('handwritten_box', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='testsets', to='handwritten.HandwrittenBox')),
            ],
        ),
        migrations.CreateModel(
            name='HandwrittenTestsetTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=200)),
                ('value', models.CharField(max_length=500)),
                ('testset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='handwritten.HandwrittenTestset')),
            ],
        ),
        migrations.AddField(
            model_name='handwrittenbox',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boxes', to='handwritten.HandwrittenSource'),
        ),
        migrations.AddField(
            model_name='box',
            name='testset',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boxes', to='handwritten.HandwrittenTestset'),
        ),
    ]
