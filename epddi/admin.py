from django.contrib import admin

# Register your models here.
from epddi.models import *


class MikrotikRouterAdmin(admin.ModelAdmin):
    list_display = ('client', 'last_config_update')
    fields = ('client', 'wan_dhcp', 'wan_ip', 'wan_netmask', 'wan_gw', 'wan_dns1', 'wan_dns2', 'token', 'admin_password', 'factoryfw', 'currentfw', 'upgradefw', 'model', 'serial', 'last_config_update')
    readonly_fields = ['admin_password']


class MikrotikConfigUpdateAdmin(admin.ModelAdmin):
    list_display = ('mikrotik', 'created', 'delivered')


admin.site.register(DECTIPNetwork)
admin.site.register(MikrotikRouter,MikrotikRouterAdmin)
admin.site.register(EPDDIClient)
admin.site.register(ClientCertRevocation)
admin.site.register(MikrotikConfigUpdate, MikrotikConfigUpdateAdmin)
