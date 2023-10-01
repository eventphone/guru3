from enum import IntEnum


class GrandStreamUpgradeMode(IntEnum):
    AlwaysCheck = 0
    CheckOnChange = 1
    AlwaysSkip = 2


class GrandStreamUpgradeProvisioningProtocol(IntEnum):
    TFTP = 0
    HTTP = 1
    HTTPS = 2


class GrandStreamUpgradeInterval(IntEnum):
    NoAutoUpgrades = 0
    CustomIntervalMinutes = 1
    EveryDay = 2
    EveryWeek = 3


class GrandStreamKeyPadMenu(IntEnum):
    Unrestricted = 0
    BasicSettings = 1
    ConstraintMode = 2


class GrandStreamWebAccessMode(IntEnum):
    HTTPS = 0
    HTTP = 1


class GrandStreamXMLDownload(IntEnum):
    Disabled = 0
    HTTP = 1
    TFTP = 2
    HTTPS = 3


class GrandStreamDNSMode(IntEnum):
    ARecord = 0
    SRVRecord = 1
    NAPTRandSRV = 2
    UseConfiguredIP = 3


class GrandStreamNATMode(IntEnum):
    No = 0
    STUN = 1
    KeepAlive = 2
    UPnP = 3
    Auto = 4
    VPN = 5


class GrandStreamVoiceCodec(IntEnum):
    PCMU = 0
    G726 = 2
    G723 = 4
    PCMA = 8
    G722WB = 9
    G729AB = 18
    ILBC = 98


class GrandStreamSRTPMode(IntEnum):
    No = 0
    EnabledButNotForce = 1
    EnabledAndForced = 2
    Optional = 3


class GrandStreamSIPTransportMode(IntEnum):
    UDP = 0
    TCP = 1
    TLS = 2


class GrandStreamLineKeyMode(IntEnum):
    Line = 0
    SharedLine = 0
    SpeedDial = 10
    BusyLampField = 11
    PresenceWatcher = 12
    EventlistBLF = 13
    SpeedDialViaActiveAccount = 14
    DialDTMF = 15
    VoiceMail =16
    CallReturn = 17
    Transfer = 18
    CallPark = 19
    Intercom = 20
    LDAPSearch = 21
    MulticastPaging = 23


class GrandStreamMultiPurposeKeyMode(IntEnum):
    SpeedDial = 0
    BusyLampField = 1
    PresenceWatcher = 2
    EventlistBLF = 3
    SpeedDialViaActiveAccount = 4
    DialDTMF = 5
    VoiceMail = 6
    CallReturn = 7
    Transfer = 8
    CallPark = 9
    Intercom = 10
    LDAPSearch = 11
    MulticastPaging = 13


class GrandStreamAccount(IntEnum):
    Account1 = 0
    Account2 = 1
    Account3 = 2
    Account4 = 3

class GrandStreamWallpaperSource(IntEnum):
    Default = 0
    Download = 1
    Uploaded = 3
    ColorBackground = 4

class GrandStreamScreenSaverStatus(IntEnum):
    No = 0
    Yes = 1
    OnlyVPK = 2

class GrandStreamScreenSaverSource(IntEnum):
    Default = 0
    Download = 2

