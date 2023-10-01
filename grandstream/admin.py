from django.contrib import admin
from grandstream.models import GrandstreamPhone

# Register your models here.


class GrandstreamPhoneAdmin(admin.ModelAdmin):
    list_display = ('mac', 'userPassword', 'userAgent','has_inventory_item')
    search_fields = ('mac', )

    def has_inventory_item(self, obj):
        return obj.get_inventory_item() is not None
    has_inventory_item.boolean = True


admin.site.register(GrandstreamPhone, GrandstreamPhoneAdmin)
