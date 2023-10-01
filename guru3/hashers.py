from django.contrib.auth.hashers import BasePasswordHasher, mask_hash
from django.utils.crypto import constant_time_compare
import hashlib
from collections import OrderedDict
from django.utils.translation import gettext_lazy as _

class Guru2PasswordHasher(BasePasswordHasher):
    """
    Guru2 Password Hasher for Backward compatibility
    Only used to verify hashes. New one won't be generated
    """
    algorithm = "guru2"

    def salt(self):
        return ''

    def encode(self, password, salt):
        raise NotImplementedError()

    def verify(self, password, encoded):
        algorithm, salt, hash = encoded.split('$', 2)
        assert algorithm == self.algorithm
        encoded_2 = hashlib.md5((salt + ":" + password).encode()).hexdigest()
        return constant_time_compare(hash, encoded_2)

    def safe_summary(self, encoded):
        return OrderedDict([
            (_('algorithm'), self.algorithm),
            (_('hash'), mask_hash(encoded, show=3)),
        ])

    def harden_runtime(self, password, encoded):
        pass
