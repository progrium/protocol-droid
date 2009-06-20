from OpenSSL.SSL import SSLv3_METHOD
from twisted.mail.smtp import SMTPSenderFactory, ESMTPSenderFactory, ESMTPSender
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
        self.sentDeferred.addErrback(self.deferred.errback)
        
        username = request.args.get('username', [request.getUser()])[0]
        password = request.args.get('password', [request.getPassword()])[0]
        fromEmail = request.args.get('from', username)[0]
        toEmail = request.args.get('to')[0]
        subject = request.args.get('subject')[0]
        message = StringIO.StringIO('''\
Date: Fri, 6 Feb 2004 10:14:39 -0800
From: %s
To: %s
Subject: %s

%s
''' % (fromEmail, toEmail, subject, request.args.get('body', [''])[0]))
        
        ESMTPSenderFactory.__init__(self, 
            username,
            password,
            fromEmail,
            toEmail,
            message,
            self.sentDeferred,
            retries=0,
            contextFactory=contextFactory,
            requireAuthentication=False,
            requireTransportSecurity=False,)
        #else:
        #    SMTPSenderFactory.__init__(self, 
        #        fromEmail,
        #        toEmail,
        #        message,
        #        self.sentDeferred,
        #        retries=0,)
    
    def buildProtocol(self, addr):
        p = pdroid.connections[self.id] = ESMTPSenderFactory.buildProtocol(self, addr)
        p.factory = self
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
    