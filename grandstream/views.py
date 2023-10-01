import re

from django.http import HttpResponse, HttpResponseBadRequest

from core.models import Extension
from grandstream.models import GrandstreamPhone
from grandstream.crypto import encrypt_data_for_gammel_grandstream
from grandstream.grandstream import *
from grandstream.grandstream_screen import get_defaultscreen
from guru3 import settings

gammelstream_extractor_re = re.compile("^.*HW (?P<hw_model>.*) SW (?P<sw_version>[0-9]+\.[0-9]+\.[0-9]+).*$")

def create_baseconfig(scheme:str, host:str, mac: str):
    host = host.split(':')[0]
    config = GrandStreamConfig()
    config.accounts_account1_general_active = False
    config.accounts_account1_network_dnsmode = GrandStreamDNSMode.ARecord
    config.accounts_account1_network_nat = GrandStreamNATMode.KeepAlive
    config.accounts_account1_sip_security_acceptproxyonly = True
    config.accounts_account2_general_active = False
    config.accounts_account2_sip_security_acceptproxyonly = True
    config.accounts_account3_general_active = False
    config.accounts_account3_sip_security_acceptproxyonly = True
    config.accounts_account4_general_active = False
    config.accounts_account4_sip_security_acceptproxyonly = True
    config.maintenance_security_webaccessmode = GrandStreamWebAccessMode.HTTPS
    if scheme.upper() == "HTTPS":
        config.maintenance_upgrade_protocol = GrandStreamUpgradeProvisioningProtocol.HTTPS
    elif scheme.upper() == "HTTP":
        config.maintenance_upgrade_protocol = GrandStreamUpgradeProvisioningProtocol.HTTP
    else:
        config.maintenance_upgrade_protocol = GrandStreamUpgradeProvisioningProtocol.TFTP
    config.maintenance_upgrade_configpath = "{0}/grandstream/config".format(host)
    config.maintenance_upgrade_mode = GrandStreamUpgradeMode.AlwaysSkip
    config.maintenance_upgrade_dhcp_allow42_66 = False
    config.maintenance_upgrade_dhcp_allow120 = False
    config.maintenance_upgrade_disable_sipnotifyauth = True
    config.maintenance_upgrade_intervalmode = GrandStreamUpgradeInterval.CustomIntervalMinutes
    config.maintenance_upgrade_intervalminutes = 60
    config.maintenance_upgrade_3cx_provisioning = False
    config.settings_xmlapp_download_on_boot = True
    config.settings_xmlapp_idlescreen_downloadmode = GrandStreamXMLDownload.HTTP
    config.settings_xmlapp_server_path = "{0}/grandstream/screen/{1}".format(host, mac)
    return config


def customize_config(config: GrandStreamConfig, extension: Extension):
    config.accounts_account1_general_active = True
    config.accounts_account1_general_sip_server = extension.sip_server
    config.accounts_account1_general_sip_transport = GrandStreamSIPTransportMode.UDP
    config.accounts_account1_general_outbound_proxy = extension.sip_server
    config.accounts_account1_general_authid = extension.extension
    config.accounts_account1_general_userid = extension.extension
    config.accounts_account1_general_authpw = extension.sipPassword
    if extension.name is not None:
        config.accounts_account1_general_name = extension.name
        config.accounts_account1_general_accountname = extension.name
    else:
        config.accounts_account1_general_name = extension.extension
        config.accounts_account1_general_accountname = extension.extension
    config.accounts_account1_general_audio_srtp_mode = GrandStreamSRTPMode.No
    config.accounts_account1_general_audio_take_first_sdpmatch = True
    config.accounts_account1_general_audio_codec1 = GrandStreamVoiceCodec.G722WB
    config.accounts_account1_general_audio_codec2 = GrandStreamVoiceCodec.PCMA
    config.accounts_account1_general_audio_codec3 = GrandStreamVoiceCodec.PCMA
    config.accounts_account1_general_audio_codec4 = GrandStreamVoiceCodec.PCMA
    config.accounts_account1_general_audio_codec5 = GrandStreamVoiceCodec.PCMA
    config.accounts_account1_general_audio_codec6 = GrandStreamVoiceCodec.PCMA
    config.accounts_account1_general_audio_codec7 = GrandStreamVoiceCodec.PCMA
    return config


def key_config(config: GrandStreamConfig):
    config.settings_keys_line1_mode = GrandStreamLineKeyMode.Line
    config.settings_keys_line1_account = GrandStreamAccount.Account1
    config.settings_keys_line1_description = "Line 1"
    config.settings_keys_line1_value = ""

    config.settings_keys_line2_account = GrandStreamAccount.Account1
    config.settings_keys_line2_account = GrandStreamAccount.Account1
    config.settings_keys_line3_account = GrandStreamAccount.Account1

#    config.settings_keys_mpk1_account = GrandStreamAccount.Account1
#    config.settings_keys_mpk1_mode = GrandStreamMultiPurposeKeyMode.SpeedDial
#    config.settings_keys_mpk1_description = "ERNA"
#    config.settings_keys_mpk1_value = "8330"
#
#    config.settings_keys_mpk2_account = GrandStreamAccount.Account1
#    config.settings_keys_mpk2_mode = GrandStreamMultiPurposeKeyMode.SpeedDial
#    config.settings_keys_mpk2_description = "TIME"
#    config.settings_keys_mpk2_value = "8463"
#
#    config.settings_keys_mpk3_account = GrandStreamAccount.Account1
#    config.settings_keys_mpk3_mode = GrandStreamMultiPurposeKeyMode.SpeedDial
#    config.settings_keys_mpk3_description = "WITZ"
#    config.settings_keys_mpk3_value = "9489"

