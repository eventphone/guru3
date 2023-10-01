import datetime
import uuid
from typing import Dict, List
from pathlib import Path

from django.utils.timezone import now

from OpenSSL import crypto
from OpenSSL.crypto import FILETYPE_PEM

from epddi.utils import datetime_to_asn1time_string


class CertificateAuthority:
    def __init__(self, ca_cert_path, ca_key_path):
        ca_cert_data = Path(ca_cert_path).read_text()
        ca_key_data = Path(ca_key_path).read_text()
        self._ca_cert = crypto.load_certificate(FILETYPE_PEM, ca_cert_data)
        self._ca_key = crypto.load_privatekey(FILETYPE_PEM, ca_key_data)

    def _raw_cert(self):
        cert = crypto.X509()
        cert.set_version(2)
        cert.set_serial_number(uuid.uuid4().int)
        cert.set_issuer(self._ca_cert.get_subject())
        return cert

    def issue_router_cert(self, csr: crypto.X509Req, subject_override: Dict[str, str]):
        cert = self._raw_cert()
        subject = csr.get_subject()
        for key, value in subject_override.items():
            setattr(subject, key, value)
        cert.set_subject(subject)
        cert.set_pubkey(csr.get_pubkey())
        validity_start = now() - datetime.timedelta(minutes=5)
        validity_end = now() + datetime.timedelta(days=2 * 365)
        validity_start.replace(hour=0, minute=0, second=0, microsecond=0)
        validity_end.replace(hour=0, minute=0, second=0, microsecond=0)
        cert.set_notBefore(datetime_to_asn1time_string(validity_start))
        cert.set_notAfter(datetime_to_asn1time_string(validity_end))
        extensions = [
            crypto.X509Extension(b'subjectKeyIdentifier', 0, b'hash', subject=cert),
            crypto.X509Extension(b'authorityKeyIdentifier', 0, b'keyid,issuer', issuer=self._ca_cert),
            crypto.X509Extension(b'basicConstraints', True, b'CA:FALSE'),
            crypto.X509Extension(b'nsCertType', False, b'client'),
            crypto.X509Extension(b'extendedKeyUsage', False, b'clientAuth'),
            crypto.X509Extension(b'keyUsage', False, b'digitalSignature')
        ]
        cert.add_extensions(extensions)
        cert.sign(self._ca_key, 'sha256')
        return cert

    def create_crl(self, revocation_entries: List['epddi.models.ClientCertRevocation']):
        crl = crypto.CRL()
        crl.set_version(2)
        crl.set_lastUpdate(datetime_to_asn1time_string(now()))
        crl.set_nextUpdate(datetime_to_asn1time_string(now() + datetime.timedelta(days=7)))

        for entry in revocation_entries:
            revoked = crypto.Revoked()
            revoked.set_reason(entry.revocation_reason.encode("ascii"))
            revoked.set_rev_date(datetime_to_asn1time_string(entry.revocation_time))
            revoked.set_serial(entry.cert_serial_hex.encode("ascii"))
            crl.add_revoked(revoked)

        crl.sign(self._ca_cert, self._ca_key, b"sha256")
        return crl

