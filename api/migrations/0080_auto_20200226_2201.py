# Generated by Django 2.2.8 on 2020-02-26 22:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0079_auto_20200221_2259'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='additional_deductions',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='employee',
            name='dependants_deduction',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='employee',
            name='other_income',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='employee',
            name='step2c_checked',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AddField(
            model_name='employeepayment',
            name='taxes',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='employee',
            name='extra_withholding',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10),
        ),
    ]
