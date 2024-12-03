import logging
import base64
from datetime import timedelta


from dal import autocomplete
from django.core.mail import send_mail
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import transaction
from django.shortcuts import redirect
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods
from itertools import count, islice 
from io import BytesIO
from math import sqrt
from random import random
from wkhtmltopdf.views import PDFTemplateView

from PIL import Image

from core.models import UserApiKey, Extension, InventoryLend
from core.forms.user import UserProfileForm
from core.views.event import CurrentEventMixin
from gcontrib.crispy_forms import defaultLayout
from gcontrib.views.edit import CrispyUpdateView
from gcontrib.views.task import JobProcessingView

try:
    from pylibdmtx.pylibdmtx import encode
except ImportError:
    encode = None
    logger = logging.getLogger(__name__)
    logger.warn("Libdtmx not found. Barcodes not available!")


class UserAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = User.objects.get_queryset().order_by('-username')
        if self.q:
            qs = qs.filter(username__istartswith=self.q)
        return qs


@require_http_methods(["POST"])
def send_reset_password_link(request, pk):
    user = User.objects.get(pk=pk)
    form = PasswordResetForm({'email': user.email})
    if form.is_valid():
        form.save(
            request=request,
            use_https=True,
            from_email=settings.DEFAULT_FROM_EMAIL,
            email_template_name='registration/password_reset_email.html')
    return redirect("user.list")


@require_http_methods(["GET"])
def confirm_new_mail(request, signed_data):
    response_template_name = "user/confirm_email_change_clicked.html"
    signer = TimestampSigner()
    try:
        user_pk, email = signer.unsign_object(signed_data, max_age=timedelta(hours=24))
        user = User.objects.get(pk=user_pk)
        user.email = email
        user.save()

        success_context = {
            "success": True,
            "user": user
        }
        return TemplateResponse(request, response_template_name, success_context)
    except SignatureExpired:
        failure_reason = "Confirmation link expired. Please re-trigger email change to get a new link"
    except BadSignature:
        failure_reason = "Invalid confirmation link. Did you copy all content correctly?"
    except User.DoesNotExist:
        failure_reason = "This user doesn't exist anymore."

    fail_context = {
        "success": False,
        "failure_reason": failure_reason
    }
    return TemplateResponse(request, response_template_name, fail_context)


class UserProfileView(CrispyUpdateView):
    form_class = UserProfileForm
    form_helper = defaultLayout(UserProfileForm, _("Save"))

    email_change_mail_subject = "Confirm your new email address"
    email_change_mail_template = "user/confirm_email_change_mail.txt"
    email_change_response_template = "user/confirm_email_change.html"

    # we get the user from the current session, not from some database
    def get_object(self, **kwargs):
        return self.request.user

    def send_mail_change_confirm_email(self, user, new_email):
        email_template = get_template(self.email_change_mail_template)
        signer = TimestampSigner()
        confirm_data = signer.sign_object((user.pk, new_email))
        confirm_url = settings.INSTALLATION_BASE_URL + reverse("user.confirm_new_mail", kwargs={"signed_data": confirm_data})
        email_content = email_template.render({
            "username": user.username,
            "confirm_url": confirm_url,
        })
        send_mail(self.email_change_mail_subject, email_content, settings.DEFAULT_FROM_EMAIL, [new_email])

    def form_valid(self, form):
        # if the email address has changed, we want this to be confirmed via mail
        if "email" in form.changed_data:
            new_mail = form.cleaned_data["email"]
            form.instance.email = form.initial["email"]
            # save all other fields but ignore redirection response
            super().form_valid(form)
            self.send_mail_change_confirm_email(form.instance, new_mail)
            return TemplateResponse(self.request, self.email_change_response_template, {"new_mail": new_mail})
        return super().form_valid(form)


def userSearch(query, request):
    if query == "":
        return User.objects.all()
    else:
        return User.objects.filter(Q(username__icontains=query) | Q(first_name__icontains=query)
                                   | Q(last_name__icontains=query) | Q(email__icontains=query))


@require_http_methods(["POST"])
def delete_api_key(request, pk):
    user = User.objects.get(pk=pk)
    UserApiKey.objects.filter(user=user).delete()
    return redirect("user.list")


