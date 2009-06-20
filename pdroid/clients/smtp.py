from OpenSSL.SSL import SSLv3_METHOD
from twisted.mail.smtp import ESMTPSenderFactory, ESMTPSender
from twisted.internet.ssl import ClientContextFactory
from twisted.internet.defer import Deferred
from twisted.web.resource import Resource
import StringIO

import pdroid


class SMTP(ESMTPSender):
    def connectionMade(self):
        ESMTPSender.connectionMade(self)
        self.factory.deferred.callback(self.factory)

class SMTPFactory(ESMTPSenderFactory):
    protocol = SMTP
    
    def __init__(self, id, request, deferred):
        # Create a context factory which only allows SSLv3 and does not verify
        # the peer's certificate.
        contextFactory = ClientContextFactory()
        contextFactory.method = SSLv3_METHOD
        
        self.id = id
        self.request = request
        self.deferred = deferred
        self.sentDeferred = Deferred()
        
        fromEmail = request.args.get('from', request.args.get('username', [request.getUser()]))[0]
        
        ESMTPSenderFactory.__init__(self, 
            request.args.get('username', [request.getUser()])[0],
            request.args.get('password', [request.getPassword()])[0],
            fromEmail[0],
            request.args.get('to')[0],
            StringIO.StringIO('''\
Date: Fri, 6 Feb 2004 10:14:39 -0800
From: %s
To: %s
Subject: %s

%s
''' % (fromEmail[0], 
        request.args.get('to')[0], 
        request.args.get('subject')[0], 
        request.args.get('body', [''])[0])),
            self.sentDeferred,
            retries=0,
            contextFactory=contextFactory,)
    
    def buildProtocol(self, addr):
        p = pdroid.connections[self.id] = ESMTPSenderFactory.buildProtocol(self, addr)
        return p

        
def http_onconnect(factory):
    request = factory.request
    def success(request):
        request.write("OK Sent")
        request.finish()
    def fail(x, request):
        request.write(str(x))
        request.finish()
    factory.sentDeferred.addCallback(lambda x: success(request))
    factory.sentDeferred.addErrback(lambda x: fail(x, request))

factory = SMTPFactory
default_port = 25
    