#    config.settings_keys_mpk4_account = GrandStreamAccount.Account1
#    config.settings_keys_mpk4_mode = GrandStreamMultiPurposeKeyMode.SpeedDial
#    config.settings_keys_mpk5_account = GrandStreamAccount.Account1
#    config.settings_keys_mpk5_mode = GrandStreamMultiPurposeKeyMode.SpeedDial
#    config.settings_keys_mpk6_account = GrandStreamAccount.Account1
#    config.settings_keys_mpk6_mode = GrandStreamMultiPurposeKeyMode.SpeedDial
#
#    config.settings_keys_mpk7_account = GrandStreamAccount.Account1
#    config.settings_keys_mpk7_mode = GrandStreamMultiPurposeKeyMode.SpeedDial
#    config.settings_keys_mpk7_description = "TNB"
#    config.settings_keys_mpk7_value = "0311"
    return config


def ldap_config(config: GrandStreamConfig, event_name: str):
    config.ldap_server = "guru3.eventphone.de"
    config.ldap_port = 389
    config.ldap_user = "cn=" + event_name
    config.ldap_password = "$random"
    config.ldap_number_filter = "(telephoneNumber=%)"
    config.ldap_name_filter = "(|(sn=%)(l=%))"
    config.ldap_version = "3"
    config.ldap_name_attributes = "sn l"
    config.ldap_number_attributes = "telephoneNumber"
    config.ldap_display_name = "%sn %l"
    config.ldap_base_dn = "dc=eventphone,dc=de"
    config.ldap_sort = True
    config.ldap_lookup_incoming = True
    config.ldap_lookup_outgoing = True
    config.ldap_lookup_display_name = "sn"
    return config


def apply_firmwareupdate_gxp2130(config: GrandStreamConfig, version:str):
    config.maintenance_upgrade_mode = GrandStreamUpgradeMode.AlwaysCheck
    if version == "1.0.4":
        config.maintenance_upgrade_firmwarepath = "cdn.eventphone.de/firmwares/gxp2130/Release_GXP2130_1.0.7.97"
    elif version == "1.0.7":
        config.maintenance_upgrade_firmwarepath = "cdn.eventphone.de/firmwares/gxp2130/Release_GXP2130_1.0.8.56"
    elif version == "1.0.8":
        config.maintenance_upgrade_firmwarepath = "cdn.eventphone.de/firmwares/gxp2130/Release_GXP2130_1.0.9.69"
    else:
        config.maintenance_upgrade_firmwarepath = "cdn.eventphone.de/firmwares/gxp2130/current"

    return config

def apply_magic(config: GrandStreamConfig, model:str, version:str):
    if model == "gxp2130":
        config.accounts_account1_general_audio_codec8 = GrandStreamVoiceCodec.PCMA
        config.settings_lcd_wallpaper_source = GrandStreamWallpaperSource.Download
        config.settings_lcd_wallpaper_path = "cdn.eventphone.de/wallpaper/default"
        config.settings_lcd_screensaver_source = GrandStreamScreenSaverSource.Download
        config.settings_lcd_screensaver_status = GrandStreamScreenSaverStatus.Yes
        config.settings_lcd_screensaver_path = "cdn.eventphone.de/screensaver/default/screensaver.xml"
        config = apply_firmwareupdate_gxp2130(config, version)
    return config


def password_config(config: GrandStreamConfig, admin_password:str, user_password:str):
    config.maintenance_webaccess_user_password = user_password
    config.maintenance_webaccess_admin_password = admin_password
    return config


def get_initial_config(request, mac):
    devices = GrandstreamPhone.objects.filter(mac__iexact=mac)
    if devices.count() != 0:
        return HttpResponseBadRequest("device already initialized")
    device = GrandstreamPhone.createForMac(mac)
    config = create_baseconfig(request.scheme, request.get_host(), mac)
    config.maintenance_upgrade_xmlpassword = str(device.preSharedPassword)
    password_config(config, device.adminPassword, device.userPassword)
    data = config.generate_config()
    device.userAgent = request.META.get("HTTP_USER_AGENT", None)
    device.save()
    return HttpResponse(data, content_type="application/octet-stream")


def get_encrypted_config(request, mac):
    devices = GrandstreamPhone.objects.filter(mac__iexact=mac)
    if devices.count() == 0:
        return HttpResponseBadRequest("device has not been initialized")
    device = devices.first()
    device.userAgent = request.META.get("HTTP_USER_AGENT", None)
    config = create_baseconfig(request.scheme, request.get_host(), mac)
    config.maintenance_upgrade_xmlpassword = str(device.preSharedPassword)
    password_config(config, device.adminPassword, device.userPassword)
    config.accounts_account1_general_name = "InventoryNoLending"
    item = device.get_inventory_item()
    if item is not None:
        lending = item.getCurrentLending()
        if lending is not None and lending.extension is not None:
            config = customize_config(config, lending.extension)
            config = key_config(config)
            config.maintenance_language = lending.extension.announcement_lang.split("-")[0]
        else:
            config.maintenance_language = 'en'
        if lending is not None and lending.event is not None:
            config = ldap_config(config, lending.event.name)
    res = gammelstream_extractor_re.match(device.userAgent)
    if res is not None:
        config = apply_magic(config, res.group("hw_model").lower(), res.group("sw_version").lower())
    configdata = config.generate_config()
    data = encrypt_data_for_gammel_grandstream(str(device.preSharedPassword), str.encode(configdata))
    device.save()
    return HttpResponse(data, content_type="application/octet-stream")


def get_screen_config(request, mac):
    return HttpResponse(get_defaultscreen(), content_type="application/octet-stream")
