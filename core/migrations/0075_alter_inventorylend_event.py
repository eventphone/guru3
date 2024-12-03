# Generated by Django 4.1.13 on 2024-08-21 18:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0074_inventoryitem_event_alter_inventoryitem_containedin"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inventorylend",
            name="event",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="core.event",
                verbose_name="Event",
            ),
        ),
    ]