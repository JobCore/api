# Generated by Django 2.2.8 on 2020-12-21 04:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0104_auto_20201201_1939'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='resume',
            field=models.URLField(blank=True),
        ),
    ]