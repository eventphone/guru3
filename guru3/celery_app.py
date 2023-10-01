import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "guru3.settings")

from django.conf import settings

app = Celery('guru3')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
