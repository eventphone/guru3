from django.contrib import admin

from snom.models import SnomPhone


class SnomPhoneAdmin(admin.ModelAdmin):
    list_display = ('mac', 'httpServerPassword', 'adminPassword',  'userAgent', 'model', 'has_inventory_item')
    search_fields = ('mac', )

    def has_inventory_item(self, obj):
        return obj.get_inventory_item() is not None
    has_inventory_item.boolean = True


admin.site.register(SnomPhone, SnomPhoneAdmin)
