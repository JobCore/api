import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0045_auto_20191107_1838'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document', models.FileField(upload_to='')),
                ('state', models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved')], default='PENDING', max_length=7)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AlterField(
            model_name='employer',
            name='payroll_period_starting_time',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2019, 10, 27, 0, 0, 0, 895811, tzinfo=utc)),
        ),
        migrations.AddField(
            model_name='employee',
            name='documents',
            field=models.ManyToManyField(blank=True, to='api.Document'),
        ),
    ]