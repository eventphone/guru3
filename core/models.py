from datetime import date, datetime
import json
import magic
import os
from functools import lru_cache

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models, connection, transaction
from django.db.models.functions import Length, Substr
from django.db.models import Q, F, CharField, Prefetch, Value, DEFERRED
from django.forms.models import model_to_dict
from django.template.loader import get_template
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils import timezone
from django.utils.safestring import SafeString
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from timezone_field import TimeZoneField

from core import messaging, utils, inventory
from core.utils import retry_on_db_deadlock

# Permission bits we use for events and their extensions (for creation)
from guru3.consumers import notify_clients

PERM_USER_READ = 1
PERM_USER = 2
PERM_ORGA = 4
PERM_ADMIN = 8

LANG_CHOICES = (
        ('de-DE', 'Deutsch (Deutschland)'),
        ('en-GB', 'English (GB)'),
        ('en-US', 'English (US)')
    )

CharField.register_lookup(Length, 'length')


class ExtensionNotAllowedException(Exception):
    pass


def return_or_throw_ext_not_allowed(throw, msg):
    if throw:
        raise ExtensionNotAllowedException(msg)
    else:
        return False

class ModelAsJsonMixin:
    def as_json(self):
        return json.dumps(model_to_dict(self))

    @staticmethod
    def query_as_json(query):
        return [o.as_json() for o in query]


def upload_file_name(instance, filename):
    instance.file.seek(0)
    buf = instance.file.read()
    mime = magic.from_buffer(buf, mime=True)
    if (mime == 'audio/mpeg'):
        if (not filename.endswith('.mp3')):
            filename += '.mp3'
    elif(mime == 'audio/x-wav'):
        if (not filename.endswith('.wav')):
            filename += '.wav'
    else:
        filename = '.' + filename
    return os.path.join('audio', filename)


class AudioFile(models.Model):
    name = models.CharField(max_length=128, verbose_name=_("Audio File Name"))
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(verbose_name=_("Audio File (<=5MB)"), upload_to=upload_file_name)
    sha512 = models.CharField(max_length=128)
    processed = models.BooleanField(default=False)
    processing_error = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def has_read_permission(self, user):
        return user == self.owner or user.is_staff

    def has_write_permission(self, user):
        return user == self.owner or user.is_staff

    def has_delete_permission(self, user):
        return self.has_write_permission(user)

    def get_url(self):
        url = self.file.url
        return url

    def get_mime(self):
        if self.file.path is not None:
            return magic.from_file(self.file.path, mime=True)
        else:
            return ""

    def delete(self, *args, **kwargs):
        related_extensions = self.extension_set.all()
        for extension in related_extensions:
            extension.ringback_tone = None
            update_msg = messaging.makeExtensionUpdateMessage(extension)
            update_msg.save()
        self.file.delete()
        super().delete(*args, **kwargs)


def _generate_orgakey():
    return utils.generateRandomPassword(32)


def _generate_mgr_key():
    return utils.generateRandomPassword(64)


class RecursiveSearchDepthLimitExceededException(Exception):
    def __init__(self, path):
        self.path = path


