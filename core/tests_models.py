from datetime import datetime, timezone, timedelta, date

from unittest import skip
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.db import IntegrityError
from core.models import Extension, Event, WireMessage,  CallGroupInvite, ExtensionClaim


class ExtensionCreationTestCases(TestCase):
    def setUp(self) -> None:
        self.normal_user_0 = User.objects.create_user(username="TestUser", password="password",
                                                    email="testuser@example.org")
        self.normal_user_1 = User.objects.create_user(username="TestUser1", password="password",
                                                    email="testuser1@example.org")
        self.orga_user = User.objects.create_user(username="OrgaUser", password="password",
                                                  email="orgauser@example.org")
        self.admin_user = User.objects.create_user(username="AdminUser", password="password",
                                                   email="adminuser@example.org", is_staff=True)
        self.registration_start = date(2018, 3, 20)
        self.event_end = date(2018, 3, 25)
        self.event = Event.objects.create(name="TestEvent", location="TestCenter", hasGSM=False,
                                          extensionLength=4, extensionStart="2100", extensionEnd="7000",
                                          orgaExtensionStart="1000", orgaExtensionEnd="1999",
                                          start=date(2018, 3, 23),
                                          end=self.event_end,
                                          registrationStart=self.registration_start)
        self.event.organizers.add(self.orga_user)
        self.event.save()
        self.extension_0 = Extension.objects.create(name="TestExtension", location="TestCenter", type="SIP",
                                                    extension="4711", event_id=self.event.id)
        self.extension_1 = Extension.objects.create(name="TestExtension", location="TestCenter", type="SIP",
                                                    extension="345", event_id=self.event.id)
        self.extension_2 = Extension.objects.create(name="TestExtension", location="TestCenter", type="SIP",
                                                    extension="45678", event_id=self.event.id)
        self.extension_claim_0 = ExtensionClaim.objects.create(event=self.event, extension="4712",
                                                               user=self.normal_user_1,
                                                               valid_until=date(2018, 3, 21), token="a")
        self.extension_claim_1 = ExtensionClaim.objects.create(event=self.event, extension="344",
                                                               user=self.normal_user_1,
                                                               valid_until=date(2018, 3, 21), token="b")
        self.extension_claim_2 = ExtensionClaim.objects.create(event=self.event, extension="34222",
                                                               user=self.normal_user_1,
                                                               valid_until=date(2018, 3, 21), token="c")

    # Base
    def test_user_can_create_free_extension(self):
        self.assertTrue(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "4700",
                                                                  today=self.registration_start))

    def test_user_cannot_create_taken_extension(self):
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "4711",
                                                                   today=self.registration_start))
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.orga_user, "4711",
                                                                   today=self.registration_start))

    def test_user_cannot_create_wrong_extension_length(self):
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "47122",
                                                                   today=self.registration_start))
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.orga_user, "47122",
                                                                   today=self.registration_start))

        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "555",
                                                                   today=self.registration_start))
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.orga_user, "555",
                                                                   today=self.registration_start))

    def test_admin_can_create_wrong_extension_length(self):
        self.assertTrue(self.event.userIsAllowedToCreateExtension(self.admin_user, "333",
                                                                  today=self.registration_start))

        self.assertTrue(self.event.userIsAllowedToCreateExtension(self.admin_user, "5555",
                                                                  today=self.registration_start))

    def test_user_cannot_create_free_extension_before_registration(self):
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "4700",
                                                                  today=self.registration_start - timedelta(1)))

    def test_user_cannot_create_free_extension_after_event(self):
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "4700",
                                                                   today=self.event_end + timedelta(1)))
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.orga_user, "4700",
                                                                   today=self.event_end + timedelta(1)))

    # Prefix Postfix Base
    def test_user_cannot_create_prefix_extension(self):
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "3455",
                                                                   today=self.registration_start))

    def test_user_cannot_create_postfix_extension(self):
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "3456",
                                                                   today=self.registration_start))

    def test_can_change_one_digit_more(self):
        self.assertTrue(self.event.checkIfExtensionIsFree("3456",for_update=True,current_ext="345"))
        self.assertTrue(self.event.userIsAllowedToCreateExtension(self.admin_user, "3456",
                                                                 today=self.registration_start,
                                                                 current_ext="345"))
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "3456",
                                                                 today=self.registration_start,
                                                                 current_ext="345"))
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.orga_user, "3456",
                                                                 today=self.registration_start,
                                                                 current_ext="345"))

    def test_can_change_one_digit_less(self):
        self.assertTrue(self.event.checkIfExtensionIsFree("4567",for_update=True,current_ext="45678"))
        self.assertTrue(self.event.userIsAllowedToCreateExtension(self.admin_user, "4567",
                                                                 today=self.registration_start,
                                                                 current_ext="45678"))
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "4567",
                                                                 today=self.registration_start,
                                                                 current_ext="45678"))
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.orga_user, "4567",
                                                                 today=self.registration_start,
                                                                 current_ext="45678"))

    def test_extension_is_free(self):
        self.assertTrue(self.event.checkIfExtensionIsFree("1234"))

    def test_extension_is_occupied(self):
        self.assertFalse(self.event.checkIfExtensionIsFree("45678"))

    # Claim Base
    def test_user_cannot_create_other_extension_claim(self):
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "4712",
                                                                   today=self.registration_start))

    def test_orga_cannot_create_other_extension_claim(self):
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.orga_user, "4712",
                                                                   today=self.registration_start))

    def test_user_can_create_own_extension_claim(self):
        self.assertTrue(self.event.userIsAllowedToCreateExtension(self.normal_user_1, "4712",
                                                                  today=self.registration_start))

    def test_user_can_create_expired_other_extension_claim(self):
        self.assertTrue(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "4712",
                                                                  today=date(2018, 3, 22)))

    # Claim prefix postfix, lengths
    def test_user_cannot_create_other_prefix_extension_claim(self):
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "3440",
                                                                   today=self.registration_start))

    def test_user_cannot_create_other_postfix_extension_claim(self):
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "3422",
                                                                   today=self.registration_start))

    def test_user_can_create_nonstandard_length_claim(self):
        self.assertTrue(self.event.userIsAllowedToCreateExtension(self.normal_user_1, "344",
                                                                  today=self.registration_start))

    # Orga
    def test_user_cannot_create_orga_range(self):
        self.assertFalse(self.event.userIsAllowedToCreateExtension(self.normal_user_0, "1042",
                                                                   today=self.registration_start))

    def test_orga_can_create_orga_range(self):
        self.assertTrue(self.event.userIsAllowedToCreateExtension(self.orga_user, "1042",
                                                                   today=self.registration_start))

    def test_orga_can_create_before_reg_start(self):
        self.assertTrue(self.event.userIsAllowedToCreateExtension(self.orga_user, "4700",
                                                                   today=self.registration_start - timedelta(1)))

