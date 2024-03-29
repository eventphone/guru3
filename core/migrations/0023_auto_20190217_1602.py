# Generated by Django 2.1.5 on 2019-02-17 16:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_extension_threegoptin'),
    ]

    operations = [
        migrations.CreateModel(
            name='IncomingWireMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remote_id', models.PositiveIntegerField(editable=False, verbose_name='Remote reference id')),
                ('timestamp', models.DateTimeField(editable=False, verbose_name='Event timestamp')),
                ('receive_timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Timestamp when received')),
                ('processed', models.BooleanField(default=False, verbose_name='Already processed')),
                ('type', models.CharField(max_length=16, verbose_name='Event type')),
                ('data', models.TextField(verbose_name='Event data')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Event', verbose_name='For event')),
            ],
        ),
        migrations.RemoveField(
            model_name='decthandset',
            name='enableEncryption',
        ),
        migrations.AddField(
            model_name='decthandset',
            name='ipei',
            field=models.CharField(default='000000000000*', max_length=16, verbose_name='IPEI in ETSI 300 175-6 Annex C format'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='decthandset',
            name='uak',
            field=models.CharField(default='', max_length=128, verbose_name='hex encoded UAK'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='inventoryitem',
            name='decommissioned',
            field=models.BooleanField(blank=True, verbose_name='This item is decommissioned'),
        ),
    ]
