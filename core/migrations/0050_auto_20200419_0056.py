# Generated by Django 2.1.14 on 2020-04-19 00:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0049_auto_20200418_1718'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extension',
            name='forward_delay',
            field=models.PositiveIntegerField(default=0, help_text='The delay after which the forward takes effect (only in Active mode). Yes, 0s means immediate forward :)', verbose_name='Activate forward after'),
        ),
        migrations.AlterField(
            model_name='extension',
            name='forward_extension',
            field=models.ForeignKey(blank=True, help_text='Enter the extension that you want to forward to. Please note that forwarding only happens if the forward mode is something other than "No forward". You may enter a number here already if you later want to activate forwarding with a feature code.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='forwards_here', to='core.Extension', verbose_name='To extension'),
        ),
        migrations.AlterField(
            model_name='extension',
            name='forward_mode',
            field=models.CharField(choices=[('DISABLED', 'No forward'), ('ENABLED', 'Active'), ('ON_BUSY', 'Forward on busy'), ('ON_UNAVAILABLE', 'Forward on unavailable')], default='DISABLED', help_text='Forwarding can either be time-based, immediate (time-based with 0s), active if you are busy or if you are unavailable. The last two are almost identical. Forward on busy will also take effect if you are unavailable. However, it also surpresses call waiting for this extension if you are available.', max_length=16, verbose_name='Forward mode'),
        ),
        migrations.AlterUniqueTogether(
            name='extension',
            unique_together={('event', 'extension')},
        ),
    ]
