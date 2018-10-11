import logging

from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet.protocol import Factory, ClientFactory
from twisted.internet.task import LoopingCall
from twisted.python import log

from pyipv8.ipv8.configuration import get_default_configuration
from pyipv8.ipv8.deprecated.community import Community
from pyipv8.ipv8.peer import Peer
from pyipv8.ipv8_service import IPv8, _COMMUNITIES

master_peer_init = Peer(
    "307e301006072a8648ce3d020106052b81040024036a00040112bc352a3f40dd5b6b34f28c82636b3614855179338a1c2f9ac87af17f5af3084955c4f58d9a48d35f6216aac27d68e04cb6c200025046155983a3ae1378320d93e3d865c6ab63b3f11a6c74fc510fa67b2b5f448de756b4114f765c80069e9faa51476604d9d4"
        .decode('HEX'))

# the middle layer won't work since the uncertain number of bytes received in dataReceived method...
# for discover peers
class Middle(Community):
    master_peer = master_peer_init

    def __init__(self, my_peer, endpoint, network):
        super(Middle, self).__init__(my_peer, endpoint, network)
        self.peers_dict = {}
        self.client_dict = {}
        self.server_dict = {}

        # self.forward_factory = ForwardFactory(self)

        # listen traffic
        self.port = self.endpoint._port
        reactor.listenTCP(self.port, ForwardFactory(self))
        logging.debug("Forwarder is listening on port: {}".format(self.port))

    def started(self):
        def start_communication():
            for p in self.get_peers():
                if p not in self.peers_dict:
                    self.logger.info("New Host {} join the network".format(p))
                    # self.send_identity_request("identity?", p)
                    # self.peers_dict.update({p: None})

        self.register_task("start_communication", LoopingCall(start_communication)).start(5.0, True).addErrback(log.err)

# receive connection from peers
class ForwardProtocol(protocol.Protocol):

    def __init__(self, factory):
        self.state = 'REQUEST'
        self.forward_protocol = factory
        self.client_protocol = None
        self.buffer = None

    def connectionMade(self):
        address = self.transport.getPeer()
        logging.debug("Receive connection from {}".format(address))

    def dataReceived(self, data):
        if self.state == 'REQUEST':
            self.handle_REQUEST(data)
            self.state = 'TRANSMISSION'

        elif self.state == 'TRANSMISSION':
            self.handle_TRANSMISSION(data)

    def handle_REQUEST(self, data):
        client_factory = ClientsFactory(self)
        # build TCP connection with server
        # host, port = self.forward_factory.server_dict.keys()[0].address
        reactor.connectTCP('localhost', 8092, client_factory)
        self.buffer = data


    def handle_TRANSMISSION(self, data):
        if self.client_protocol is not None:
            self.client_protocol.write(data)
        else:
            self.buffer += data

    def write(self, data):
        self.transport.write(data)

class ForwardFactory(Factory):
    def __init__(self, middle):
        self.middle = middle
        self.peers_dict = self.middle.peers_dict
        self.server_dict = self.middle.server_dict
        self.client_dict = self.middle.client_dict

    def buildProtocol(self, addr):
        return ForwardProtocol(self)


# remote side of forwarder
class ClientProtocol(protocol.Protocol):

    def __init__(self, client_factory):
        self.client_factory = client_factory

    def connectionMade(self):
        self.client_factory.forward_protocol.client_protocol = self
        self.write(self.client_factory.forward_protocol.buffer)
        self.client_factory.forward_protocol.buffer = None

    def dataReceived(self, data):
        self.client_factory.forward_protocol.write(data)

    def write(self, data):
        self.transport.write(data)


class ClientsFactory(ClientFactory):

    def __init__(self, forward_protocol):
        self.forward_protocol = forward_protocol

    def buildProtocol(self, addr):
        return ClientProtocol(self)


def middle():
    _COMMUNITIES['Middle'] = Middle

    for i in [3]:
        configuration = get_default_configuration()
        configuration['keys'] = [{
            'alias': "my peer3",
            'generation': u"curve25519",
            'file': u"ec%d.pem" % i
        }]
        configuration['logger'] = {
            'level': 'DEBUG'
        }
        configuration['overlays'] = [{
            'class': 'Middle',
            'key': "my peer3",
            'walkers': [{
                'strategy': "RandomWalk",
                'peers': 10,
                'init': {
                    'timeout': 3.0
                }
            }],
            'initialize': {},
            'on_start': [('started',)]
        }]
        IPv8(configuration)


if __name__ == '__main__':
    middle()
    reactor.run()
