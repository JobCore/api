# Generated by Django 2.2.8 on 2020-01-31 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0073_auto_20200129_1730'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rate',
            name='comments',
            field=models.TextField(blank=True, default=''),
        ),
    ]