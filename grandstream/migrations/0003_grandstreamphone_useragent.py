# Generated by Django 2.0.3 on 2018-08-26 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grandstream', '0002_auto_20180821_1839'),
    ]

    operations = [
        migrations.AddField(
            model_name='grandstreamphone',
            name='userAgent',
            field=models.CharField(max_length=512, null=True, verbose_name='User Agent'),
        ),
    ]
