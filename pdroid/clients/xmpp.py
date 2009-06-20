from twisted.words.protocols.jabber import client, jid, xmlstream
from twisted.words.xish import domish
from twisted.web.resource import Resource
from twisted.internet import reactor


import pdroid

class XMPP(xmlstream.XmlStream):
    pass

class XMPPFactory(xmlstream.XmlStreamFactory):
    protocol = XMPP
    
    def __init__(self, id, request, deferred):
        self.id = id
        self.request = request
        self.deferred = deferred
        
        self.continueTrying = 0
        
        jabber_id = request.args.get('username', [request.getUser()])[0]
        self.jabber_id = jid.JID(jabber_id)
        secret = request.args.get('password', [request.getPassword()])[0]
        a = client.XMPPAuthenticator(self.jabber_id, secret)
        xmlstream.XmlStreamFactory.__init__(self, a)
        
        self.addBootstrap('//event/stream/authd', self.authenticated)
    
    def startedConnecting(self, connector):
        self.connector = connector
    
    def authenticated(self, xmlstream):
        self.deferred.callback(self)
        
        presence = domish.Element(('jabber:client','presence'))
        #presence.addElement('status').addContent('Online')
        xmlstream.send(presence)

        xmlstream.addObserver('/message',  self.messageReceived)
        #xmlstream.addObserver('/presence', debug)
        xmlstream.addObserver('/*',       debug)
    
    def sendMessage(self, to, body):
        message = domish.Element(('jabber:client', 'message'))
        message['to'] = jid.JID(to).full()
        #message['from'] = self.jabber_id.full()
        message['type'] = 'chat'
        message.addElement('body', 'jabber:client', body)
        pdroid.connections[self.id].send(message)
    
    def messageReceived(self, el):
        from_jid = el['from']
        for e in el.elements():
            if e.name == 'body':
                if el['type'] == 'chat':
                    self.chatReceived(from_jid, str(e))
                else:
                    print el.toXml()
    
    def chatReceived(self, fromJid, body):
        pass
    
    def buildProtocol(self, addr):
        p = pdroid.connections[self.id] = xmlstream.XmlStreamFactory.buildProtocol(self, addr)
        p.factory = self
        return p
    
    def dispatchShortcut(self, action):
        # this is currently broken.
        if action == 'send':
            to = self.request.args.get('to', [None])[0]
            body = self.request.args.get('body', [None])[0]
            reactor.callLater(3, self.sendMessage, to, body)
            #reactor.callLater(5, self.connector.disconnect)
        self.request.finish()

def debug(elem):
    print elem.toXml().encode('utf-8')
    print "="*20

class ConnectionResource(Resource):
    def render_GET(self, request):
        return "Try POST"
        
    def render_POST(self, request):
        id = request.prepath[0].split(':')[1]
        conn = pdroid.connections[id]
        to = request.args.get('to', [None])[0]
        body = request.args.get('body', [None])[0]
        conn.factory.sendMessage(to, body)
        return "Sent."

factory = XMPPFactory
default_port = 5222
http_resource = ConnectionResource