# Generated by Django 2.1.14 on 2020-04-10 17:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0041_auto_20200410_1716'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extension',
            name='call_waiting',
            field=models.BooleanField(default=True, help_text='When this extension is currently on a call and another call arrives, the other call is NOT indicated that you are busy but normally ringing. The other incoming call is signaled to your device. This is usually nicely integrated with desktop SIP phones and works also with some DECT phones. If you want to signal busy to the other end when you are on a call, disable call waiting here.', verbose_name='Activate call waiting'),
        ),
    ]