class InvoiceView(CurrentEventMixin, PDFTemplateView):
    invoiceLines = None
    user = None
    barcode = None

    def __init__(self, *args, **kwargs):
        self.invoiceLines = []
        self.template_name = 'user/invoice.html';
        self.footer_template = 'user/invoice_footer.html';
        self.header_template = 'user/invoice_header.html';
        return super().__init__(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        event = self.get_event()
        if ('pk' in kwargs):
            self.user = User.objects.get(pk=kwargs['pk'])
        else:
            self.user = self.request.user
        self.filename = 'invoice_{}_{}.pdf'.format(slugify(event.name), slugify(self.user.username))
        extensions = self.InvoiceLine('extension base price (including call flat)', 1.2)
        short_extensions = self.InvoiceLine('short extension', 13.37)
        orga_extensions = self.InvoiceLine('orga range', 0.23)
        premium_extensions = self.InvoiceLine('premium extension', 2.3)
        single_digit_extensions = self.InvoiceLine('single digit', 4.2)
        increasing_extensions = self.InvoiceLine('arithmetic sequence', 4.23)
        nerd_extensions = self.InvoiceLine('nerdy', 23.42)
        prime_extensions = self.InvoiceLine('prime', 3.14)
        callgroups = self.InvoiceLine('callgroup', 1.337)
        ringback_tones = self.InvoiceLine('ringback tones', 0.42)
        devices = self.InvoiceLine('rental devices', 42.23)
        query = Extension.objects.filter(owner=self.user).filter(event=event).order_by('extension')

        is_pl = False

        for e in query:
            name = '{} {} ({})'.format(e.extension, e.name, e.location)
            if e.extension == '1000':
                is_pl = True
            extensions.items.append(name)
            if (len(e.extension) <= 3):
                short_extensions.items.append(name)
            if ((e.extension >= event.orgaExtensionStart) & (e.extension <= event.orgaExtensionEnd)):
                orga_extensions.items.append(name)
            if (e.isPremium):
                premium_extensions.items.append(name)
            if (len(set(e.extension)) == 1):
                single_digit_extensions.items.append(name)
            if (e.extension in ['1234', '2345', '3456', '4567', '5678', '6789', '7890','4321', '5432', '6543', '7654', '8765', '9876']):
                increasing_extensions.items.append(name)
            if (('23' in e.extension) | ('42' in e.extension)):
                nerd_extensions.items.append(name)
            if (all(int(e.extension)%i for i in islice(count(2), int(sqrt(int(e.extension))-1)))):
                prime_extensions.items.append(name)
            if (e.type == 'GROUP'):
                callgroups.items.append(name)
            if (e.ringback_tone is not None):
                ringback_tones.items.append('{} ({})'.format(e.ringback_tone.name, name))

        query = InventoryLend.objects.filter(extension__owner=self.user).filter(event=event)
        seen = set();
        for d in query:
            if (d.item.id not in seen):
                seen.add(d.item.id)
                devices.items.append('#{}: {} ({})'.format(d.item.barcode, d.item.description, d.item.itemType.name))

        self.invoiceLines.append(extensions)
        self.invoiceLines.append(short_extensions)
        self.invoiceLines.append(orga_extensions)
        self.invoiceLines.append(premium_extensions)
        self.invoiceLines.append(single_digit_extensions)
        self.invoiceLines.append(increasing_extensions)
        self.invoiceLines.append(nerd_extensions)
        self.invoiceLines.append(prime_extensions)
        self.invoiceLines.append(callgroups)
        self.invoiceLines.append(ringback_tones)
        self.invoiceLines.append(devices)

        if is_pl:
            query = Extension.objects.filter(event=event)
            sponsoring = 0.0
            for e in query:
                sponsoring += extensions.price
                if (len(e.extension) <= 3):
                    sponsoring += short_extensions.price
                if ((e.extension >= event.orgaExtensionStart) & (e.extension <= event.orgaExtensionEnd)):
                    sponsoring += orga_extensions.price
                if (e.isPremium):
                    sponsoring += premium_extensions.price
                if (len(set(e.extension)) == 1):
                    sponsoring += single_digit_extensions.price
                if (e.extension in ['1234', '2345', '3456', '4567', '5678', '6789', '7890','4321', '5432', '6543', '7654', '8765', '9876']):
                    sponsoring += increasing_extensions.price
                if (('23' in e.extension) | ('42' in e.extension)):
                    sponsoring += nerd_extensions.price
                if (all(int(e.extension)%i for i in islice(count(2), int(sqrt(int(e.extension))-1)))):
                    sponsoring += prime_extensions.price
                if (e.type == 'GROUP'):
                    sponsoring += callgroups.price
                if (e.ringback_tone is not None):
                    sponsoring += ringback_tones.price
            sponsoring_line = self.InvoiceLine('PL sponsoring', sponsoring)
            sponsoring_line.items.append('')
            self.invoiceLines.append(sponsoring_line)

        if settings.C3POST_TRACKING_URL is not None and encode is not None and event.start is not None:
            trackingurl = settings.C3POST_TRACKING_URL.format(event.id, event.start.year, self.user.id)
            postbarcode = encode(trackingurl.encode('utf8'))
            img = Image.frombytes('RGB', (postbarcode.width, postbarcode.height), postbarcode.pixels)
            buffered = BytesIO()
            img.save(buffered, format='PNG')
            self.barcode = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return super().get(request, *args, **kwargs)

    @property
    def net(self):
        return sum(l.total for l in self.invoiceLines)

    @property
    def vat(self):
        return sum(l.total for l in self.invoiceLines) * 0.23

    @property
    def gross(self):
        return self.net + self.vat

    @property
    def due(self):
        return random()/100

    class InvoiceLine:
        price = None
        items = None
        description = ''

        def __init__(self, description, price):
            self.price = price
            self.description = description
            self.items = []

        @property
        def total(self):
            return self.price * len(self.items)


class UserApiKeyCreationView(JobProcessingView):
    def get(self, request, *args, **kwargs):
        return self.render_template()

    def post(self, request, *args, **kwargs):
        user = request.user
        api_key = UserApiKey.regenerate_for(user)
        self.add_context("api_key", api_key)
        return self.render_template()
