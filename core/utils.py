import functools
import random
import string
import textwrap
import time
import itertools

from django.conf import settings
from django.db import OperationalError
from django.urls import reverse

def _normalize_one_digit(digit):
    transform_map = {
        "ABC": "2",
        "DEF": "3",
        "GHI": "4",
        "JKL": "5",
        "MNO": "6",
        "PQRS": "7",
        "TUV": "8",
        "WXYZ": "9",
    }
    if digit.isdigit():
        return digit
    else:
        for l, d in transform_map.items():
            if digit in l:
                return d
        return ""


def get_apikey_header(request):
    api_key_header_field = "HTTP_" + settings.AUTH_KEY_HEADER.upper()
    return request.META.get(api_key_header_field)


def extension_normalize(ext):
    return "".join(map(_normalize_one_digit, ext.upper()))


def generateRandomPassword(length):
    return "".join([random.SystemRandom().choice(
        string.ascii_lowercase +
        string.ascii_uppercase +
        string.digits) for _ in range(length)])

def generateRandomNumberToken(length):
    return "".join([random.SystemRandom().choice(string.digits) for _ in range(length)])


def generate_register_token():
    token_plain = "".join([random.SystemRandom().choice(
        string.ascii_uppercase +
        string.digits) for _ in range(10)])
    return token_plain[0:5] + "-" + token_plain[5:]

def mac_format(mac_str):
    mac_str = mac_str.upper().replace(":", "").replace("-", "")
    return ":".join(textwrap.wrap(mac_str, 2))


def ipei_normalize(ipei):
    ipei = ipei.replace(" ", "")
    return ipei[:5] + " " + ipei[5:12] + " " + ipei[12]


def retry_on_db_deadlock(max_retries=4, exponential_backoff=2, initial_backoff=0.1):
    def decorator_func(decorated_func):
        @functools.wraps(decorated_func)
        def returned_func(*args, **kwargs):
            retries = max_retries
            current_backoff = initial_backoff
            while True:
                try:
                    return decorated_func(*args, **kwargs)
                except OperationalError as e:
                    if str(e).find("Deadlock found") != -1:
                        if current_backoff is not None:
                            time.sleep(current_backoff)
                            current_backoff *= exponential_backoff
                        if retries > 0:
                            retries -= 1
                            continue
                    raise  # re-raise if non-matching exception-text or retries exhausted
        return returned_func
    return decorator_func


def task_url(task):
    return reverse("celery.taskstatus", kwargs={"taskid": task.id})

def batched(iterable, n):
    # batched('ABCDEFG', 3) → ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while batch := tuple(itertools.islice(it, n)):
        yield batch