class Event(models.Model):
    name = models.CharField(max_length=128, verbose_name=_("Event name"))
    location = models.CharField(max_length=128, verbose_name=_("Event location"))
    announcement_lang = models.CharField(max_length=5, choices=LANG_CHOICES, default='de-DE',
                                         verbose_name=_("Default Extension Announcement Language"))
    eventStreamTarget = models.CharField(max_length=256, verbose_name=_("PBX events target"))

    start = models.DateField(verbose_name=_("Start date"), blank=True, null=True)
    end = models.DateField(verbose_name=_("End date"), blank=True, null=True)
    registrationStart = models.DateField(verbose_name=_("Registration start date"), blank=True, null=True)

    extensionLength = models.PositiveIntegerField(verbose_name=_("Extension length (in number of digits)"))

    extensionStart = models.CharField(max_length=32, verbose_name=_("Extension start"))
    extensionEnd = models.CharField(max_length=32, verbose_name=_("Extension end"))
    orgaExtensionStart = models.CharField(max_length=32, verbose_name=_("Orga Extension start"))
    orgaExtensionEnd = models.CharField(max_length=32, verbose_name=_("Orga Extension end"))

    hasGSM = models.BooleanField(verbose_name=_("This event has also a GSM network"), default=False)
    hasDECT = models.BooleanField(verbose_name=_("This event has DECT"), default=True)
    hasApp = models.BooleanField(verbose_name=_("This event has Applications"), default=True)
    hasPremium = models.BooleanField(verbose_name=_("This event has premium SIP"), default=False)

    descriptionDE = models.TextField(verbose_name=_("Event description (German)"))
    descriptionEN = models.TextField(verbose_name=_("Event description (English)"))

    url = models.URLField(verbose_name=_("Event Homepage"))

    organizers = models.ManyToManyField(User, related_name="organizedEvents", editable=False,
                                        verbose_name=_("Organizers of this event"))
    pocHelpdesk = models.ManyToManyField(User, related_name="helpdeskEvents", editable=False,
                                         verbose_name=_("PoC helpdesk people in this event"))

    isPermanentAndPublic = models.BooleanField(verbose_name=_("This event is public although it is permanent"),
                                               default=False)

    regularSipServer = models.CharField(max_length=128, verbose_name=_("(regular) SIP server address"),
                                        default=settings.SIP_SERVER)

    orgaKey = models.CharField(max_length=64, verbose_name=_("Organizer key for this event"), editable=False,
                               default=_generate_orgakey)

    mgr_key = models.CharField(max_length=150, verbose_name=_("Api Key"), editable=False,
                               default="INVALID_KEY")

    timezone = TimeZoneField(default="Europe/Berlin", use_pytz=False, verbose_name=_("Timezone"))

    def regenerate_mgr_key(self):
        key = _generate_mgr_key()
        self.mgr_key = make_password(key)
        self.save()
        return "{}${}".format(self.pk,key)

    def check_mgr_key(self, key):
        return check_password(key, self.mgr_key)

    def __str__(self):
        return self.name

    @property
    def isPermanent(self):
        return self.start is None

    @property
    def isPast(self):
        return (not self.isPermanent) and self.end < now().date()

    # Methods to access all the events. We want the possibility to show some events
    # Only to special users, so pass the user variable
    @classmethod
    def getPermanent(cls, user=None):
        if user is not None and user.is_staff:
            return cls.objects.filter(start__isnull=True).order_by("name")
        elif user.is_authenticated:
            return cls.objects.filter(start__isnull=True, isPermanentAndPublic=True).order_by("name")
        else:
            return []

    @classmethod
    def getRunning(cls, user=None):
        running = cls.objects.filter(start__isnull=False).filter(start__lte=date.today(), end__gte=date.today())
        return running.order_by("start")

    @classmethod
    def getUpcoming(cls, user=None):
        # if staff
        upcoming = cls.objects.filter(start__isnull=False).filter(start__gt=date.today())
        if not user.is_authenticated:
            # anon
            upcoming = upcoming.filter(Q(registrationStart__lte=date.today()))
        elif not user.is_staff:
            # logged in
            upcoming = upcoming.filter(Q(registrationStart__lte=date.today()) | Q(organizers=user.pk))
        return upcoming.distinct().order_by("start")

    @classmethod
    def getPast(cls, user=None):
        if user is not None and user.is_staff:
            return cls.objects.filter(start__isnull=False).filter(end__lt=date.today()).order_by("-start")
        else:
            return []

    def getUserPermissions(self, user, orga_key=None):
        if user is None or not user.is_authenticated:
            return 0
        elif user.is_staff:
            return PERM_USER_READ | PERM_USER | PERM_ORGA | PERM_ADMIN
        else:
            perms = PERM_USER_READ
            # For all non-permanent events the user also has normal user rights
            if not self.isPermanent or self.isPermanentAndPublic:
                perms = perms | PERM_USER
            # Orgas get permission to populate orga range
            if self.organizers.filter(pk=user.pk).exists():
                perms |= PERM_ORGA
            elif self.orgaKey == orga_key:
                perms |= PERM_ORGA

            # Poc Helpdesk people serve as "local admins" for this event
            if self.pocHelpdesk.filter(pk=user.pk).exists():
                perms |= PERM_ORGA | PERM_ADMIN
            return perms

    def isEventAdmin(self, user):
        if user is None or not user.is_authenticated:
            return False
        elif user.is_staff:
            return True
        else:
            return self.pocHelpdesk.filter(pk=user.pk).exists()

    def isEventOrga(self, user):
        if user is None or not user.is_authenticated:
            return False
        elif user.is_staff:
            return True
        else:
            return self.organizers.filter(pk=user.pk).exists()

    def userIsAllowedToCreateExtension(self, user, extension, throw=False, perms=None, today=None, current_ext=None):
        if today is None:
            today = date.today()
        if perms is None:
            perms = self.getUserPermissions(user)

        # If there is a valid claim, allow/deny based on the user that owns the claim
        try:
            claim = ExtensionClaim.objects.get(event=self, extension=extension)
            if claim.valid_until >= today:
                if claim.user != user:
                    return return_or_throw_ext_not_allowed(throw, _("Extension claim is not yours"))
                return True
        except ExtensionClaim.DoesNotExist:
            pass

        # Only admin or claim may create extensions that do not match standard length
        if (len(extension) != self.extensionLength) and (perms & PERM_ADMIN) == 0:
            return return_or_throw_ext_not_allowed(throw, _("Invalid extension length"))

        # Only admin may add or remove digits from extension
        if ((perms & PERM_ADMIN) != 0 and current_ext is not None):
            if (extension.startswith(current_ext) or current_ext.startswith(extension)):
                # someone somehow managed to create this extension without a conflict, so we don't need to validate anymore
                return True

        # if extension, prefix or suffix exists as extension we will deny it
        existing_extension_count = self.getConflictingExtensions(extension)\
            .count()
        if (existing_extension_count > 0):
            return return_or_throw_ext_not_allowed(throw, _("Extension already exists"))

        # if extension, prefix or suffix exists as claim we will deny it
        existing_claim_count = ExtensionClaim.objects\
            .filter(event=self, valid_until__gte=today)\
            .values('extension')\
            .annotate(prefix_extension=Value(extension, output_field=CharField()))\
            .filter(Q(extension__startswith=extension)|Q(prefix_extension__startswith=F('extension')))\
            .count()
        if (existing_claim_count > 0):
            return return_or_throw_ext_not_allowed(throw, _("An extension claim collides with your extension"))

        # Only orga may create within orga range
        orgaExtStart = self.orgaExtensionStart[:len(extension)]
        orgaExtEnd = self.orgaExtensionEnd[:len(extension)]
        if orgaExtStart <= extension <= orgaExtEnd:
            if (perms & PERM_ORGA) == 0:
                return return_or_throw_ext_not_allowed(throw, _("Extensions in orga range require privileges"))
            else:
                return True

        # Only real admins may create without standard range
        extStart = self.extensionStart[:len(extension)]
        extEnd = self.extensionEnd[:len(extension)]
        if (extension < extStart or extension > extEnd) and (perms & PERM_ADMIN) == 0:
            return return_or_throw_ext_not_allowed(throw, _("Extensions outside normal range require privileges"))

        # Check if admin/orga and outside of register period.
        if not self.isPermanent:
            if not(self.registrationStart <= today) and \
                    (perms & (PERM_ADMIN | PERM_ORGA)) == 0:
                return return_or_throw_ext_not_allowed(throw, _("Public registration is closed for this event."))
            if not(today <= self.end) and (perms & PERM_ADMIN) == 0:
                return return_or_throw_ext_not_allowed(throw, _("This is event is in the past."))

        # Deny for non ORGA/ADMIN if extension limit for event is exceeded
        if (Extension.objects.filter(event=self, owner=user).count() >= settings.NORMAL_USER_MAX_EXTENSIONS
           and (perms & (PERM_ADMIN | PERM_ORGA) == 0)):
            return return_or_throw_ext_not_allowed(throw, _("Extension limit exceeded. Please contact us if you think"
                                                            " that you need more for a valid reason."))

        # Now ok if at least user permissions
        if (perms & PERM_USER) != 0:
            return True
        else:
            return return_or_throw_ext_not_allowed(throw, _("You have no permissions for this event."))

    def getConflictingExtensions(self, ext, for_update=False):
        if for_update:
            obj_manager = Extension.objects.select_for_update()
        else:
            obj_manager = Extension.objects
        res = obj_manager.filter(event=self)\
            .annotate(prefix_extension=Value(ext, output_field=CharField()))\
            .filter(Q(extension__startswith=ext)|Q(prefix_extension__startswith=F('extension')))
        return res

    def checkIfExtensionIsFree(self, ext, for_update=False, current_ext=None):
        """Check if an extension is currently free in this event"""
        # Check if there is already a prefix for this number
        return len(self.getConflictingExtensions(ext, for_update).exclude(extension=current_ext)) == 0

    def isPhonebookPublic(self):
        """Returns True if the phonebook should currently be public.
           This is the case for currently running events
        """
        # Permanent events never have a public phonebook
        if self.isPermanent:
            return False
        # Otherwise check if it is currently running
        return self.registrationStart <= date.today() <= self.end

    def searchExtensions(self, searchstring):
        # We search in the extension, the name and the location
        normalized_extension = utils.extension_normalize(searchstring)
        qs = ((Q(extension__icontains=searchstring) | Q(name__icontains=searchstring) |
               Q(extension__icontains=normalized_extension) |
               Q(location__icontains=searchstring)) & Q(event=self.pk))
        return Extension.objects.filter(qs)

    def calculateFormExtensionTypes(self, perm):
        return filter(lambda x:  EXTENSION_TYPES_CONDITIONS[x[0]](self, perm), EXTENSION_TYPES)

    def getOpenWireMessageCount(self):
        return WireMessage.objects.filter(event=self,delivered=False).count()

    def get_oldest_unprocessed_wiremessage_age_seconds(self):
        oldest_undelivered = WireMessage.objects.filter(event=self,delivered=False).order_by("timestamp")[:1]
        if oldest_undelivered:
            last_unprocessed_delta = datetime.now() - oldest_undelivered[0].timestamp
            return last_unprocessed_delta.seconds
        else:
            return None

    def unusedExtensionQuery(self):
        extensions = Extension.objects.filter(event=self).values('extension')
        claims = ExtensionClaim.objects.filter(event=self).filter(valid_until__gte=timezone.now()).values('extension')
        extensions_exact = extensions.filter(extension__length=self.extensionLength)
        claims_exact = claims.filter(extension__length=self.extensionLength)
        query = ExtensionPool.objects.exclude(extension__in=extensions_exact)\
            .exclude(extension__in=claims_exact)\
            .filter(extension__gte=self.extensionStart)\
            .filter(extension__lte=self.extensionEnd)\
            .filter(extension__length=self.extensionLength)
        #Filter conflicting suffixes
        extensions_suffix = extensions.filter(extension__length__gt=self.extensionLength)\
            .annotate(suffix_extension=Substr('extension', 1, self.extensionLength))\
            .values('suffix_extension')
        claims_suffix = claims.filter(extension__length__gt=self.extensionLength)\
            .annotate(suffix_claim=Substr('extension', 1, self.extensionLength))\
            .values('suffix_claim')
        query = query.exclude(extension__in=extensions_suffix)\
            .exclude(extension__in=claims_suffix)
        # Filter conflicting prefixes
        for i in range(1, self.extensionLength):
            claims_prefix = claims.filter(extension__length=i)
            extensions_prefix = extensions.filter(extension__length=i)
            alias = 'prefix_' + str(i)
            query = query.annotate(**{alias : Substr('extension', 1, i)})\
                .exclude(**{alias + '__in':claims_prefix})\
                .exclude(**{alias + '__in':extensions_prefix})
        return query

    def getRandomFreeExtension(self):
        query = self.unusedExtensionQuery()
        free = query.order_by('?')\
            .values_list('extension', flat=True)[:1]
        return free[0]

    def getAllFreeExtensions(self):
        query = self.unusedExtensionQuery()
        return query.order_by('extension')\
            .values_list('extension', flat=True)


