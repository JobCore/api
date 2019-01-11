# Generated by Django 2.0 on 2019-01-11 16:11

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0024_auto_20190110_2049'),
    ]

    operations = [
        migrations.AddField(
            model_name='venue',
            name='employer',
            field=models.ForeignKey(blank=True, default=1, on_delete=django.db.models.deletion.CASCADE, to='api.Employer'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='employer',
            name='payroll_period_starting_time',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2019, 1, 11, 0, 0, 0, 923459, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='payrollperiodpayment',
            name='paryroll_period',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='api.PayrollPeriod'),
        ),
    ]
