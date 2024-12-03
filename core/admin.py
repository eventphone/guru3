from django.contrib import admin
from core.models import Event, AudioFile, InventoryItem, InventoryType, InventoryItemRecallStatus
from core.models import Extension, DECTHandset, ExtensionClaim, DECTManufacturer, DECTInventorySuggestion
from core.models import WireMessage, UserApiKey, IncomingWireMessage
from core.models import CallGroupInvite
from core.models import RegistrationEmailToken


class OrgaInline(admin.TabularInline):
    model = Event.organizers.through
    verbose_name = "Orga"


class PocHelpdeskInline(admin.TabularInline):
    model = Event.pocHelpdesk.through
    verbose_name = "Poc Helpdesk"


class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'start', 'end', 'registrationStart', 'hasGSM', 'isPermanent')
    search_fields = ('name', 'location', 'start', 'end', 'registrationStart', 'hasGSM', 'isPermanent')

    inlines = [
        OrgaInline,
        PocHelpdeskInline,
    ]


class ExtensionAdmin(admin.ModelAdmin):
    list_display = ('extension', 'owner', 'name', 'location', 'get_event')
    search_fields = ('extension', 'owner__username', 'name', 'location', 'event__name')

    def get_event(self, obj):
        return Event.objects.get(pk=obj.event_id).name
    get_event.short_description = 'Event'
    get_event.admin_order_field = 'event__name'


class CallGroupInviteAdmin(admin.ModelAdmin):
    model = CallGroupInvite
    list_display = ('extension', 'group', 'get_event', 'invite_reason', 'inviter', 'accepted')
    search_fields = ('extension__extension', 'group__name',)

    def get_event(self, obj):
        return Event.objects.get(pk=obj.group.event_id).name
    get_event.short_description = 'Event'
    get_event.admin_order_field = 'event__name'

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        queryset |= self.model.objects.filter(group__event__name__contains=search_term)
        queryset |= self.model.objects.filter(invite_reason__contains=search_term)
        queryset |= self.model.objects.filter(inviter__username__contains=search_term)
        return queryset, use_distinct


class CallGroupInviteInline(admin.StackedInline):
    model = CallGroupInvite
    extension = 'extension'


class ExtensionClaimAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'extension')
    search_fields = ('user__username', 'event__name', 'extension')


class AudioFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'file')
    search_fields = ('name', 'owner__username', 'file')


class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('description', 'barcode', 'itemType', 'decommissioned')
    search_fields = ('description', 'barcode', 'itemType__name', 'decommissioned')


class WireMessageAdmin(admin.ModelAdmin):
    list_display = ('type', 'event', 'delivered')
    search_fields = ('type', 'event__name', 'delivered')


class IncomingWireMessageAdmin(admin.ModelAdmin):
    list_display = ('type', 'event', 'processed')
    search_fields = ('type', 'event__name', 'processed')


class DECTHandsetAdmin(admin.ModelAdmin):
    readonly_fields = ('owner',)
    list_display = ('owner', 'description')
    search_fields = ('owner__username', 'description', 'ipei')


admin.site.register(Extension, ExtensionAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(DECTHandset, DECTHandsetAdmin)
admin.site.register(WireMessage, WireMessageAdmin)
admin.site.register(IncomingWireMessage, IncomingWireMessageAdmin)
admin.site.register(CallGroupInvite, CallGroupInviteAdmin)
admin.site.register(ExtensionClaim, ExtensionClaimAdmin)
admin.site.register(AudioFile, AudioFileAdmin)
admin.site.register(InventoryItem, InventoryItemAdmin)
admin.site.register(InventoryType)
admin.site.register(DECTManufacturer)
admin.site.register(DECTInventorySuggestion)
admin.site.register(RegistrationEmailToken)
admin.site.register(InventoryItemRecallStatus)
