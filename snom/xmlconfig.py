from zoneinfo import ZoneInfo

from django.template.loader import get_template

__zoneinfo_snom_dict = {
     'Europe/Amsterdam': "NLD+1",
     'Europe/Athens': "GRC+2",
     'Europe/Belfast': "IRL-0",
     'Europe/Berlin' : "GER+1",
     'Europe/Bratislava': "SVK+1",
     'Europe/Brussels': "BEL+1",
     'Europe/Bucharest': "ROU+2",
     'Europe/Budapest': "HUN+1",
     'Europe/Chisinau': "MDA+2",
     'Europe/Copenhagen': "DNK+1",
     'Europe/Dublin': "IRL-0",
     'Europe/Gibraltar': "GIB+1",
     'Europe/Helsinki': "FIN+2",
     'Europe/Istanbul': "TUR+2",
     'Europe/Kaliningrad': "RUS+2",
     'Europe/Kiev': "UKR+2",
     'Europe/Kirov': "RUS+3",
     'Europe/Lisbon': "PRT-0",
     'Europe/London': "GBR-0",
     'Europe/Luxembourg': "LUX+1",
     'Europe/Madrid': "ESP+1",
     'Europe/Minsk': "RUS+3",
     'Europe/Moscow': "RUS+3",
     'Europe/Nicosia': "CYP+2",
     'Europe/Oslo': "NOR+1",
     'Europe/Paris': "FRA+1",
     'Europe/Prague': "CZE+1",
     'Europe/Riga': "LVA+2",
     'Europe/Rome': "ITA+1",
     'Europe/Saratov': "RUS+4",
     'Europe/Simferopol': "UKR+2",
     'Europe/Sofia': "BGR+2",
     'Europe/Stockholm': "SWE+1",
     'Europe/Tallinn': "EST+2",
     'Europe/Tirane': "ALB+1",
     'Europe/Ulyanovsk': "RUS+3",
     'Europe/Uzhgorod': "UKR+2",
     'Europe/Vienna': "AUT+1",
     'Europe/Volgograd': "RUS+3",
     'Europe/Warsaw': "POL+1",
     'Europe/Zagreb': "HRV+1",
     'Europe/Zaporozhye': "UKR+2",
     'Europe/Zurich': "CHE+1",
 }


def zoneinfo_to_snom_tz(zone: ZoneInfo):
    return __zoneinfo_snom_dict.get(zone.key, "GER+1")


def render_xml_config(snom_phone, inventory_item, inventory_lend, prov_url, event):
    context = {
        "snom_phone": snom_phone,
        "inventory_item": inventory_item,
        "inventory_lend": inventory_lend,
        "prov_url": prov_url,
        "timezone": zoneinfo_to_snom_tz(event.timezone)
    }
    template = get_template("snom/provisioning.xml")
    return template.render(context)
