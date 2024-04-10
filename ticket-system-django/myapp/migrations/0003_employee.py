# Generated by Django 5.0 on 2024-03-16 09:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_ticket_delete_member'),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('empcode', models.CharField(default=None, max_length=255)),
                ('fullname', models.CharField(default=None, max_length=255)),
                ('designation', models.CharField(default=None, max_length=500)),
            ],
        ),
    ]