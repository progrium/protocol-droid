from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
from twisted.web import client, error, http

import pdroid

class ConnectResource(Resource):
    def getChild(self, name, request):
        if len(request.prepath) < 2:
            return ConnectResource()
        else:
            return pdroid.interface_handler(request.prepath[0], 'http')()

    def render(self, request):
        try:
            protocol, host, port = (request.prepath[0].split(':') + [None])[:3]
        except ValueError, e:
            return "Please specify a protocol, host and optional port in the path. Ex: /http:www.google.com:80"
        port = int(port) if port else None
        request.protocol = protocol
        try:
            d = pdroid.connect(protocol, host, port)
            d.addCallback(lambda x: self.connection_made(request, x))
            return NOT_DONE_YET
        except ImportError, e:
            return e.message
            
    def connection_made(self, request, factory):
        request.redirect('/%s/%s' % (request.protocol, factory.id))
        request.finish()
        