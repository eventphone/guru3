import django
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guru3.settings')
from django.conf import settings
# Overwrite Logging to log to stderr instead of a file
settings.LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
           'level': 'INFO',
           'class': 'logging.StreamHandler',
           'stream': sys.stderr,
           'formatter': 'verbose'
       },
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(name)s %(process)d %(thread)d %(message)s',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
django.setup()

import asyncio
import re
import sys
import time
from email.parser import BytesParser
from urllib.parse import urlparse
import signal
from asgiref.sync import sync_to_async

from aiosmtpd.controller import Controller

from core.models import RegistrationEmailToken

token_re = re.compile("[A-Z0-9]{5}-[A-Z0-9]{5}")


def confirm_token(token):
    try:
        token_obj = RegistrationEmailToken.objects.get(token=token)
        token_obj.confirmed = True
        token_obj.save()
        print(f"Token {token} confimed.")
        return True,'250 Message accepted for delivery'
    except RegistrationEmailToken.DoesNotExist:
        print(f"Did not find token {token}.")
        return True,'550 Token not valid'
    except Exception:
        return False,'421 Internal error, please retry'

def emergency_halt():
    time.sleep(1)
    os.abort()

class RegisterMailHandler:
    def __init__(self, host):
        self._host = host

    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        if address != f"register@{self._host}":
            return '550 not relaying to that domain'
        envelope.rcpt_tos.append(address)
        return '250 OK'

    async def handle_DATA(self, server, session, envelope):
        print('Message from %s' % envelope.mail_from)
        print('Message for %s' % envelope.rcpt_tos)
        print('Message data:\n')
        for ln in envelope.content.decode('utf8', errors='replace').splitlines():
            print(f'> {ln}'.strip())
        print('End of message')
        parser = BytesParser()
        mail = parser.parsebytes(envelope.content, headersonly=True)
        subject = mail.get("Subject")
        if subject is not None:
            token = token_re.search(subject)
            if token:
                success,result = await sync_to_async(confirm_token, thread_sensitive=True)(token[0])
                if not success:
                    asyncio.get_running_loop().run_in_executor(None, emergency_halt)
                return result
            else:
                return '550 Token missing'
        else:
            return '550 Subject missing'


parsed_url = urlparse(settings.INSTALLATION_BASE_URL)
host = parsed_url.hostname

controller = Controller(RegisterMailHandler(host), hostname="*", port=settings.SMTP_REGISTER_BRIDGE_PORT, ident="Token validation service")
controller.start()
print(f"Starting controller for {host} on port {settings.SMTP_REGISTER_BRIDGE_PORT}")
signal.sigwait([signal.SIGTERM, signal.SIGINT])
