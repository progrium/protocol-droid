from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
from twisted.web import client, error, http
from twisted.internet.defer import Deferred

import pdroid

class ConnectorResource(Resource):
    def getChild(self, name, request):
        conn_part = request.prepath[0].split(':')
        try:
            conn = int(conn_part[1])
            protocol = conn_part[0]
            resource = pdroid.from_client(protocol, 'http_resource', None)
            if resource:
                return resource()
            else:
                return ConnectorResource()
        except:
            return ConnectorResource()

    def render(self, request):
        try:
            protocol, host, port = (request.prepath[0].split(':') + [None])[:3]
        except ValueError, e:
            return "Please specify a protocol, host and optional port in the path. Ex: /http:www.google.com:80"
        port = int(port) if port else None
        request.protocol = protocol
        if host == 'listen':
            try:
                pdroid.listen(protocol, port, request)
                request.setResponseCode(http.ACCEPTED)
                return "202 Listening on port %s" % port
            except ImportError, e:
                return e.message
        else:
            try:
                d = Deferred()
                d.addCallback(pdroid.from_client(protocol, 'http_onconnect', http_onconnect))
                d.addErrback(lambda e: write_error(request, e))
                pdroid.connect(protocol, host, port, request, d)
                return NOT_DONE_YET
            except ImportError, e:
                return e.message

def write_error(request, e):
    request.write(str(e))
    request.finish()

def http_onconnect(factory):
    request = factory.request
    if len(request.prepath) > 1:
        factory.dispatchShortcut(request.prepath[1])
    else:
        request.redirect('/%s:%s' % (request.protocol, factory.id))
        request.finish()