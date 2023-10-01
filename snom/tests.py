from django.test import TestCase

from snom.views import verify_snom_ca

# Create your tests here.

class SnomCaTestCases(TestCase):
    def test_old_ca_valid(self):
        self.assertTrue(verify_snom_ca("emailAdress=security@snom.com,CN=Snom Phone 1,O=Snom Technology AG,L=Berlin,ST=Berlin,C=DE"))
        self.assertTrue(verify_snom_ca("/C=DE/ST=Berlin/L=Berlin/O=Snom Technology AG/CN=Snom Phone 1/emailAddress=security@snom.com"))

    def test_new_ca_valid(self):
        self.assertTrue(verify_snom_ca("emailAddress=security@snom.com,CN=Snom Phone 1 SHA-256,O=snom technology AG,L=Berlin,ST=Berlin,C=DE"))
        self.assertTrue(verify_snom_ca("/C=DE/ST=Berlin/L=Berlin/O=snom technology AG/CN=Snom Phone 1 SHA-256/emailAddress=security@snom.com"))

    def test_invalid_ca_invalid(self):
        self.assertFalse(verify_snom_ca("emailAdress=security@snom.com,CN=Strom Phone 1,O=Snom Technology AG,L=Berlin,ST=Berlin,C=DE"))
        self.assertFalse(verify_snom_ca("/C=DE/ST=Berlin/L=Berlin/O=Strom Technology AG/CN=Snom Phone 1/emailAddress=security@snom.com"))
        self.assertFalse(verify_snom_ca("emailAdress=security@snom.com,CN=Schmom Phone 1,O=Snom Technology AG,L=Berlin,ST=Berlin,C=DE"))
        self.assertFalse(verify_snom_ca("/C=DE/ST=Berlin/L=Berlin/O=Schmom Technology AG/CN=Snom Phone 1/emailAddress=security@snom.com"))