class DECTManufacturer(models.Model):
    display_name = models.CharField(max_length=64, verbose_name=_("Manufacturer name"))

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name


class DECTHandset(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, editable=False)
    description = models.CharField(max_length=64, blank=True, verbose_name=_("Description"))
    vendor = models.ForeignKey(DECTManufacturer, blank=True, null=True, on_delete=models.SET_NULL,
                               verbose_name=_("Device vendor"),
                               help_text=_("Help us to create an IPEI to vendor translation table and select the "
                                           "vendor of your device from the list. If the vendor is missing, please "
                                           "create a ticket in our <a href=\"/support\" target=\"_blank\">"
                                           "support system.</a> Thanks :)"))
    model_designation = models.CharField(max_length=32, blank=True, default="", verbose_name=_("Model designation"),
                                         help_text=_("Helps us to better understand manufacturer codes of devices."))
    ipei = models.CharField(max_length=16, verbose_name=_("IPEI in ETSI 300 175-6 Annex C format"))
    uak = models.CharField(max_length=128, editable=False, verbose_name=_("hex encoded UAK"))

    def __str__(self):
        if self.description:
            return self.description
        else:
            return "(Unnamed - IPEI {})".format(self.ipei)

    def __repr__(self):
        return "<DECTHandset desc={} IPEI={}>".format(self.description, self.ipei)

    def has_read_permission(self, user):
        return user == self.owner

    def has_write_permission(self, user):
        return user == self.owner

    def has_delete_permission(self, user):
        return self.has_write_permission(user)

    def get_event_extension(self, event):
        try:
            return self.extension_set.get(event=event)
        except Extension.DoesNotExist:
            return None

    def get_extension_history(self):
        return Extension.objects.filter(handset=self.pk).order_by("event__start")

    @classmethod
    def get_user_handsets(cls, user):
        return cls.objects.filter(owner=user).order_by("description")

    @classmethod
    def get_user_handset_history(cls, user):
        return cls.objects \
                  .prefetch_related(Prefetch("extension_set",
                                             queryset=Extension.objects
                                                               .select_related("event").order_by("event__start"))) \
                  .filter(owner=user).order_by("description")

    @classmethod
    def get_unused(cls, user, event):
        return cls.objects.filter(owner=user).exclude(extension__event=event)


