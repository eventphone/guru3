from xmlrpc.client import ServerProxy
import ssl
server = ServerProxy('https://<user>:<pass>@hg.eventphone.de:20444/',context=ssl._create_unverified_context())
print(server.getOnlineUsers())
print(server.getOnlineUAStrings())
#server.createOrUpdateNormalUser('SIP')

