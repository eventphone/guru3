from django.test import TestCase
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import Extension, Event, WireMessage


class ExtensionCreateViewTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(username="TestUser", password="password", email="testuser@example.org")
        self.event = Event.objects.create(name="TestEvent", location="TestCenter", hasGSM=False,
                                          extensionLength=4, extensionStart="2100", extensionEnd="7000",
                                          orgaExtensionStart="1000", orgaExtensionEnd="2099",
                                          start=datetime(2018, 3, 23, tzinfo=timezone.utc),
                                          end=timezone.now() + timedelta(days=1),
                                          registrationStart=datetime(2018, 3, 22, tzinfo=timezone.utc))

    def test_create_valid_user_extension(self):
        ext_count = Extension.objects.count()
        wire_msg_count = WireMessage.objects.count()
        self.client.login(username="TestUser", password="password")
        response = self.client.post("/extension/new", {"name": "TestExtension", "location": "TestCenter",
                                                       "type": "SIP", "extension": "2323", "inPhonebook": "on",
                                                       "announcement_lang": "de-DE", "save": "Save",
                                                       "displayModus": "NUMBER_NAME", "forward_mode": "DISABLED",
                                                       "forward_delay": "0"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse('Please correct your inputs!' in str(response.content))
        self.assertEqual(Extension.objects.count(), ext_count+1)
        self.assertEqual(WireMessage.objects.count(), wire_msg_count+1)
        self.assertEqual(WireMessage.objects.get(pk=1).type, 'UPDATE_EXTENSION')

    def test_create_user_extension_in_invalid_range(self):
        ext_count = Extension.objects.count()
        wire_msg_count = WireMessage.objects.count()
        self.client.login(username="TestUser", password="password")
        response = self.client.post("/extension/new", {"name": "TestExtension", "location": "TestCenter",
                                                       "type": "SIP", "extension": "100", "inPhonebook": "on",
                                                       "announcement_lang": "de-DE", "save": "Save",
                                                       "displayModus": "NUMBER_NAME"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please correct your inputs!' in str(response.content))
        self.assertEqual(Extension.objects.count(), ext_count)
        self.assertEqual(WireMessage.objects.count(), wire_msg_count)

    def test_create_user_extension_with_invalid_number(self):
        ext_count = Extension.objects.count()
        wire_msg_count = WireMessage.objects.count()
        self.client.login(username="TestUser", password="password")
        response = self.client.post("/extension/new", {"name": "TestExtension", "location": "TestCenter",
                                                       "type": "SIP", "extension": "1!0", "inPhonebook": "on",
                                                       "save": "Save", "displayModus": "NUMBER_NAME"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please correct your inputs!' in str(response.content))
        self.assertEqual(Extension.objects.count(), ext_count)
        self.assertEqual(WireMessage.objects.count(), wire_msg_count)