EXTENSION_TYPES = (
    ("SIP", _("SIP telephone")),
    ("DECT", _("DECT handset")),
    ("GSM", _("GSM handset")),
    ("GROUP", _("Callgroup")),
    ("APP", _("Application")),
    ("ANNOUNCEMENT", _("Announcement")),
    ("SPECIAL", _("Special extension")),
)

EXTENSION_TYPES_CONDITIONS = {
    "SIP": lambda event, user_perm: True,
    "DECT": lambda event, user_perm: event.hasDECT,
    "GSM":lambda event, user_perm: event.hasGSM,
    "GROUP": lambda event, user_perm: user_perm & PERM_ADMIN != 0,
    "APP": lambda event, user_perm: user_perm & PERM_ADMIN != 0,
    "ANNOUNCEMENT": lambda  event, user_perm: True,
    "SPECIAL": lambda event, user_perm: user_perm & PERM_ADMIN != 0,
}


DISPLAY_MODES = (
    ("NUMBER", _("Show only caller number")),
    ("NUMBER_NAME", _("Show caller number followed by name")),
    ("NAME", _("Show only caller name (if available)")),
)

FORWARD_MODES = (
    ("DISABLED", "No forward"),
    ("ENABLED", "Active"),
    ("ON_BUSY", "Forward on busy"),
    ("ON_UNAVAILABLE", "Forward on unavailable"),
)


