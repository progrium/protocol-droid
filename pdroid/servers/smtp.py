from zope.interface import implements
from twisted.internet import defer
from twisted.mail import smtp
from twisted.mail import protocols
from twisted.web import client

import datetime
import md5
import email
import urllib

HOOKAH_HOST = 'hookah.webhooks.org'

class MessageDelivery:
    implements(smtp.IMessageDelivery)
    
    def __init__(self, factory):
        self.factory = factory
    
    def receivedHeader(self, helo, origin, recipients):
        return "Received: from %s\n\tby localhost\n\tfor %s; %s" % (helo, origin, datetime.datetime.today().isoformat())
    
    def validateFrom(self, helo, origin):
        # All addresses are accepted
        return origin
    
    def validateTo(self, user):
        # Only messages directed to mailhooks.com are accepted.
        callbacks = self.factory.callbacks
        if user.dest.domain in callbacks.keys():
            return lambda: Message(callbacks[user.dest.domain])
        elif '*' in callbacks.keys():
            return lambda: Message(callbacks['*'])
        raise smtp.SMTPBadRcpt(user)

class Message:
    implements(smtp.IMessage)
    
    def __init__(self, callback_url):
        self.callback_url = callback_url
        self.lines = []
    
    def lineReceived(self, line):
        self.lines.append(line)
    
    def eomReceived(self):
        data = parse_mail("\n".join(self.lines))
        data['_url'] = self.callback_url
        postdata = urllib.urlencode(data)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': str(len(postdata)),
        }
        client.getPage('http://%s/' % HOOKAH_HOST, followRedirect=0, method='POST', headers=headers, postdata=postdata).addErrback(if_fail)
        self.lines = None
        return defer.succeed(None)
    
    def connectionLost(self):
        # There was an error, throw away the stored lines
        self.lines = None

class SMTPFactory(protocols.ESMTPFactory):
    callbacks = {}
    
    def __init__(self, port, request):
        self.port = port
        self.request = request
        self.callbacks['*'] = request.args.get('callback', [None])[0]
        smtp.SMTPFactory.__init__(self)
        self.delivery = MessageDelivery(self)
    
    def buildProtocol(self, addr):
        p = smtp.SMTPFactory.buildProtocol(self, addr)
        p.delivery = self.delivery
        return p
    
    def relisten(self, request):
        pass

def if_fail(reason):
    if reason.getErrorMessage()[0:3] in ['301', '302', '303']:
        return

def parse_mail(data):
    msg = email.message_from_string(data)
    prefix = md5.new(data).hexdigest()
    attachments = []
    body_html = None
    body = None
    for part in msg.walk():
        if part.get_content_type() == 'text/plain' and not part.get_filename(False):
            body = part.get_payload(decode=True)
        elif part.get_content_type() == 'text/html' and not part.get_filename(False):
            body_html = part.get_payload(decode=True)
        else: 
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            
            filename = part.get_filename()
            counter = 1
            if not filename:
                filename = 'part-%03d%s' % (counter, 'bin')
                counter += 1
            fp = os.tmpfile()
            fp.write(part.get_payload(decode=True))
            attachments.append([filename, fp.tell(), fp])
    # 'headers': dict([k,v for k,v in msg.items() if not 'mime' in k.lower() and not 'multipart' in v.lower()]),
    data = {
        'to': msg['to'],
        'from': msg['from'],
        'subject': msg['subject'],
        'body': body,}
    if body_html:
        data['body_html'] = body_html
    if len(attachments):
        for attachment in attachments:
            data['file'+str(attachments.index(attachment))] = attachment
    return data

default_port = 25
factory = SMTPFactory