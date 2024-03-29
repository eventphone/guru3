# Generated by Django 2.1.5 on 2019-10-13 21:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_auto_20191012_2215'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='extension',
            name='apply_for_rental_device',
        ),
        migrations.RemoveField(
            model_name='extension',
            name='qualifies_for_rental_device',
        ),
        migrations.AddField(
            model_name='extension',
            name='assignedRentalDevice',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_extensions', to='core.RentalDeviceClassification', verbose_name='Assigned rental device'),
        ),
        migrations.AddField(
            model_name='extension',
            name='requestedRentalDevice',
            field=models.ForeignKey(blank=True, help_text='Please specify the category of rental device you would like to get for this extension. Please note that we may not have sufficiently many devices of this category. As a consequence, we may provide you another or cannot give you any device at all. You can see the assigned device below once we processed your request. Just leave this field empty if you bring your own device.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='request_extensions', to='core.RentalDeviceClassification', verbose_name='Rental device request'),
        ),
    ]