class Extension(models.Model):
    class Meta:
        unique_together = ["event", "extension"]

    lastChanged = models.DateTimeField(editable=False, auto_now=True, verbose_name=_("Last changed"))
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    announcement_lang = models.CharField(max_length=5, choices=LANG_CHOICES, default='de-DE',
                                         verbose_name=_("Announcement Language"))

    type = models.CharField(max_length=16, choices=EXTENSION_TYPES, verbose_name=_("Type"))
    event = models.ForeignKey(Event, on_delete=models.CASCADE, editable=False)

    extension = models.CharField(max_length=32, verbose_name=_("Extension"),
                                 help_text="You can enter characters here, which will be"
                                           " automagically converted into their vanity digits.")
    name = models.CharField(max_length=64, blank=True, verbose_name=_("Name"))
    inPhonebook = models.BooleanField(verbose_name=_("Show in public phonebook"), default=True)
    isInstalled = models.BooleanField(verbose_name=_("Is installed?"), editable=False, default=False)
    ringback_tone = models.ForeignKey(AudioFile, verbose_name=_("Ringback Tone"), on_delete=models.SET_NULL, blank=True,
                                      null=True)
    call_waiting = models.BooleanField(verbose_name=_("Activate call waiting"), default=True,
                                       help_text=_("When this extension is currently on a call and another call"
                                                   " arrives, the other call is NOT indicated that you are busy but"
                                                   " normally ringing. The other incoming call is signaled to your"
                                                   " device. This is usually nicely integrated with desktop SIP phones"
                                                   " and works also with some DECT phones. If you want to signal busy"
                                                   " to the other end when you are on a call, disable call waiting"
                                                   " here."))
    allow_dialout = models.BooleanField(verbose_name=_("Allow dialout"), default=False)

    # Forwards
    forward_mode = models.CharField(max_length=16, choices=FORWARD_MODES, verbose_name=_("Forward mode"),
                                    default="DISABLED",
                                    help_text=_("Forwarding can either be time-based, immediate (time-based with 0s), "
                                                "active if you are busy or if you are unavailable. The last two are "
                                                "almost identical. Forward on busy will also take effect if you are "
                                                "unavailable. However, it also surpresses call waiting for this "
                                                "extension if you are available."))
    forward_extension = models.ForeignKey('Extension', on_delete=models.SET_NULL, blank=True, null=True,
                                          verbose_name=_("To extension"), related_name="forwards_here",
                                          help_text=_("Enter the extension that you want to forward to. Please note"
                                                      " that forwarding only happens if the forward mode is something"
                                                      " other than \"No forward\". You may enter a number here already"
                                                      " if you later want to activate forwarding with a feature "
                                                      "code."))
    forward_delay = models.PositiveIntegerField(verbose_name=_("Activate forward after"),
                                                help_text=_("The delay after which the forward takes effect (only in "
                                                            "Active mode). Yes, 0s means immediate forward :)"),
                                                default=0)

    sip_trunk = models.BooleanField(verbose_name=_("Configure this extension as trunk"), default=False)

    # Only fixed phones
    location = models.CharField(max_length=64, blank=True, verbose_name=_("Location"))

    # GSM / DECT
    registerToken = models.CharField(max_length=32, verbose_name=_("Selfregistration token"), editable=False,
                                     blank=True)

    # GSM
    twoGOptIn = models.BooleanField(verbose_name=_("Use GSM/2G"), help_text=_("Use 2G mobile network. This is the most"
                                                                              " stable technology and recommended to be"
                                                                              " used."), default=True)
    threeGOptIn = models.BooleanField(verbose_name=_("Use UMTS/3G"), help_text=_("Use 3G access access technology "
                                                                                " (highly experimental). Voice"
                                                                                " might not work."), default=True)
    fourGOptIn = models.BooleanField(verbose_name=_("Use LTE/4G"), help_text=_("Use 4G access technology (very new, "
                                                                               "even more experimental, your phone"
                                                                               " will explode ;)"), default=False)

    # DECT handset
    handset = models.ForeignKey(DECTHandset, on_delete=models.SET_NULL, blank=True, null=True)
    displayModus = models.CharField(max_length=16, choices=DISPLAY_MODES, default="NUMBER_NAME",
                                    verbose_name=_("Display modus"))
    useEncryption = models.BooleanField(verbose_name=_("Use encryption"), default=False)

    # SIP
    sipPassword = models.CharField(max_length=16, verbose_name=_("SIP password"), editable=False)
    isPremium = models.BooleanField(verbose_name=_("Provision on premium server"), default=False)

    # GROUP
    group_admins = models.ManyToManyField(User, blank=False, verbose_name=_("Callgroup administrators"),
                                          related_name="adminstrated_callgroups")
    group_members = models.ManyToManyField("Extension",
                                           related_name="callgroups",
                                           through="CallGroupInvite",
                                           through_fields=("group", "extension"))
    group_shortcode = models.CharField(max_length=3, blank=True, verbose_name=_("Group shortcode"),
                                       help_text=_("When a group call arrives, this short code will be shown in "
                                                   "square brackets in front of the caller so that you can see "
                                                   "that this a group call and which group it is coming from."))

    # ANNOUNCEMENT
    announcement_audio = models.ForeignKey(AudioFile, verbose_name=_("Announcement Audio"), on_delete=models.SET_NULL,
                                           blank=True, null=True, related_name="announcement_extensions")

    # rental device
    requestedRentalDevice = models.ForeignKey('RentalDeviceClassification', on_delete=models.SET_NULL, blank=True,
                                              null=True, verbose_name=_("Rental device request"),
                                              help_text=_("Please specify the category of rental device you would"
                                                          " like to get for this extension. Please note that we may not"
                                                          " have sufficiently many devices of this category."
                                                          " As a consequence, we may provide you another or cannot"
                                                          " give you any device at all. You can see the assigned"
                                                          " device below once we processed your request."
                                                          " Just leave this field empty if you bring your own device."),
                                              related_name="request_extensions")
    assignedRentalDevice = models.ForeignKey('RentalDeviceClassification', on_delete=models.SET_NULL, blank=True,
                                              null=True, verbose_name=_("Assigned rental device"),
                                             related_name="assigned_extensions")

    # Information for form configuration

    # The attributes
    # format (<attributeName>, <writePermissionBit>, <readPermissionBit>)
    common_attributes = [
        ("owner", PERM_ADMIN, PERM_ADMIN),
        ("type", PERM_USER, PERM_USER_READ),
        ("allow_dialout", PERM_ADMIN, PERM_ADMIN),
        ("extension", PERM_USER, PERM_USER_READ),
        ("name", PERM_USER, PERM_USER_READ),
        ("location", PERM_USER, PERM_USER_READ),
        ("announcement_lang", PERM_USER, PERM_USER_READ),
        ("ringback_tone", PERM_USER, PERM_USER_READ),
        ("inPhonebook", PERM_USER, PERM_USER_READ),
        ("call_waiting", PERM_USER, PERM_USER_READ),
        ("sip_trunk", PERM_ADMIN, PERM_ADMIN),
        ("requestedRentalDevice", PERM_ORGA,  PERM_ORGA),
        ("assignedRentalDevice", PERM_ADMIN, PERM_ORGA),
        ("forward_mode", PERM_USER, PERM_USER_READ),
        ("forward_extension", PERM_USER, PERM_USER_READ),
        ("forward_delay", PERM_USER, PERM_USER_READ),
    ]
    special_layout_attributes = {
        "requestedRentalDevice",
        "assignedRentalDevice",
        "forward_mode",
        "forward_extension",
        "forward_delay",
    }
    type_attributues = {
        "SIP": [
            ("isPremium", PERM_ORGA, PERM_ORGA),
        ],
        "DECT": [
            ("displayModus", PERM_USER, PERM_USER_READ),
            ("useEncryption", PERM_USER, PERM_USER_READ),
            ("handset", PERM_USER, PERM_USER_READ),
        ],
        "GSM": [
            ("twoGOptIn", PERM_USER, PERM_USER_READ),
            ("threeGOptIn", PERM_USER, PERM_USER_READ),
            ("fourGOptIn", PERM_USER, PERM_USER_READ),
        ],
        "GROUP": [
            ("group_shortcode", PERM_USER, PERM_USER_READ),
        ],
        "APP": [],
        "ANNOUNCEMENT": [
            ("announcement_audio", PERM_USER, PERM_USER_READ),
        ],
        "SPECIAL": [],
    }
    group_display_fields = [
        "owner",
        "extension",
        "name",
        "location",
        "ringback_tone",
        "inPhonebook",
        "group_shortcode",
    ]

    ALLOWED_GROUP_RECURSION_DEPTH = 8

    ALLOWED_TRUNK_TYPES = ("SIP", "DECT", "GSM", "APP")

    def __str__(self):
        return self.extension

    @classmethod
    @lru_cache(maxsize=None)
    def get_field_index(cls, fieldname):
        for index, field in enumerate(cls._meta.fields):
            if field.attname == fieldname:
                return index

    @classmethod
    def calculateFormFields(cls, perm):
        """Calculate form fields to be displayed depending on permissions

        Calculates all attributes that should be shown in a form depending on
        the given permission mask. This function returns a 3-tuple that contains
        the common attributes in the first element and a dictionary with
        attributes per extension type in the second element and a (flat) list
        of attributes that the user should only be able to read.
        """
        common = [(a[0], (a[1] & perm) != 0) for a in cls.common_attributes if (perm & (a[1] | a[2])) != 0]
        types = {
            t: [(a[0], (a[1] & perm) != 0) for a in cls.type_attributues[t] if (perm & (a[1] | a[2])) != 0]
            for t in [type[0] for type in EXTENSION_TYPES]
        }

        commonFields = [c[0] for c in common]
        commonFieldsReadonly = [c[0] for c in common if c[1] == False]

        typeFields = {
            t : [f[0] for f in types[t]] for t in types.keys()
        }
        typeFieldsReadonly = [f[0] for t in types.keys() for f in types[t] if f[1] == False]

        readonly = list(set(commonFieldsReadonly + typeFieldsReadonly))
        return commonFields, typeFields, readonly

    @staticmethod
    def getExtensionDesciption(type):
        for t, d in EXTENSION_TYPES:
            if t == type:
                return d
        raise AttributeError("There is no extension of type '{}'".format(type))

    def has_read_permission(self, user):
        if self.type == "GROUP":
            if user == self.owner or (self.event.isEventAdmin(user)):
                return True
            return self.group_members.filter(owner=user.pk).exists() or \
                   self.group_members.filter(group_admins=user).exists() or \
                   self.group_admins.filter(pk=user.pk).exists()
        else:
            return user == self.owner or (self.event.isEventAdmin(user))

    def has_write_permission(self, user):
        return user == self.owner or (self.event.isEventAdmin(user)) or \
               (self.type == "GROUP" and self.group_admins.filter(pk=user.pk).exists())

    def has_delete_permission(self, user):
        if self.type == "GROUP":
            return user == self.owner or self.event.isEventAdmin(user)
        else:
            return self.has_write_permission(user)

    def __init__(self, *args, **kwargs):
        super(Extension, self).__init__(*args, **kwargs)

        # This is the amazing story of django's object lazy loading mechanism:
        # If we want to know the state of certain fields at the time they were loaded
        # from the database, we need to store it after the object was created. This is
        # what we used to do here all along. However, at some point django started to
        # only partially load objects for some internal use-cases. In this case, the values
        # we desire to see here are (in fact) initialized but not provided. Instead they are
        # lazy-loaded when the attribute is accessed. This lazy loading somehow involves
        # instantiating yet another object with only one attribute and also lazy-loading.
        # Consequently, we got into an endless loop of lazy-reloading the "extension" and
        # the "type" field. We'll mitigate this for the time being by checking if any of
        # "extension" or "type" have the special Deferred value
        extension_index = self.get_field_index("extension")
        type_index = self.get_field_index("type")

        self._incomplete = False
        if len(args) >= extension_index and args[extension_index] is DEFERRED:
            self._incomplete = True
        elif len(args) >= type_index and args[type_index] is DEFERRED:
            self._incomplete = True
        else:
            self._currentExtension = self.extension
            self._currentType = self.type

    def copyToEvent(self, newEvent):
        copy = Extension.objects.get(pk=self.pk)
        copy.pk = None
        copy._currentExtension = None
        copy._currentType = None
        copy.event = newEvent
        copy.save()
        return copy

    def unsubscribe_device(self):
        unsubscribe_msg = messaging.UnsubscribeDeviceMsg(self).makeWireMessage()
        unsubscribe_msg.save()

    @retry_on_db_deadlock()
    def save(self, *args, **kwargs):
        if self._incomplete:
            raise RuntimeError("Incomplete extension objects may not be saved")
        no_messaging = kwargs.pop("no_messaging", False)
        no_transaction_modify = kwargs.pop("no_transaction_modify", False)
        if no_messaging:
            return super().save(*args, **kwargs)
        # We want to save the changes to the object and emit a
        # change the event in an atomic fashion and with sufficient db locks to ensure that
        # nobody can actually sneak into prefix freedom of extensions
        with transaction.atomic():
            # if this is mysql we want isolation level serializable
            if connection.vendor == "mysql" and not no_transaction_modify:
                cursor = connection.cursor()
                cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            # if the extension changed, double check consistency and create db gap and next-key locks on potentially
            # conflicting extension ranges
            if self.extension != self._currentExtension:
                if not self.event.checkIfExtensionIsFree(self.extension, for_update=True,
                                                         current_ext=self._currentExtension):
                    raise AttributeError("Extension taken")

            # if the extension is not new and changed, so we emit a rename message
            if self.extension != self._currentExtension and self.pk is not None:
                rename_msg = messaging.RenameExtensionMsg(self._currentExtension, self).makeWireMessage()
                rename_msg.save()

            if self.type != self._currentType:
                if self.pk is not None and (self.type == "GROUP" or self._currentType == "GROUP"):
                    # the type changed, and was or is now group
                    # delete all admins and members
                    CallGroupInvite.objects.filter(group=self.pk).delete()
                    self.group_admins.all().delete()
                    group_update_msg = messaging.makeGroupUpdateMessage(self)
                    group_update_msg.save()

                self._triggerTypeInit()

            # emit update event
            updateMsg = messaging.makeExtensionUpdateMessage(self)
            updateMsg.save()

            # save our data
            super(Extension, self).save(*args, **kwargs)

            # update object internal storage please note that this occurs after all deadlocks and thus only if it
            # isn't retried.
            self._currentExtension = self.extension
            self._currentType = self.type

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            # as we later-on want to call save() on extension models, we need to ensure that this transaction
            # has the correct transaction isolation level right from the beginning.
            if connection.vendor == "mysql":
                cursor = connection.cursor()
                cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            # check if there are active forwards to this extension. If yes, deactivate them first
            forwards_to_self = Extension.objects.filter(forward_extension=self)
            for extension in forwards_to_self:
                extension.forward_extension = None
                extension.forward_mode = "DISABLED"
                extension.save(no_transaction_modify=True)

            deleteMsg = messaging.makeExtensionDeleteMessage(self, self.extension)
            deleteMsg.save()

            super(Extension, self).delete(*args, **kwargs)

    def generateSipPassword(self):
        self.sipPassword = utils.generateRandomPassword(settings.SIP_PW_LENGTH)

    def _generateRegisterToken(self):
        while True:
            self.registerToken = utils.generateRandomNumberToken(settings.REGISTER_TOKEN_LENGTH)
            # double check it wasn't already taken
            res = Extension.objects.filter(event=self.event, registerToken=self.registerToken)
            if len(res) == 0:
                break
            elif len(res) == 1 and res[0].pk == self.pk:
                break

    def _triggerTypeInit(self):
        if hasattr(self, "typeInit{}".format(self.type)):
            getattr(self, "typeInit{}".format(self.type))()

    def typeInitGSM(self):
        self._generateRegisterToken()

    def typeInitDECT(self):
        self._generateRegisterToken()

    def typeInitSIP(self):
        self.generateSipPassword()

    def getCurrentLending(self):
        res = InventoryLend.objects.select_related().filter(extension=self.pk, backDate__isnull=True)
        if len(res) == 1:
            return res[0]
        else:
            return None

    currentLending = cached_property(getCurrentLending, name="currentLending")

    def recursive_member_search(self, extension, path, max_depth):
        current_path = path + [self.extension]
        if max_depth == 0 and len(self.group_members.all()) > 0:
            raise RecursiveSearchDepthLimitExceededException(current_path)

        if self.extension == extension:
            return current_path
        else:
            for child in self.group_members.all():
                result = child.recursive_member_search(extension, current_path, max_depth-1)
                if result is not None:
                    return result

    @property
    def sip_server(self):
        if self.isPremium:
            return settings.SIP_SERVER_PREMIUM
        else:
            return self.event.regularSipServer

    @property
    def is_forward_target(self):
        return Extension.objects.filter(forward_extension=self).exists()


