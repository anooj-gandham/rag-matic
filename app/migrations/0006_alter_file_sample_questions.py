# Generated by Django 5.1.6 on 2025-02-19 00:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_alter_file_sample_questions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='sample_questions',
            field=models.JSONField(blank=True, default=list, null=True),
        ),
    ]
