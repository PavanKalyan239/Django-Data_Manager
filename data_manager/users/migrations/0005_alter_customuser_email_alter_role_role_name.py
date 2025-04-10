# Generated by Django 5.1.6 on 2025-03-02 01:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_remove_customuser_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(db_index=True, max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='role',
            name='role_name',
            field=models.CharField(db_index=True, max_length=50, unique=True),
        ),
    ]