class WireMessage(models.Model):
    timestamp = models.DateTimeField(editable=False, auto_now_add=True, db_index=True,
                                     verbose_name=_("Event timestamp"))
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name=_("For event"))
    delivered = models.BooleanField(default=False, verbose_name=_("Already delivered"))
    type = models.CharField(max_length=32, verbose_name=_("Event type"))
    data = models.TextField(verbose_name=_("Event data"))

    def __str__(self):
        return "{}  - Delivered: {} - ({})".format(self.type,  self.delivered, self.event.name)

    def getWireData(self):
        data = json.loads(self.data)
        wireMsg = {
            "id": self.pk,
            "timestamp": self.timestamp.timestamp(),
            "type": self.type,
            "data": data
        }
        return wireMsg

    def save(self, **kwargs):
        no_notify = kwargs.pop("no_notify", False)
        super().save()
        if not no_notify:
            notify_clients(self.event_id,
                           {"action": "messagecount", "queuelength": WireMessage.objects.filter(
                               event=self.event, delivered=False).count()
                            })


class IncomingWireMessage(models.Model):
    remote_id = models.PositiveIntegerField(editable=False, verbose_name=_("Remote reference id"))
    timestamp = models.DateTimeField(editable=False, verbose_name=_("Event timestamp"))
    receive_timestamp = models.DateTimeField(editable=False, auto_now_add=True,
                                             verbose_name=_("Timestamp when received"))
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name=_("For event"))
    processed = models.BooleanField(default=False, verbose_name=_("Already processed"))
    type = models.CharField(max_length=16, verbose_name=_("Event type"))
    data = models.TextField(verbose_name=_("Event data"))

    @classmethod
    def parse_from(cls, input):
        if "timestamp" not in input:
            raise messaging.MessageParsingError("Incoming message has no timestamp.")
        elif not isinstance(input["timestamp"], (int, float)):
            raise messaging.MessageParsingError("Incoming message has invalid timestamp format.")
        elif "id" not in input:
            raise messaging.MessageParsingError("Incoming message has no id.")
        elif "type" not in input:
            raise messaging.MessageParsingError("Incoming message has no type.")
        elif "data" not in input:
            raise messaging.MessageParsingError("Incoming message has no data")
        message = cls()
        message.timestamp = datetime.fromtimestamp(input["timestamp"])
        message.remote_id = input["id"]
        message.type = input["type"]
        message.data = json.dumps(input["data"])
        return message


