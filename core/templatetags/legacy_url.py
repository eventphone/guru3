from random import choice

from django import template
from django.template.defaulttags import url, URLNode
from django.template.exceptions import  TemplateSyntaxError
from django.urls.base import get_urlconf
from django.utils.safestring import SafeText
from django.urls.resolvers import get_resolver

from core.converters import LegacyHostingConverter

register = template.Library()
queries = ('ENV=()%20%7B%20%3A%3B%20%7D%3B%20%2Fsbin%2Fpoweroff',
           'LD_PRELOAD=secure.so',
           'SQL=Robert%27)%3B+DROP+TABLE+extensions%3B--',
           'JSESSIONID=3EA0C1DA-7033-4229-935A-8F893CE46C38',
           'utm_source=E-Corp',
           'm=2&Werror&Wall',
           'debug=false',
           'backend=192.168.1.86&method=runcontainer&container=microsoft%25iis',
           'js=%3Cscript%3Ealert(%22XSS%22);%3C/script%3E',
           'url=c%3A%2Fwindows%2Fsystem32%2Fcalc.exe',
           'apitoken=c60f1de66cba44aaa863cb6fab964a27',
           'environment=production',
           'font=Comic%20Sans&force=true',
           'admin=true&force=false',
           'payload=X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*',
           'transport=X.25&port=COM2&speed=9600',
           'isencrypted=true',
           'subsystem=plugins&lib=system32.dll',
           'state=init&src=autoexec.bat&drivers=config.sys',
           's=getrich.tld%252F2011%252F09%252Fhow-to-make-money-on-ebay-with-old-magazines+Launching+an+eBay+business'
           '+is+straightforward+fun+and+can+be+done+from+the+comfort+of+your+personal+home+ways+to+make+money'
           '+with+ebay+marketing+items+',
           'full_eventphone_experience=yes&level=expert',
           'enable_tracking_pixel=true',
           'enable_nsa_backdoor=true',
           'five_eyes_certified_content=true',
           'hack_client&ip_address=379.612.554.114',
           'password_successfully_validated=true',
           'authmethod=plaintext',
           'encryption=base64&hash=md5',
           'listusers=all&unhash_password=1',
           '$top=42&$skip=13&$filter=extension+ne+null+and+type+eq+premium&$select=location,name&$search=admin&$expand=device',
           '#iefix',
           '%20event[id%00=42"+AND+1=0--',
           'expert_mode=1')


class TemplateRandom:
    """
    Mimic an interface that looks like a template expression but ignores the context and solves
    to a random choice of things
    """
    def __init__(self, choices):
        self._choices = choices

    def resolve(self, context):
        return choice(self._choices)


@register.tag(name="legacy_url")
def add_legacy_url_parameter(parser, token):
    result = url(parser, token)
    if not isinstance(result.view_name.var, SafeText):
        raise TemplateSyntaxError("legacy_url tag can only process constant view names. No variables!")
    return LegacyURLNode(result.view_name, result.args, result.kwargs, result.asvar)


class LegacyURLNode(URLNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.next_url = None
        if "next_url" in self.kwargs:
            self.next_url = self.kwargs.pop("next_url")
        self._populate_legacy_extension(self.view_name.resolve({}))

    def render(self, context):
        rendered_url = super().render(context)
        if self.asvar:
            return ""
        if self.next_url is not None:
            return rendered_url + '?next_url=' + str(self.next_url.resolve(context)) + '&' + choice(queries)
        else:
            return rendered_url + '?' + choice(queries)

    def _populate_legacy_extension(self, view_name):
        urlconf = get_urlconf()
        resolver = get_resolver(urlconf)
        possibilities = resolver.reverse_dict.getlist(view_name)
        legacy_hosting_converter_names = set()
        for possibility, pattern, defaults, converters in possibilities:
            for key, converter in converters.items():
                if isinstance(converter, LegacyHostingConverter):
                    legacy_hosting_converter_names.add(key)
                    if len(legacy_hosting_converter_names) > 1:
                        raise TemplateSyntaxError("View is unsuitable for legacy_url. Multiple legacy hosting converters with different names detected.")
                    self.kwargs[key] = TemplateRandom(LegacyHostingConverter.extensions)

