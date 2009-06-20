from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet
from twisted.web.server import Site

from pdroid.interfaces.http import ConnectorResource

class Options(usage.Options):
    optParameters = [["port", "p", 8080, "The port number to listen on."]]


class ProtocolDroidMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "pdroid"
    description = "Universal (read: HTTP) protocol adapter"
    options = Options

    def makeService(self, options):
        """
        Construct a TCPServer from a factory defined in myproject.
        """
        return internet.TCPServer(int(options["port"]), Site(ConnectorResource()))

serviceMaker = ProtocolDroidMaker()