class UserApiKey(models.Model):
    key = models.CharField(max_length=150, verbose_name=_("Api Key"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))

    def __str__(self):
        return self.user.username

    @classmethod
    def regenerate_for(cls, user):
        cls.objects.filter(user=user).delete()
        apikey_obj = cls()
        apikey = utils.generateRandomPassword(64)
        apikey_obj.key = make_password(apikey)
        apikey_obj.user = user
        apikey_obj.save()
        return "{}${}".format(user.pk, apikey)

    def check_apikey(self, key):
        return check_password(key, self.key)


class CallGroupInvite(models.Model):
    class Meta:
        unique_together = ["group", "extension"]

    group = models.ForeignKey(Extension, on_delete=models.CASCADE, blank=False)
    extension = models.ForeignKey(Extension, on_delete=models.CASCADE, blank=False,
                                  related_name="callgroup_memberships")
    inviter = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                                related_name="callgroup_invites")
    invite_reason = models.CharField(max_length=64, blank=True)
    accepted = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    delay_s = models.PositiveIntegerField(default=0)

    def has_read_permission(self, user):
        return self.group.has_read_permission(user)

    def has_write_permission(self, user):
        return self.extension.has_write_permission(user) or (self.group.event.isEventAdmin(user))

    def has_delete_permission(self, user):
        return self.has_write_permission(user) or self.group.has_write_permission(user)

    def save(self, *args, **kwargs):
        no_messaging = kwargs.pop("no_messaging", False)
        if no_messaging:
            return super().save(*args, **kwargs)

        if self.pk is not None:
            # On update send message anyway
            super().save(*args, **kwargs)
            update_msg = messaging.makeGroupUpdateMessage(self.group)
            update_msg.save()
        else:
            # For new invites check if already accepted
            super().save(*args, **kwargs)
            if self.accepted:
                update_msg = messaging.makeGroupUpdateMessage(self.group)
                update_msg.save()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        update_msg = messaging.makeGroupUpdateMessage(self.group)
        update_msg.save()


class RentalDeviceClassification(models.Model):
    name = models.CharField(max_length=64, verbose_name=_("Rental device class name"))

    class Meta:
        ordering = ["name"]

    @classmethod
    def get_event_usage_statistics(cls, event):
        all_classifications = cls.objects.all()
        results = []
        for classification in all_classifications:
            available = InventoryItem.objects.filter(itemType__classification=classification, decommissioned=False) \
                                             .count()
            used = Extension.objects.filter(assignedRentalDevice=classification, event=event).count()
            used += InventoryLend.objects.filter(backDate__isnull=True, item__itemType__classification=classification) \
                                         .exclude(extension__assignedRentalDevice=classification).count()
            unserved = Extension.objects.filter(requestedRentalDevice=classification, assignedRentalDevice__isnull=True,
                                                event=event).count()
            results.append((classification.name, used, available, unserved, available-used))
        return results

    def __str__(self):
        return self.name