class GrandStreamConfig:
    config = dict()

    # Accounts - Account 1
    @property
    def accounts_account1_general_active(self):
        """Accounts - Account 1 - General - Active"""
        return self.config['P271'] == "1"

    @accounts_account1_general_active.setter
    def accounts_account1_general_active(self, value: bool):
        if value:
            self.config['P271'] = "1"
        else:
            self.config['P271'] = "0"

    @property
    def accounts_account1_general_accountname(self):
        """Accounts - Account 1 - General - Name"""
        return self.config['P270']

    @accounts_account1_general_accountname.setter
    def accounts_account1_general_accountname(self, value: str):
        self.config['P270'] = value

    @property
    def accounts_account1_general_sip_server(self):
        """Accounts - Account 1 - General - SIP Server"""
        return self.config['P47']

    @accounts_account1_general_sip_server.setter
    def accounts_account1_general_sip_server(self, value: str):
        self.config['P47'] = value

    @property
    def accounts_account1_general_outbound_proxy(self):
        """Accounts - Account 1 - General - Outbound Proxy"""
        return self.config['P48']

    @accounts_account1_general_outbound_proxy.setter
    def accounts_account1_general_outbound_proxy(self, value: str):
        self.config['P48'] = value

    @property
    def accounts_account1_general_sip_transport(self):
        """Accounts - Account 1 - General - SIP Transport"""
        return self.config['P130']

    @accounts_account1_general_sip_transport.setter
    def accounts_account1_general_sip_transport(self, value: GrandStreamSIPTransportMode):
        self.config['P130'] = value

    @property
    def accounts_account1_general_audio_codec1(self):
        """Accounts - Account 1 - General - Audio Choice 1"""
        return self.config['P57']

    @accounts_account1_general_audio_codec1.setter
    def accounts_account1_general_audio_codec1(self, value: GrandStreamVoiceCodec):
        self.config['P57'] = value

    @property
    def accounts_account1_general_audio_codec2(self):
        """Accounts - Account 1 - General - Audio Choice 2"""
        return self.config['P58']

    @accounts_account1_general_audio_codec2.setter
    def accounts_account1_general_audio_codec2(self, value: GrandStreamVoiceCodec):
        self.config['P58'] = value

    @property
    def accounts_account1_general_audio_codec3(self):
        """Accounts - Account 1 - General - Audio Choice 3"""
        return self.config['P59']

    @accounts_account1_general_audio_codec3.setter
    def accounts_account1_general_audio_codec3(self, value: GrandStreamVoiceCodec):
        self.config['P59'] = value

    @property
    def accounts_account1_general_audio_codec4(self):
        """Accounts - Account 1 - General - Audio Choice 4"""
        return self.config['P60']

    @accounts_account1_general_audio_codec4.setter
    def accounts_account1_general_audio_codec4(self, value: GrandStreamVoiceCodec):
        self.config['P60'] = value

    @property
    def accounts_account1_general_audio_codec5(self):
        """Accounts - Account 1 - General - Audio Choice 5"""
        return self.config['P61']

    @accounts_account1_general_audio_codec5.setter
    def accounts_account1_general_audio_codec5(self, value: GrandStreamVoiceCodec):
        self.config['P61'] = value

    @property
    def accounts_account1_general_audio_codec6(self):
        """Accounts - Account 1 - General - Audio Choice 6"""
        return self.config['P62']

    @accounts_account1_general_audio_codec6.setter
    def accounts_account1_general_audio_codec6(self, value: GrandStreamVoiceCodec):
        self.config['P62'] = value

    @property
    def accounts_account1_general_audio_codec7(self):
        """Accounts - Account 1 - General - Audio Choice 7"""
        return self.config['P46']

    @accounts_account1_general_audio_codec7.setter
    def accounts_account1_general_audio_codec7(self, value: GrandStreamVoiceCodec):
        self.config['P46'] = value

    @property
    def accounts_account1_general_audio_codec8(self):
        """Accounts - Account 1 - General - Audio Choice 8 - GXP2130 only"""
        return self.config['P98']

    @accounts_account1_general_audio_codec8.setter
    def accounts_account1_general_audio_codec8(self, value: GrandStreamVoiceCodec):
        self.config['P98'] = value

    @property
    def accounts_account1_general_audio_srtp_mode(self):
        """Accounts - Account 1 - General - Audio SRTP-Mode"""
        return self.config['P183']

    @accounts_account1_general_audio_srtp_mode.setter
    def accounts_account1_general_audio_srtp_mode(self, value: GrandStreamSRTPMode):
        self.config['P183'] = value

    @property
    def accounts_account1_general_audio_take_first_sdpmatch(self):
        """Accounts - Account 1 - General - Audio Accept first SDP Match"""
        return self.config['2348'] == "1"

    @accounts_account1_general_audio_take_first_sdpmatch.setter
    def accounts_account1_general_audio_take_first_sdpmatch(self, value: bool):
        if value:
            self.config['P2348'] = "1"
        else:
            self.config['P2348'] = "0"

    @property
    def accounts_account1_general_userid(self):
        """Accounts - Account 1 - General - UserID"""
        return self.config['P35']

    @accounts_account1_general_userid.setter
    def accounts_account1_general_userid(self, value: str):
        self.config['P35'] = value

    @property
    def accounts_account1_general_authid(self):
        """Accounts - Account 1 - General - AuthID"""
        return self.config['P36']

    @accounts_account1_general_authid.setter
    def accounts_account1_general_authid(self, value: str):
        self.config['P36'] = value

    @property
    def accounts_account1_general_authpw(self):
        """Accounts - Account 1 - General - AuthPassword"""
        return self.config['P34']

    @accounts_account1_general_authpw.setter
    def accounts_account1_general_authpw(self, value: str):
        self.config['P34'] = value

    @property
    def accounts_account1_general_name(self):
        """Accounts - Account 1 - General - Name"""
        return self.config['P3']

    @accounts_account1_general_name.setter
    def accounts_account1_general_name(self, value: str):
        self.config['P3'] = value

    @property
    def accounts_account1_network_dnsmode(self):
        """Accounts - Account 1 - Network - DNS-Mode"""
        return self.config['P103']

    @accounts_account1_network_dnsmode.setter
    def accounts_account1_network_dnsmode(self, value: GrandStreamDNSMode):
        self.config['P103'] = value

    @property
    def accounts_account1_network_primary(self):
        """Accounts - Account 1 - Network - PrimaryIP"""
        return self.config['P2308']

    @accounts_account1_network_primary.setter
    def accounts_account1_network_primary(self, value: str):
        self.config['P2308'] = value

    @property
    def accounts_account1_network_nat(self):
        """Accounts - Account 1 - Network - NAT"""
        return self.config['P52']

    @accounts_account1_network_nat.setter
    def accounts_account1_network_nat(self, value: GrandStreamNATMode):
        self.config['P52'] = value

    @property
    def accounts_account1_sip_security_acceptproxyonly(self):
        """Accounts - Account 1 - SIP Settings - Securtiy Settings"""
        return self.config['P2347'] == "1"

    @accounts_account1_sip_security_acceptproxyonly.setter
    def accounts_account1_sip_security_acceptproxyonly(self, value: bool):
        if value:
            self.config['P2347'] = "1"
        else:
            self.config['P2347'] = "0"

    # Accounts - Account 2
    @property
    def accounts_account2_general_active(self):
        """Accounts - Account 2 - General - Active"""
        return self.config['P401'] == "1"

    @accounts_account2_general_active.setter
    def accounts_account2_general_active(self, value: bool):
        if value:
            self.config['P401'] = "1"
        else:
            self.config['P401'] = "0"

    @property
    def accounts_account2_sip_security_acceptproxyonly(self):
        """Accounts - Account 2 - SIP Settings - Securtiy Settings"""
        return self.config['P2447'] == "1"

    @accounts_account2_sip_security_acceptproxyonly.setter
    def accounts_account2_sip_security_acceptproxyonly(self, value: bool):
        if value:
            self.config['P2447'] = "1"
        else:
            self.config['P2447'] = "0"

    # Accounts - Account 3
    @property
    def accounts_account3_general_active(self):
        """Accounts - Account 3 - General - Active"""
        return self.config['P501'] == "1"

    @accounts_account3_general_active.setter
    def accounts_account3_general_active(self, value: bool):
        if value:
            self.config['P501'] = "1"
        else:
            self.config['P501'] = "0"

    @property
    def accounts_account3_sip_security_acceptproxyonly(self):
        """Accounts - Account 3 - SIP Settings - Securtiy Settings"""
        return self.config['P2547'] == "1"

    @accounts_account3_sip_security_acceptproxyonly.setter
    def accounts_account3_sip_security_acceptproxyonly(self, value: bool):
        if value:
            self.config['P2547'] = "1"
        else:
            self.config['P2547'] = "0"

    # Accounts - Account 4
    @property
    def accounts_account4_general_active(self):
        """Accounts - Account 4 - General - Active"""
        return self.config['P601'] == "1"

    @accounts_account4_general_active.setter
    def accounts_account4_general_active(self, value: bool):
        if value:
            self.config['P601'] = "1"
        else:
            self.config['P601'] = "0"

    @property
    def accounts_account4_sip_security_acceptproxyonly(self):
        """Accounts - Account 4 - SIP Settings - Securtiy Settings"""
        return self.config['P2647'] == "1"

    @accounts_account4_sip_security_acceptproxyonly.setter
    def accounts_account4_sip_security_acceptproxyonly(self, value: bool):
        if value:
            self.config['P2647'] = "1"
        else:
            self.config['P2647'] = "0"

    # Settings - LCD Display
    @property
    def settings_lcd_wallpaper_source(self):
        """Settings - LCD Display - Source"""
        return self.config['P2916']

    @settings_lcd_wallpaper_source.setter
    def settings_lcd_wallpaper_source(self, value: GrandStreamWallpaperSource):
        self.config['P2916'] = value

    @property
    def settings_lcd_wallpaper_path(self):
        """Settings - LCD Display - Source"""
        return self.config['P2917']

    @settings_lcd_wallpaper_path.setter
    def settings_lcd_wallpaper_path(self, value: str):
        self.config['P2917'] = value

    @property
    def settings_lcd_screensaver_path(self):
        """Settings - LCD Display - Screensaver Source"""
        return self.config['P934']

    @settings_lcd_screensaver_path.setter
    def settings_lcd_screensaver_path(self, value: str):
        self.config['P934'] = value

    @property
    def settings_lcd_screensaver_timout(self):
        """Settings - LCD Display - Screensaver Timout in Min"""
        return self.config['P2919']

    @settings_lcd_screensaver_timout.setter
    def settings_lcd_screensaver_timout(self, value: int):
        if value < 3:
            raise Exception("Value is to small. Minimum 3")
        if value > 60:
            raise Exception("Value is to large. Max 60")
        self.config['P2919'] = value

    @property
    def settings_lcd_screensaver_source(self):
        """Settings - LCD Display - Screensaver Source"""
        return self.config['P6759']

    @settings_lcd_screensaver_source.setter
    def settings_lcd_screensaver_source(self, value: GrandStreamScreenSaverSource):
        self.config['P6759'] = value

    @property
    def settings_lcd_screensaver_status(self):
        """Settings - LCD Display - Screensaver Source"""
        return self.config['P2918']

    @settings_lcd_screensaver_status.setter
    def settings_lcd_screensaver_status(self, value: GrandStreamScreenSaverStatus):
        self.config['P2918'] = value

    # Settings - XML Applications
    @property
    def settings_xmlapp_idlescreen_downloadmode(self):
        """Settings - XML Applications - IdleScreen XML Download"""
        return self.config['P340']

    @settings_xmlapp_idlescreen_downloadmode.setter
    def settings_xmlapp_idlescreen_downloadmode(self, value: GrandStreamXMLDownload):
        if value == GrandStreamXMLDownload.Disabled:
            self.config.pop('P1349')
        self.config['P340'] = value

    @property
    def settings_xmlapp_download_on_boot(self):
        """Settings - XML Applications - Download Screen XML at Boot"""
        return self.config['P1349'] == "1"

    @settings_xmlapp_download_on_boot.setter
    def settings_xmlapp_download_on_boot(self, value: bool):
        if value:
            self.config['P1349'] = "1"
        else:
            self.config['P1349'] = "0"

    @property
    def settings_xmlapp_server_path(self):
        """Settings - XML Applications - Idle Screen XML Sever Path"""
        return self.config['P341']

    @settings_xmlapp_server_path.setter
    def settings_xmlapp_server_path(self, value: str):
        if "tftp:" in value:
            self.config['P340'] = GrandStreamXMLDownload.TFTP
        elif "http:" in value:
            self.config['P340'] = GrandStreamXMLDownload.HTTP
        elif "https:" in value:
            self.config['P340'] = GrandStreamXMLDownload.HTTPS
        self.config['P341'] = value

    @property
    def settings_keys_line1_mode(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1363']

    @settings_keys_line1_mode.setter
    def settings_keys_line1_mode(self, value: GrandStreamLineKeyMode):
        self.config['P1363'] = value

    @property
    def settings_keys_line1_account(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1364']

    @settings_keys_line1_account.setter
    def settings_keys_line1_account(self, value: GrandStreamAccount):
        self.config['P1364'] = value

    @property
    def settings_keys_line1_description(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1465']

    @settings_keys_line1_description.setter
    def settings_keys_line1_description(self, value: str):
        self.config['P1465'] = value

    @property
    def settings_keys_line1_value(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1466']

    @settings_keys_line1_value.setter
    def settings_keys_line1_value(self, value: str):
        self.config['P1466'] = value

    @property
    def settings_keys_line2_mode(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1365']

    @settings_keys_line2_mode.setter
    def settings_keys_line2_mode(self, value: GrandStreamLineKeyMode):
        self.config['P1365'] = value

    @property
    def settings_keys_line2_account(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1366']

    @settings_keys_line2_account.setter
    def settings_keys_line2_account(self, value: GrandStreamAccount):
        self.config['P1366'] = value

    @property
    def settings_keys_line2_description(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1467']

    @settings_keys_line2_description.setter
    def settings_keys_line2_description(self, value: str):
        self.config['P1467'] = value

    @property
    def settings_keys_line2_value(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1468']

    @settings_keys_line2_value.setter
    def settings_keys_line2_value(self, value: str):
        self.config['P1468'] = value

    @property
    def settings_keys_line3_mode(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1367']

    @settings_keys_line3_mode.setter
    def settings_keys_line3_mode(self, value: GrandStreamLineKeyMode):
        self.config['P1367'] = value

    @property
    def settings_keys_line3_account(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1368']

    @settings_keys_line3_account.setter
    def settings_keys_line3_account(self, value: GrandStreamAccount):
        self.config['P1368'] = value

    @property
    def settings_keys_line3_description(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1469']

    @settings_keys_line3_description.setter
    def settings_keys_line3_description(self, value: str):
        self.config['P1469'] = value

    @property
    def settings_keys_line3_value(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1470']

    @settings_keys_line3_value.setter
    def settings_keys_line3_value(self, value: str):
        self.config['P1470'] = value

    @property
    def settings_keys_line4_mode(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1369']

    @settings_keys_line4_mode.setter
    def settings_keys_line4_mode(self, value: GrandStreamLineKeyMode):
        self.config['P1369'] = value

    @property
    def settings_keys_line4_account(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1370']

    @settings_keys_line4_account.setter
    def settings_keys_line4_account(self, value: GrandStreamAccount):
        self.config['P1370'] = value

    @property
    def settings_keys_line4_description(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1471']

    @settings_keys_line4_description.setter
    def settings_keys_line4_description(self, value: str):
        self.config['P1471'] = value

    @property
    def settings_keys_line4_value(self):
        """Settings - Programmable Keys - LineKeys"""
        return self.config['P1472']

    @settings_keys_line4_value.setter
    def settings_keys_line4_value(self, value: str):
        self.config['P1472'] = value

    @property
    def settings_keys_mpk1_mode(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P323']

    @settings_keys_mpk1_mode.setter
    def settings_keys_mpk1_mode(self, value: GrandStreamMultiPurposeKeyMode):
        self.config['P323'] = value

    @property
    def settings_keys_mpk1_account(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P301']

    @settings_keys_mpk1_account.setter
    def settings_keys_mpk1_account(self, value: GrandStreamAccount):
        self.config['P301'] = value

    @property
    def settings_keys_mpk1_description(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P302']

    @settings_keys_mpk1_description.setter
    def settings_keys_mpk1_description(self, value: str):
        self.config['P302'] = value

    @property
    def settings_keys_mpk1_value(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P303']

    @settings_keys_mpk1_value.setter
    def settings_keys_mpk1_value(self, value: str):
        self.config['P303'] = value

    @property
    def settings_keys_mpk2_mode(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P324']

    @settings_keys_mpk2_mode.setter
    def settings_keys_mpk2_mode(self, value: GrandStreamMultiPurposeKeyMode):
        self.config['P324'] = value

    @property
    def settings_keys_mpk2_account(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P304']

    @settings_keys_mpk2_account.setter
    def settings_keys_mpk2_account(self, value: GrandStreamAccount):
        self.config['P304'] = value

    @property
    def settings_keys_mpk2_description(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P305']

    @settings_keys_mpk2_description.setter
    def settings_keys_mpk2_description(self, value: str):
        self.config['P305'] = value

    @property
    def settings_keys_mpk2_value(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P306']

    @settings_keys_mpk2_value.setter
    def settings_keys_mpk2_value(self, value: str):
        self.config['P306'] = value

    @property
    def settings_keys_mpk3_mode(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P325']

    @settings_keys_mpk3_mode.setter
    def settings_keys_mpk3_mode(self, value: GrandStreamMultiPurposeKeyMode):
        self.config['P325'] = value

    @property
    def settings_keys_mpk3_account(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P307']

    @settings_keys_mpk3_account.setter
    def settings_keys_mpk3_account(self, value: GrandStreamAccount):
        self.config['P307'] = value

    @property
    def settings_keys_mpk3_description(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P308']

    @settings_keys_mpk3_description.setter
    def settings_keys_mpk3_description(self, value: str):
        self.config['P308'] = value

    @property
    def settings_keys_mpk3_value(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P309']

    @settings_keys_mpk3_value.setter
    def settings_keys_mpk3_value(self, value: str):
        self.config['P309'] = value

    @property
    def settings_keys_mpk4_mode(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P326']

    @settings_keys_mpk4_mode.setter
    def settings_keys_mpk4_mode(self, value: GrandStreamMultiPurposeKeyMode):
        self.config['P326'] = value

    @property
    def settings_keys_mpk4_account(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P310']

    @settings_keys_mpk4_account.setter
    def settings_keys_mpk4_account(self, value: GrandStreamAccount):
        self.config['P310'] = value

    @property
    def settings_keys_mpk4_description(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P311']

    @settings_keys_mpk4_description.setter
    def settings_keys_mpk4_description(self, value: str):
        self.config['P311'] = value

    @property
    def settings_keys_mpk4_value(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P312']

    @settings_keys_mpk4_value.setter
    def settings_keys_mpk4_value(self, value: str):
        self.config['P312'] = value

    @property
    def settings_keys_mpk5_mode(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P327']

    @settings_keys_mpk5_mode.setter
    def settings_keys_mpk5_mode(self, value: GrandStreamMultiPurposeKeyMode):
        self.config['P327'] = value

    @property
    def settings_keys_mpk5_account(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P313']

    @settings_keys_mpk5_account.setter
    def settings_keys_mpk5_account(self, value: GrandStreamAccount):
        self.config['P313'] = value

    @property
    def settings_keys_mpk5_description(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P314']

    @settings_keys_mpk5_description.setter
    def settings_keys_mpk5_description(self, value: str):
        self.config['P314'] = value

    @property
    def settings_keys_mpk5_value(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P315']

    @settings_keys_mpk5_value.setter
    def settings_keys_mpk5_value(self, value: str):
        self.config['P315'] = value

    @property
    def settings_keys_mpk6_mode(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P328']

    @settings_keys_mpk6_mode.setter
    def settings_keys_mpk6_mode(self, value: GrandStreamMultiPurposeKeyMode):
        self.config['P328'] = value

    @property
    def settings_keys_mpk6_account(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P316']

    @settings_keys_mpk6_account.setter
    def settings_keys_mpk6_account(self, value: GrandStreamAccount):
        self.config['P316'] = value

    @property
    def settings_keys_mpk6_description(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P317']

    @settings_keys_mpk6_description.setter
    def settings_keys_mpk6_description(self, value: str):
        self.config['P317'] = value

    @property
    def settings_keys_mpk6_value(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P318']

    @settings_keys_mpk6_value.setter
    def settings_keys_mpk6_value(self, value: str):
        self.config['P318'] = value

    @property
    def settings_keys_mpk7_mode(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P329']

    @settings_keys_mpk7_mode.setter
    def settings_keys_mpk7_mode(self, value: GrandStreamMultiPurposeKeyMode):
        self.config['P329'] = value

    @property
    def settings_keys_mpk7_account(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P319']

    @settings_keys_mpk7_account.setter
    def settings_keys_mpk7_account(self, value: GrandStreamAccount):
        self.config['P319'] = value

    @property
    def settings_keys_mpk7_description(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P320']

    @settings_keys_mpk7_description.setter
    def settings_keys_mpk7_description(self, value: str):
        self.config['P320'] = value

    @property
    def settings_keys_mpk7_value(self):
        """Settings - Programmable Keys - MultipurposeKeys"""
        return self.config['P321']

    @settings_keys_mpk7_value.setter
    def settings_keys_mpk7_value(self, value: str):
        self.config['P321'] = value

    # Maintenance - Web Access
    @property
    def maintenance_webaccess_user_password(self):
        """Maintenance - WebAccess - User password"""
        return self.config['P196']

    @maintenance_webaccess_user_password.setter
    def maintenance_webaccess_user_password(self, value: str):
        self.config['P196'] = value

    @property
    def maintenance_webaccess_admin_password(self):
        """Maintenance - WebAccess - Admin password"""
        return self.config['P2']
    
    @maintenance_webaccess_admin_password.setter
    def maintenance_webaccess_admin_password(self, value: str):
        self.config['P2'] = value

    # Maintenance - Upgrade and Provisioning
    @property
    def maintenance_upgrade_mode(self):
        """Maintenance - Upgrade and Provisioning - Mode"""
        return self.config['P238']

    @maintenance_upgrade_mode.setter
    def maintenance_upgrade_mode(self, value: GrandStreamUpgradeMode):
        self.config['P238'] = value

    @property
    def maintenance_upgrade_xmlpassword(self):
        """Maintenance - Upgrade and Provisioning - XML Config File Password"""
        return self.config['P1359']

    @maintenance_upgrade_xmlpassword.setter
    def maintenance_upgrade_xmlpassword(self, value: str):
        self.config['P1359'] = value

    @property
    def maintenance_upgrade_protocol(self):
        """Maintenance - Upgrade and Provisioning - Upgrade via"""
        return self.config['P212']

    @maintenance_upgrade_protocol.setter
    def maintenance_upgrade_protocol(self, value: GrandStreamUpgradeProvisioningProtocol):
        self.config['P212'] = value

    @property
    def maintenance_upgrade_firmwarepath(self):
        """Maintenance - Upgrade and Provisioning - Firmware Server Path"""
        return self.config['P192']

    @maintenance_upgrade_firmwarepath.setter
    def maintenance_upgrade_firmwarepath(self, value: str):
        self.config['P192'] = value

    @property
    def maintenance_upgrade_configpath(self):
        """Maintenance - Upgrade and Provisioning - Config Server Path"""
        return self.config['P237']

    @maintenance_upgrade_configpath.setter
    def maintenance_upgrade_configpath(self, value: str):
        self.config['P237'] = value

    @property
    def maintenance_upgrade_dhcp_allow42_66(self):
        """Maintenance - Upgrade and Provisioning - Allow DHCP Option 43 and Option 66 to Override Server"""
        return self.config['P145'] == "1"

    @maintenance_upgrade_dhcp_allow42_66.setter
    def maintenance_upgrade_dhcp_allow42_66(self, value: bool):
        if value:
            self.config['P145'] = "1"
        else:
            self.config['P145'] = "0"

    @property
    def maintenance_upgrade_dhcp_allow120(self):
        """Maintenance - Upgrade and Provisioning - Allow DHCP Option 120 to Override SIP Server"""
        return self.config['P1411'] == "1"

    @maintenance_upgrade_dhcp_allow120.setter
    def maintenance_upgrade_dhcp_allow120(self, value: bool):
        if value:
            self.config['P1411'] = "1"
        else:
            self.config['P1411'] = "0"

    @property
    def maintenance_upgrade_3cx_provisioning(self):
        """Maintenance - Upgrade and Provisioning - 3CX Auto Provision"""
        return self.config['P1414'] == "1"

    @maintenance_upgrade_3cx_provisioning.setter
    def maintenance_upgrade_3cx_provisioning(self, value: bool):
        if value:
            self.config['P1414'] = "1"
        else:
            self.config['P1414'] = "0"

    @property
    def maintenance_upgrade_intervalmode(self):
        """Maintenance - Upgrade and Provisioning - Automatic Upgrade Mode"""
        return self.config['P194']

    @maintenance_upgrade_intervalmode.setter
    def maintenance_upgrade_intervalmode(self, value: GrandStreamUpgradeInterval):
        if value != GrandStreamUpgradeInterval.CustomIntervalMinutes:
            self.config.pop("P193")
        self.config['P194'] = value

    @property
    def maintenance_upgrade_intervalminutes(self):
        """Maintenance - Upgrade and Provisioning - Automatic Upgrade Mode"""
        return self.config['P193']

    @maintenance_upgrade_intervalminutes.setter
    def maintenance_upgrade_intervalminutes(self, value: int):
        if value < 60:
            raise Exception("Interval to Short. Minimum 60")
        if value > 86400:
            raise Exception("Interval to long. Maximum 86400")
        self.config['P194'] = GrandStreamUpgradeInterval.CustomIntervalMinutes
        self.config['P193'] = value

    @property
    def maintenance_upgrade_upgradehour(self):
        """Maintenance - Upgrade and Provisioning - Automatic Upgrade Hour"""
        return self.config['P285']

    @maintenance_upgrade_upgradehour.setter
    def maintenance_upgrade_upgradehour(self, value: int):
        if value < 0:
            raise Exception("Interval to Short. Minimum 0")
        if value > 24:
            raise Exception("Interval to long. Maximum 24")
        self.config['P194'] = GrandStreamUpgradeInterval.EveryDay
        self.config['P285'] = value

    @property
    def maintenance_upgrade_upgradeday(self):
        """Maintenance - Upgrade and Provisioning - Automatic Upgrade Day"""
        return self.config['P286']


    @maintenance_upgrade_upgradeday.setter
    def maintenance_upgrade_upgradeday(self, value: int):
        if value < 0:
            raise Exception("Interval to Short. Minimum 0")
        if value > 6:
            raise Exception("Interval to long. Maximum 6")
        self.config['P194'] = GrandStreamUpgradeInterval.EveryWeek
        self.config['P286'] = value

    @property
    def maintenance_upgrade_disable_sipnotifyauth(self):
        """Maintenance - Upgrade and Provisioning - Disable SIP NOTIFY Authentication"""
        return self.config['P4428'] == "1"

    @maintenance_upgrade_disable_sipnotifyauth.setter
    def maintenance_upgrade_disable_sipnotifyauth(self, value: bool):
        if value:
            self.config['P4428'] = "1"
        else:
            self.config['P4428'] = "0"

    @property
    def maintenance_language(self, value: str):
        return self.config['P1362']

    @maintenance_language.setter
    def maintenance_language(self, value: str):
        self.config['P1362'] = value

    # Maintenance - Security
    @property
    def maintenance_security_keypadmenu(self):
        """Maintenance - Security - Configuration via Keypad Menu"""
        return self.config['P1357']

    @maintenance_security_keypadmenu.setter
    def maintenance_security_keypadmenu(self, value: GrandStreamKeyPadMenu):
        self.config['P1357'] = value

    @property
    def maintenance_security_keypadlocking(self):
        """Maintenance - Security - Enable STAR Key Keypad Locking"""
        return self.config['P1382'] == "1"

    @maintenance_security_keypadlocking.setter
    def maintenance_security_keypadlocking(self, value: bool):
        if value:
            self.config['P1382'] = "1"
        else:
            self.config['P1382'] = "0"

    @property
    def maintenance_security_keypad_password(self):
        """Maintenance - Security - Password to Lock/Unlock"""
        return self.config['P1383']

    @maintenance_security_keypad_password.setter
    def maintenance_security_keypad_password(self, value: str):
        if value != None:
            self.config['P1382'] = "1"
        self.config['P1383'] = value

    @property
    def maintenance_security_webaccessmode(self):
        """Maintenance - Security - WebAccessMode"""
        return self.config['P1650']

    @maintenance_security_webaccessmode.setter
    def maintenance_security_webaccessmode(self, value: GrandStreamWebAccessMode):
        self.config['P1650'] = value

    # LDAP Settings

    @property
    def ldap_server(self):
        return self.config['P8020']

    @ldap_server.setter
    def ldap_server(self, value: str):
        self.config['P8020'] = value

    @property
    def ldap_port(self):
        return self.config['P8021']

    @ldap_port.setter
    def ldap_port(self, value: int):
        self.config['P8021'] = value

    @property
    def ldap_user(self):
        return self.config['P8023']

    @ldap_user.setter
    def ldap_user(self, value: str):
        self.config['P8023'] = value

    @property
    def ldap_password(self):
        return self.config['P8024']

    @ldap_password.setter
    def ldap_password(self, value: str):
        self.config['P8024'] = value

    @property
    def ldap_number_filter(self):
        return self.config['P8025']

    @ldap_number_filter.setter
    def ldap_number_filter(self, value: str):
        self.config['P8025'] = value

    @property
    def ldap_name_filter(self):
        return self.config['P8026']

    @ldap_name_filter.setter
    def ldap_name_filter(self, value: str):
        self.config['P8026'] = value

    @property
    def ldap_version(self):
        return self.config['P8027']

    @ldap_version.setter
    def ldap_version(self, value: str):
        self.config['P8027'] = value

    @property
    def ldap_name_attributes(self):
        return self.config['P8028']

    @ldap_name_attributes.setter
    def ldap_name_attributes(self, value: str):
        self.config['P8028'] = value

    @property
    def ldap_number_attributes(self):
        return self.config['P8029']

    @ldap_number_attributes.setter
    def ldap_number_attributes(self, value: str):
        self.config['P8029'] = value

    @property
    def ldap_display_name(self):
        return self.config['P8030']

    @ldap_display_name.setter
    def ldap_display_name(self, value: str):
        self.config['P8030'] = value

    @property
    def ldap_base_dn(self):
        return self.config['P8022']

    @ldap_base_dn.setter
    def ldap_base_dn(self, value: str):
        self.config['P8022'] = value

    @property
    def ldap_sort(self):
        return self.config['P8033'] == 1

    @ldap_sort.setter
    def ldap_sort(self, value: bool):
        if value:
            self.config['P8033'] = 1
        else:
            self.config['P8033'] = 0

    @property
    def ldap_lookup_incoming(self):
        return self.config['P8035'] == 1

    @ldap_lookup_incoming.setter
    def ldap_lookup_incoming(self, value: bool):
        if value:
            self.config['P8035'] = 1
        else:
            self.config['P8035'] = 0

    @property
    def ldap_lookup_outgoing(self):
        return self.config['P8034'] == 1

    @ldap_lookup_outgoing.setter
    def ldap_lookup_outgoing(self, value: bool):
        if value:
            self.config['P8034'] = 1
        else:
            self.config['P8034'] = 0

    @property
    def ldap_lookup_display_name(self):
        return self.config['P8036']

    @ldap_lookup_display_name.setter
    def ldap_lookup_display_name(self, value: str):
        self.config['P8036'] = value

    def generate_config(self):
        configfile = '<?xml version="1.0" encoding="UTF-8" ?>\r\n'
        configfile += '<!-- Grandstream XML Provisioning Configuration -->\r\n'
        configfile += '<gs_provision version="1">\r\n'
        configfile += '<config version="1">\r\n'
        for key, value in self.config.items():
            if type(value) == str:
                configfile += "<{0}>{1}</{0}>\r\n".format(key, value)
            else:
                num = int(value)
                configfile += "<{0}>{1}</{0}>\r\n".format(key, num)
        configfile += '</config>\r\n'
        configfile += '</gs_provision>'
        return configfile