class ExtensionTestCase(TestCase):
    def setUp(self):
        self.event = Event.objects.create(name="TestEvent", location="TestCenter", hasGSM=False,
                                     extensionLength=4, extensionStart="2100", extensionEnd="7000",
                                     orgaExtensionStart="1000", orgaExtensionEnd="2099")

    def test_create_extension(self):
        ext_count = Extension.objects.count()
        wire_msg_count = WireMessage.objects.count()
        Extension.objects.create(name="TestExtension", announcement_lang='de-DE',
                                 location="TestCenter", type="SIP",
                                 extension="1000", event_id=self.event.id)
        self.assertEqual(Extension.objects.count(), ext_count+1)
        self.assertEqual(WireMessage.objects.count(), wire_msg_count+1)
        self.assertEqual(WireMessage.objects.get(pk=1).type, 'UPDATE_EXTENSION')

    def test_delete_extension(self):
        Extension.objects.create(name="TestExtension", announcement_lang='de-DE',
                                 location="TestCenter", type="SIP",
                                 extension="1000", event_id=self.event.id)
        ext_count = Extension.objects.count()
        wire_msg_count = WireMessage.objects.count()
        Extension.objects.get(extension='1000').delete()
        self.assertEqual(Extension.objects.count(), ext_count-1)
        self.assertEqual(WireMessage.objects.count(), wire_msg_count+1)
        self.assertEqual(WireMessage.objects.get(pk=1).type, 'UPDATE_EXTENSION')
        self.assertEqual(WireMessage.objects.get(pk=2).type, 'DELETE_EXTENSION')

    def test_modify_extension_name(self):
        Extension.objects.create(name="TestExtension", announcement_lang='de-DE',
                                 location="TestCenter", type="SIP",
                                 extension="1000", event_id=self.event.id)
        ext_count = Extension.objects.count()
        wire_msg_count = WireMessage.objects.count()
        extension = Extension.objects.get(extension='1000')
        last_changed = extension.lastChanged
        extension.name = "ImportantTextExtension"
        extension.save()
        self.assertNotEqual(extension.lastChanged, last_changed)
        self.assertEqual(Extension.objects.count(), ext_count)
        self.assertEqual(WireMessage.objects.count(), wire_msg_count+1)
        self.assertEqual(WireMessage.objects.get(pk=1).type, 'UPDATE_EXTENSION')
        self.assertEqual(WireMessage.objects.get(pk=2).type, 'UPDATE_EXTENSION')

    @skip("Not fixed yet")
    def test_create_extension_twice(self):
        ext_count = Extension.objects.count()
        wire_msg_count = WireMessage.objects.count()
        Extension.objects.create(name="TestExtension", location="TestCenter", type="SIP",
                                 extension="1000", event_id=self.event.id)
        with self.assertRaises(IntegrityError):
            Extension.objects.create(name="TestExtension", location="TestCenter", type="SIP",
                                     extension="1000", event_id=self.event.id)
        self.assertEqual(Extension.objects.count(), ext_count+1)
        self.assertEqual(WireMessage.objects.count(), wire_msg_count+1)
        self.assertEqual(WireMessage.objects.get(pk=1).type, 'UPDATE_EXTENSION')

