from pathlib import Path

from celery.utils.log import get_task_logger
from celery.schedules import crontab
from django.conf import settings
from OpenSSL import crypto
from OpenSSL.crypto import FILETYPE_PEM

from epddi.ca import CertificateAuthority
from epddi.models import ClientCertRevocation
from guru3.celery_app import app

logger = get_task_logger(__name__)

EPDDI_CRL_DIR = Path(settings.MEDIA_ROOT) / "epddi_crl"
EPDDI_CRL_FILE = EPDDI_CRL_DIR / "epddi.crl"


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0*60*24, update_cached_epddi_crl.signature(), name='Update CRL')


@app.task(ignore_result=True)
def update_cached_epddi_crl():
    # ensure that output directory exists
    if not EPDDI_CRL_DIR.is_dir():
        # create it
        EPDDI_CRL_DIR.mkdir()

    revoked_list = ClientCertRevocation.objects.all()

    ca = CertificateAuthority(settings.EPDDI_CA_CERT, settings.EPDDI_CA_KEY)
    revocation_list = ca.create_crl(revoked_list)
    crl_pem = crypto.dump_crl(FILETYPE_PEM, revocation_list)
    EPDDI_CRL_FILE.write_bytes(crl_pem)


#app.conf.beat_schedule = {
#    "UpdateCRL": {
#        "task": "epddi.tasks.update_cached_epddi_crl",
#        "schedule": 60.0
#    }
#}
