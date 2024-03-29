# Generated by Django 2.1.14 on 2020-04-18 17:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0048_auto_20200415_0039'),
    ]

    operations = [
        migrations.AddField(
            model_name='extension',
            name='forward_delay',
            field=models.PositiveIntegerField(blank=True, help_text='The delay after which the forward takes effect (only in Active mode)', null=True, verbose_name='After'),
        ),
        migrations.AddField(
            model_name='extension',
            name='forward_extension',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='forwards_here', to='core.Extension', verbose_name='To extension'),
        ),
        migrations.AddField(
            model_name='extension',
            name='forward_mode',
            field=models.CharField(choices=[('DISABLED', 'No forward'), ('ENABLED', 'Active'), ('ON_BUSY', 'Forward on busy'), ('ON_UNAVAILABLE', 'Forward on unavailably')], default='DISABLED', max_length=16, verbose_name='Forward mode'),
        ),
    ]
