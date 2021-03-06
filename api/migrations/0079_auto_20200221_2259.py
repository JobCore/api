# Generated by Django 2.2.8 on 2020-02-21 22:59

from django.db import migrations, models
import django.db.models.deletion


def delete_employeedocuments(apps, schema_editor):
    EmployeeDocument = apps.get_model('api', 'EmployeeDocument')
    EmployeeDocument.objects.filter(document_type__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0078_profile_last_4dig_ssn'),
    ]

    operations = [
        migrations.RunPython(delete_employeedocuments),
        migrations.AlterField(
            model_name='employeedocument',
            name='document_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Document'),
        ),
        migrations.AlterField(
            model_name='employeedocument',
            name='employee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Employee'),
        ),
        migrations.AlterField(
            model_name='employeedocument',
            name='rejected_reason',
            field=models.CharField(blank=True, default='', max_length=255),
            preserve_default=False,
        ),
    ]
