# Generated by Django 2.0 on 2018-12-05 17:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_rate_shift'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rate',
            name='shift',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.Shift'),
        ),
    ]
