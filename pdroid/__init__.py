from twisted.internet import reactor
from twisted.internet.defer import Deferred
import time

connections = {}

def connect(protocol, host, port = None, request = None):
    module = __import__('.'.join(['pdroid', 'clients', protocol]), globals(), locals(), ['factory', 'default_port'])
    id = str(abs(hash(time.time())))
    f = module.factory(id, request, Deferred())
    reactor.connectTCP(host, port or module.default_port or 1, f)
    return f.deferred
    
    
def from_client(protocol, name, default):
    m = __import__('.'.join(['pdroid', 'clients', protocol]), globals(), locals(), ['http_onconnect', 'http_resource'])
    return getattr(m, name, default)