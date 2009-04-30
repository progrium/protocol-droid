from twisted.internet import reactor, defer
import time

connections = {}

def connect(protocol, host, port = None):
    module = __import__('.'.join(['pdroid', 'clients', protocol]), globals(), locals(), ['factory', 'default_port'])
    id = str(abs(hash(time.time())))
    f = module.factory(id, defer.Deferred())
    reactor.connectTCP(host, port or module.default_port or 1, f)
    return f.deferred
    
def interface_handler(protocol, interface):
    module = __import__('.'.join(['pdroid', 'clients', protocol]), globals(), locals(), ['interface_handlers'])
    return module.interface_handlers[interface]