class InventoryType(models.Model):
    name = models.CharField(max_length=64, verbose_name=_("Type name"))
    magic = models.CharField(max_length=64, blank=True, null=True,
                             verbose_name=_("Magic type that should happen for this inventory item"))
    auto_recall = models.BooleanField(default=False, verbose_name=_("Automatically recall rental devices of this type "
                                                                    "if they are assigned to an extension"))
    classification = models.ForeignKey(RentalDeviceClassification, on_delete=models.SET_NULL, null=True, blank=True,
                                       verbose_name=_("Rental device class"))

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    itemType = models.ForeignKey(InventoryType, on_delete=models.SET_NULL, null=True, verbose_name=_("Type"))
    description = models.CharField(max_length=128, verbose_name=_("Description"), blank=True)
    barcode = models.CharField(max_length=32, unique=True, verbose_name=_("Barcode"))
    creationDate = models.DateField(auto_now_add=True, verbose_name=_("Creation date"))
    comments = models.TextField(verbose_name=_("Comments"), blank=True)
    serialNumber = models.CharField(max_length=64, blank=True, verbose_name=_("Serial number"))
    mac = models.CharField(max_length=64, blank=True, verbose_name=_("MAC address"))
    decommissioned = models.BooleanField(blank=True, verbose_name=_("This item is decommissioned"))

    def getCurrentMagic(self):
        type = self.itemType
        if type is not None:
            return type.magic
        return ""

    def isCurrentlyOnStock(self):
        res = self.inventorylend_set.filter(backDate__isnull=True)
        return len(res) == 0

    def getCurrentLending(self):
        res = self.inventorylend_set.filter(backDate__isnull=True)
        if len(res) == 0:
            return None
        elif len(res) == 1:
            return res[0]
        else:
            raise LookupError("Item is lended two times currently. This should not happen. Please debug!")

    def getLendingList(self):
        return self.inventorylend_set.order_by("outDate")

    @classmethod
    def find_item(cls, search):
        # for now we just search for barcodes. Maybe this is gonna be more intelligent in the future
        return cls.objects.get(barcode=search)

    @classmethod
    def search_items(cls, search):
        return cls.objects.filter(Q(mac__icontains=search)
                                  | Q(serialNumber__icontains=search)
                                  | Q(description__icontains=search)
                                  | Q(itemType__name__icontains=search)
                                  | Q(comments__icontains=search)
                                  | Q(barcode__icontains=search)).filter(decommissioned=False)

    def _evaluate_item_hooks(self, hook_type, lending=None):
        type_magic = self.itemType.magic
        result = SafeString()
        hooks = inventory.registry.get_hook_list(type_magic, hook_type)
        for hook in hooks:
            res = hook(self) if lending is None else hook(self, lending)
            if res:
                result += res
        return result

    def hook_display_extension(self, lending=None):
        if lending is None:
            lending = self.currentLending
        return self._evaluate_item_hooks(inventory.InventoryHookType.EXTENSION_DISPLAY, lending)

    def hook_display_item(self):
        return self._evaluate_item_hooks(inventory.InventoryHookType.ITEM_DISPLAY)

    def hook_hand_out(self, lending):
        return self._evaluate_item_hooks(inventory.InventoryHookType.ITEM_HAND_OUT, lending)

    def hook_return(self, lending):
        return self._evaluate_item_hooks(inventory.InventoryHookType.ITEM_RETURN, lending)

    def save(self, *args, **kwargs):
        self._evaluate_item_hooks(inventory.InventoryHookType.ITEM_SAVE)
        super().save(*args, **kwargs)


class InventoryLend(ModelAsJsonMixin, models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, verbose_name=_("Item"))
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name=_("Event"))
    extension = models.ForeignKey(Extension, blank=True, null=True, on_delete=models.SET_NULL,
                                  verbose_name=_("Linked Extension"))
    outDate = models.DateTimeField(auto_now_add=True, verbose_name=_("Lending start"))
    backDate = models.DateTimeField(null=True, blank=True, verbose_name=_("Lending end"))
    comment = models.TextField(blank=True, verbose_name=_("Comment"))
    lender = models.CharField(max_length=64, verbose_name=_("Lender"))

    def has_read_permission(self, user):
        return user.is_staff or self.event.isEventAdmin(user)

    def has_write_permission(self, user):
        return user.is_staff or self.event.isEventAdmin(user)

    @classmethod
    def search_lent_items(cls, search, event=None):
        query = cls.objects.select_related().filter(backDate__isnull=True)
        if search != "":
            query = query.filter(
                Q(lender__icontains=search)
                | Q(item__mac__icontains=search)
                | Q(item__serialNumber__icontains=search)
                | Q(item__description__icontains=search)
                | Q(item__itemType__name__icontains=search)
                | Q(item__comments__icontains=search)
                | Q(item__barcode__icontains=search)
                | Q(extension__extension__icontains=search)
                | Q(extension__name__icontains=search)
            )
        if event is None:
            return query
        else:
            return query.filter(event=event)

    def hook_display_extension(self):
        return self.item.hook_display_extension(self)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_pk = self.pk
        self._current_backDate = self.backDate

    def save(self, *args, **kwargs):
        if self._current_pk is None and self.item:
            self.item.hook_hand_out(self)
        elif self.backDate is not None and self._current_backDate is None and self.item:
            self.item.hook_return(self)
        super().save(*args, **kwargs)
        self._current_pk = self.pk
        self._current_backDate = self.backDate


class ExtensionClaim(models.Model):
    class Meta:
        unique_together = ("event", "extension")

        indexes = [
            models.Index(fields=["token"]),
        ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name=_("Event"))
    extension = models.CharField(max_length=32, verbose_name=_("Extension"))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    valid_until = models.DateField(verbose_name=_("Claim valid until"))
    token = models.CharField(max_length=64, unique=True, verbose_name=_("Alphanumeric claim token."))
    mail_sent = models.BooleanField(default=False)

    @classmethod
    def generate(cls, **kwargs):
        while True:
            c = cls(**kwargs)
            c.token = utils.generateRandomPassword(64)
            try:
                old_claim = cls.objects.get(token=c.token)
            except cls.DoesNotExist:
                c.save()
                return c

    def _render_mail_template(self, tmpl):
        ctxt = {
            "event": self.event,
            "claim": self,
            "claim_url": settings.INSTALLATION_BASE_URL + reverse("extension.new") + "?claim=" + self.token,
        }
        return tmpl.render(ctxt)

    def send_invite_email(self):
        subject_template = get_template("event/mails/invite_subject.txt")
        content_template = get_template("event/mails/invite_content.txt")
        if len(self.user.email) > 0:
            subject = self._render_mail_template(subject_template)
            content = self._render_mail_template(content_template)
            send_mail(subject, content, settings.DEFAULT_FROM_EMAIL, [self.user.email])


class ExtensionPool(models.Model):
    extension = models.CharField(max_length=32, verbose_name=_("Extension"), primary_key=True)


class DECTInventorySuggestion(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, verbose_name=_("Inventory item"))
    extension = models.ForeignKey(Extension, on_delete=models.CASCADE, verbose_name=_("Extension used in rent"))
    handset = models.ForeignKey(DECTHandset, on_delete=models.CASCADE, verbose_name=_("Handset"))
