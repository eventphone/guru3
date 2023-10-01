from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_
from model_guru2 import *
from model_guru3 import *
import icu
import string

srcdb = create_engine('mysql://thomas:Kennwort1@localhost/guru2',encoding='utf8')
dstdb = create_engine('mysql://thomas:Kennwort1@localhost/guru3_staging?charset=utf8mb4',encoding='utf8')
SrcSession = sessionmaker(bind=srcdb)
DstSession = sessionmaker(bind=dstdb)
srcdb = SrcSession()
dstdb = DstSession()

#dstdb.query(CoreWiremessage).delete()
#dstdb.query(CoreExtension).delete()
#dstdb.query(AuthUser).filter(AuthUser.is_staff == 0).delete()
#dstdb.query(CoreEvent).filter(CoreEvent.id > 2).delete()
#dstdb.commit()

events = srcdb.query(Event).order_by(Event.event_start.desc()).all()
cacheevents = {}

for event in events:
    if event.event_name == "_PERMANENT":
        continue
    if event.event_name == "_PERMANENT_PUBLIC":
        continue
    if event.event_name == "_EPVPN":
        continue
    if event.event_name == "EPVPN":
        continue
    if event.event_name == "guru_debug_event":
        continue
    dstevent = CoreEvent()
    dstevent.name = event.event_name
    dstevent.start = datetime.fromtimestamp(event.event_start).strftime('%Y-%m-%d')
    dstevent.end = datetime.fromtimestamp(event.event_end).strftime('%Y-%m-%d')
    try:
        dstevent.descriptionDE = unicode(event.event_description_de, "utf-8")
    except:
        dstevent.descriptionDE = event.event_description_de.decode('iso-8859-1').encode("utf-8")
    try:
        dstevent.descriptionEN = unicode(event.event_description_en, "utf-8")
    except:
        dstevent.descriptionEN =event.event_description_en.decode('iso-8859-1').encode("utf-8")
    dstevent.hasGSM = event.has_gsm
    dstevent.url = event.event_url
    try:
        dstevent.location = unicode(event.event_location, "utf-8")
    except:
        dstevent.location = event.event_location.decode('iso-8859-1').encode('utf8')
    dstevent.extensionStart = event.ext_range_start
    dstevent.extensionEnd = event.ext_range_end
    dstevent.orgaExtensionStart = event.orga_ext_range_start
    dstevent.orgaExtensionEnd = event.orga_ext_range_end
    dstevent.registrationStart = datetime.fromtimestamp(event.event_valid_from).strftime('%Y-%m-%d')
    dstevent.extensionLength = 4
    dstevent.eventStreamTarget = "/dev/null"
    dstdb.add(dstevent)
    cacheevents[event.event_name] = dstevent
dstdb.commit()
print "Events are commited"

cacheauthusers = {}
for authuser in dstdb.query(AuthUser).all():
    cacheauthusers[string.strip(string.lower(authuser.username))] = authuser
print "Existing AuthUsers cached"

users = srcdb.query(User).all()
for user in users:
    username = string.strip(string.lower(user.username))
    if cacheauthusers.has_key(username):
        continue
    dstuser = AuthUser()
    dstuser.username = username
    dstuser.first_name = unicode(user.firstname, "utf-8")
    try:
        dstuser.last_name = unicode(user.name, "utf-8")
    except:
        dstuser.last_name = user.name.decode('iso-8859-1').encode("utf-8")
    if user.id == 24:
        print "found"
    dstuser.is_active = user.confirmed
    dstuser.email = user.email
    if user.md5password:
        dstuser.password = "guru2$"+user.username+"$"+user.md5password
    else:
        dstuser.password = ""
    dstuser.is_superuser = 0
    dstuser.is_staff = 0
    if (user.joined):
        dstuser.date_joined = datetime.fromtimestamp(user.joined).strftime('%Y-%m-%d')
    else:
        dstuser.date_joined = 0
    dstuser.last_login = 0
    dstdb.add(dstuser)
    #print "inserting User: " + user.username
dstdb.commit()
print "Users are commited"

cacheusers = {}
for user in dstdb.query(AuthUser).all():
    cacheusers[string.strip(string.lower(user.username))] = user
print "Existing AuthUsers cached"

extensions = srcdb.query(Phonebook)\
    .filter(or_(Phonebook.phone_type == 1, Phonebook.phone_type == 5, Phonebook.phone_type == 20))\
    .all()
for ext in extensions:
    dstext = CoreExtension()
    if ext.event_name == "_PERMANENT":
        continue
    elif ext.event_name == "_PERMANENT_PUBLIC":
        ext.event_name = "PERMANENT_PUBLIC"
    if ext.event_name == "_EPVPN":
        continue
    if ext.event_name == "guru_debug_event":
        continue
    event = cacheevents.get(ext.event_name)
    if event == None:
        print "event not found: " + ext.event_name
        continue
    username = string.strip(string.lower(ext.user))
    if ext.user == "thomasDOTwtf":
        print "debug"
    if cacheusers.has_key(username):
        user = cacheusers[username]
    else:
        user = None
    #user = dstdb.query(AuthUser).filter(AuthUser.username == ext.user).first()
    #if user == None:
    #    print "user not found: "+ ext.user
    try:
        dstext.name = unicode(ext.ext_name, "utf-8")
    except:
        dstext.name = ext.ext_name.decode('iso-8859-1').encode("utf-8")
    dstext.extension = ext.extension
    try:
        dstext.location = unicode(ext.location, "utf-8")
    except:
        dstext.location = ext.location.decode('iso-8859-1').encode("utf-8")
    dstext.event = event
    dstext.owner = user
    dstext.inPhonebook = ext.phonebook_entry
    dstext.isInstalled = ext.installed
    dstext.lastChanged = ext.timestamp
    dstext.isPremium = 0
    dstext.useEncryption = 0
    if ext.phone_type == 20:
        dstext.type = 'GSM'
        dstext.registerToken = ext.abbrev_destination
    elif ext.phone_type == 1:
        dstext.type = 'DECT'
        dstext.registerToken = 'DECTGEN'
    elif ext.phone_type == 5:
        dstext.type = 'SIP'
        dstext.sipPassword = ext.ext_password
    dstext.displayModus = 'num'
    if dstext.sipPassword == None or dstext.sipPassword == '':
        dstext.sipPassword = 'SIPGEN'
    if dstext.registerToken == None or dstext.sipPassword == '':
        dstext.registerToken = ''
    dstdb.add(dstext)
dstdb.commit()

print "Extensions committed"

