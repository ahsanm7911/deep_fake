# Generated by Django 5.2 on 2025-04-27 02:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_profile'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='history',
            options={'ordering': ['-timestamp'], 'verbose_name': 'History', 'verbose_name_plural': 'Histories'},
        ),
        migrations.RenameField(
            model_name='history',
            old_name='date',
            new_name='timestamp',
        ),
        migrations.AddField(
            model_name='history',
            name='confidence',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='history',
            name='image_height',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='history',
            name='image_width',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='history',
            name='pdf_report',
            field=models.FileField(blank=True, null=True, upload_to='pdfs/'),
        ),
        migrations.AlterField(
            model_name='history',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='images/'),
        ),
        migrations.AlterField(
            model_name='history',
            name='image_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='history',
            name='result',
            field=models.CharField(choices=[('Real', 'Real'), ('Fake', 'Fake')], max_length=10),
        ),
        migrations.AlterField(
            model_name='history',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detection_history', to=settings.AUTH_USER_MODEL),
        ),
    ]
