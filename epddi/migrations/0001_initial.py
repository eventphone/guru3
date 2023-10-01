# Generated by Django 3.0.5 on 2020-12-15 21:45

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import epddi.utils
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0061_auto_20200801_1233'),
    ]

    operations = [
        migrations.CreateModel(
            name='DECTIPNetwork',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('network_address', models.GenericIPAddressField(protocol='IPv4', verbose_name='Network address')),
                ('network_mask', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(16), django.core.validators.MaxValueValidator(30)], verbose_name='Network mask')),
            ],
        ),
        migrations.CreateModel(
            name='EPDDIClient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, max_length=64, null=True, verbose_name='Name')),
                ('location', models.CharField(blank=True, max_length=32, null=True, verbose_name='Location')),
                ('hostname', models.CharField(default=epddi.utils.get_new_router_name, max_length=32, unique=True, verbose_name='Hostname')),
                ('device_type', models.IntegerField(choices=[(1, 'Mikrotik')], verbose_name='Device type')),
                ('device_state', models.IntegerField(choices=[(-1, 'Disabled'), (1, 'New'), (2, 'Provisioning'), (3, 'Provisioned')], default=1, verbose_name='Status')),
                ('dect_network', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='epddi.DECTIPNetwork', verbose_name='DECT network')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Event')),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MikrotikRouter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model', models.CharField(blank=True, max_length=250, verbose_name='Model')),
                ('serial', models.CharField(blank=True, max_length=128, verbose_name='Serial number')),
                ('wan_dhcp', models.BooleanField(default=True, verbose_name='WAN DHCP enabled')),
                ('wan_ip', models.GenericIPAddressField(blank=True, null=True, protocol='IPv4', verbose_name='WAN IP')),
                ('wan_netmask', models.IntegerField(blank=True, default=24, null=True, validators=[django.core.validators.MinValueValidator(16), django.core.validators.MaxValueValidator(31)], verbose_name='Network mask')),
                ('wan_gw', models.GenericIPAddressField(blank=True, null=True, protocol='IPv4', verbose_name='WAN Gateway')),
                ('wan_dns1', models.GenericIPAddressField(blank=True, null=True, protocol='IPv4', verbose_name='WAN DNS1')),
                ('wan_dns2', models.GenericIPAddressField(blank=True, null=True, protocol='IPv4', verbose_name='WAN DNS2')),
                ('token', models.UUIDField(default=uuid.uuid4, verbose_name='Access Token')),
                ('factoryfw', models.CharField(blank=True, max_length=128, verbose_name='Factory Firmware')),
                ('currentfw', models.CharField(blank=True, max_length=128, verbose_name='Current Firmware')),
                ('upgradefw', models.CharField(blank=True, max_length=128, verbose_name='Upgrade Firmware')),
                ('last_config_update', models.DateTimeField(blank=True, default=None, null=True, verbose_name='Last config update')),
                ('client', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='epddi.EPDDIClient')),
            ],
        ),
        migrations.CreateModel(
            name='MikrotikConfigUpdate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('config', models.TextField(verbose_name='Configuration')),
                ('delivered', models.DateTimeField(blank=True, default=None, null=True, verbose_name='Config Delivered')),
                ('mikrotik', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='epddi.MikrotikRouter')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]