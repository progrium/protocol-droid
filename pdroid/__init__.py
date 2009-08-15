from twisted.internet import reactor
from twisted.internet.defer import Deferred
import time

connections = {}
listeners = {}

def connect(protocol, host, port = None, request = None, deferred = None):
    module = __import__('.'.join(['pdroid', 'clients', protocol]), globals(), locals(), ['factory', 'default_port'])
    id = str(abs(hash(time.time())))
    f = module.factory(id, request, deferred or Deferred())
    reactor.connectTCP(host, port or module.default_port or 1, f)
    return f.deferred

def listen(protocol, port = None, request = None, token = None):
    module = __import__('.'.join(['pdroid', 'servers', protocol]), globals(), locals(), ['factory', 'default_port'])
    if port in listeners:
        f = listeners[port]
        f.relisten(request)
    else:
        f = listeners[port] = module.factory(port, request, token)
        reactor.listenTCP(port or module.default_port or 1, f)
    return f
    
def from_client(protocol, name, default):
    m = __import__('.'.join(['pdroid', 'clients', protocol]), globals(), locals(), ['http_onconnect', 'http_resource'])
    return getattr(m, name, default)