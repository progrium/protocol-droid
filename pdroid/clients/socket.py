from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.web.resource import Resource

import pdroid

class Socket(LineReceiver):
    def lineReceived(self, line):
        self.buffer = self.delimiter.join([self.buffer, line])

    def connectionMade(self):
        self.buffer = ''
        self.connected = True
        self.factory.deferred.callback(self.factory)

class SocketFactory(ClientFactory):
    def __init__(self, id, request, deferred):
        if pdroid.connections.get(id):
            raise "Connection id in use"
        self.id = id
        self.request = request
        self.deferred = deferred
        
    def buildProtocol(self, addr):
        p = pdroid.connections[self.id] = Socket()
        p.factory = self
        return p
        
    def clientConnectionLost(self, connector, reason):
        pdroid.connections[self.id].connected = False
        
class ConnectionResource(Resource):
    def render_GET(self, request):
        id = request.prepath[0].split(':')[1]
        conn = pdroid.connections[id]
        data = conn.buffer
        conn.buffer = ''
        if len(data) == 0 and conn.connected == False:
            return "Connection dropped."
        else:
            return data
        
    def render_POST(self, request):
        id = request.prepath[0].split(':')[1]
        conn = pdroid.connections[id]
        conn.transport.write(request.content.getvalue())
        return "Thanks!"

factory = SocketFactory
default_port = None
http_resource = ConnectionResource