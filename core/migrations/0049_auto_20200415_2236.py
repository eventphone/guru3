# Generated by Django 2.1.14 on 2020-04-15 22:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0048_auto_20200415_0039'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userapikey',
            name='key',
            field=models.CharField(max_length=150, verbose_name='Api Key'),
        ),
    ]
