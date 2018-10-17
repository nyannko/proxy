import struct
import socket
import logging

from tw2.core import Deferred
from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet.task import LoopingCall
from twisted.internet.protocol import Factory, ClientFactory

from pyipv8.ipv8.messaging.anonymization.community import TunnelCommunity, TunnelSettings, inlineCallbacks
from pyipv8.ipv8.peer import Peer
from pyipv8.ipv8_service import IPv8, _COMMUNITIES
from pyipv8.ipv8.deprecated.community import Community
from pyipv8.ipv8.configuration import get_default_configuration

master_peer_init = Peer(
    "307e301006072a8648ce3d020106052b81040024036a00040112bc352a3f40dd5b6b34f28c82636b3614855179338a1c2f9ac87af17f5af3084955c4f58d9a48d35f6216aac27d68e04cb6c200025046155983a3ae1378320d93e3d865c6ab63b3f11a6c74fc510fa67b2b5f448de756b4114f765c80069e9faa51476604d9d4"
        .decode('HEX'))

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', filemode='a+')


# IPv8 node
# ----------------------------------------------------------------------------------------------------------------------
# For peer discovery ...
class MultiProxy(TunnelCommunity):
    master_peer = master_peer_init

    def __init__(self, my_peer, endpoint, network):
        super(MultiProxy, self).__init__(my_peer, endpoint, network)
        self.peers_dict = {}
        self.be_server = False
        self.tunnel = True
        self.socks5_factory = Socks5Factory(self)
        self.forward_factory = ForwardFactory(self)
        self.server_factory = ServerFactory(self)

        self.open_socks5_server()

        self.settings = TunnelSettings()
        self.settings.become_exitnode = False

        self.port = self.endpoint.get_address()[1]
        if not self.be_server:
            reactor.listenTCP(self.port, self.forward_factory)
            self.logger.debug("Forwarder is listening on port: {}".format(self.port))
        else:
            reactor.listenTCP(self.port, self.server_factory)
            self.logger.debug("Server is listening on port: {}".format(self.port))

        if self.tunnel:
            self.build_tunnels(2)

    def open_socks5_server(self):
        """Start socks5 twisted server"""
        port = 40000
        for _ in range(100):
            try:
                reactor.listenTCP(port, self.socks5_factory)
                break
            except Exception as e:
                self.logger.exception(e.message)
                port += 1
                continue
        print "listening at ", port
        # logging.info("socks5_twisted server listening at port {}".format(port))

    def started(self):
        def start_communication():
            for p in self.get_peers():
                if p not in self.peers_dict:
                    self.logger.info("New Host {} join the network".format(p))

        self.register_task("start_communication", LoopingCall(start_communication)).start(5.0, True).addErrback(log.err)
        self.register_task("build_tunnel", LoopingCall(self.check_circuit)).start(1.0, True).addErrback(log.err)
        # self.register_task("tunnels_ready", LoopingCall(self.tunnels_ready).start(5.0, True).addErrback(log.err))

    # only if there are new circuits available could we send the data
    def check_circuit(self):
        if self.circuits != {}:
            print "get new circuit", self.circuits, self.relay_from_to, self.exit_candidates
            cir_id = self.circuits.keys()[0]
            peer_address = self.circuits[cir_id].peer.address
            print "peer address", peer_address
            self.socks5_factory.circuit_peers[cir_id] = peer_address
        if self.exit_candidates != {}:
            print "get new exit candidates", self.circuits, self.relay_from_to, self.exit_candidates
            exit_pub_key = self.exit_candidates.keys()[0]
            exit_address = self.exit_candidates[exit_pub_key].address
            self.forward_factory.circuit_peers[exit_pub_key] = exit_address
        if self.relay_from_to != {}:
            print "get new relay from to peers", self.circuits, self.relay_from_to, self.exit_candidates
            from_cir_id = self.relay_from_to.keys()
            print "from_realy_address", [i.peer.address for i in self.relay_from_to[from_cir_id]]
        else:
            # no circuit available
            print "self.circuits is None", self.circuits, self.relay_from_to, self.exit_candidates


# Client local side
# ----------------------------------------------------------------------------------------------------------------------
# Browser sends requests to here
class Socks5Protocol(protocol.Protocol):
    def __init__(self, factory):
        self.socks5_factory = factory
        self.remote_protocol = None
        self.state = 'NEGOTIATION'
        # buffer and protocol for tcp
        self.buffer = None

    def connectionMade(self):
        address = self.transport.getPeer()
        logging.info("Receive {} connection from {}:{}".format(address.type, address.host, address.port))

    def dataReceived(self, data):
        if self.state == 'NEGOTIATION':
            self.handle_NEGOTIATION(data)
            self.state = 'REQUEST'

        elif self.state == 'REQUEST':
            self.handle_REQUEST_tcp(data)
            self.state = 'TRANSMISSION'

        elif self.state == 'TRANSMISSION':
            self.handle_TRANSMISSION(data)

    def handle_NEGOTIATION(self, data):
        self.transport.write('\x05\x00')

    def handle_REQUEST_tcp(self, data):
        addr_to_send = self.unpack_request_data_tcp(data)
        self.send_address(addr_to_send)

    def send_address(self, data):
        # use tcp endpoint
        remote_factory = RemoteFactory(self)
        host, port = self.socks5_factory.circuit_peers.values()[0]
        reactor.connectTCP(host, port, remote_factory)
        logging.info("Connected to {}:{}".format(host, port))
        self.buffer = data

    def handle_TRANSMISSION(self, data):
        """ Send packed data to server """
        if self.remote_protocol is not None:
            self.remote_protocol.write(data)
        else:
            self.buffer += data

    def get_packed_address(self, address):
        packed_ip = socket.inet_aton(address.host)
        packed_port = struct.pack('>H', address.port)
        return packed_ip, packed_port

    def unpack_request_data_tcp(self, data):
        socks_version, = struct.unpack('>B', data[0])
        cmd, = struct.unpack('>B', data[1])

        addr_type, = struct.unpack('>B', data[3])
        addr_to_send = data[3]

        if addr_type == 3:
            domain_len, = struct.unpack('>B', data[4])
            addr_to_send += data[4: 5 + domain_len]

        port, = struct.unpack('>H', data[-2:])
        addr_to_send += data[-2:]
        logging.debug("version:{}, cmd:{}, addr_type:{}, port:{}".format(socks_version, cmd, addr_type, port))

        reply = b"\x05\x00\x00\x01"
        reply += socket.inet_aton('0.0.0.0') + struct.pack('>H', port)
        self.transport.write(reply)

        length = struct.pack('>B', len(addr_to_send))

        addr_to_send = length + addr_to_send
        return addr_to_send

    def write(self, data):
        self.transport.write(data)


class Socks5Factory(Factory):
    def __init__(self, proxy):
        self.proxy = proxy
        self.circuit_peers = {}

    def buildProtocol(self, addr):
        return Socks5Protocol(self)


# Forwarder local side
# ----------------------------------------------------------------------------------------------------------------------
# Receive data from other peers
class ForwardProtocol(protocol.Protocol):

    def __init__(self, forward_factory):
        self.state = 'REQUEST'
        self.forward_factory = forward_factory
        self.remote_protocol = None
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
        # build TCP connection with server
        remote_factory = RemoteFactory(self)
        print "forward factory address", self.forward_factory
        host, port = self.forward_factory.circuit_peers.values()[0]
        print "connected to ", host, port
        reactor.connectTCP(host, port, remote_factory)
        self.buffer = data

    def handle_TRANSMISSION(self, data):
        if self.remote_protocol is not None:
            self.remote_protocol.write(data)
        else:
            self.buffer += data

    def write(self, data):
        self.transport.write(data)


class ForwardFactory(Factory):
    def __init__(self, proxy):
        self.proxy = proxy
        self.circuit_peers = {}

    def buildProtocol(self, addr):
        return ForwardProtocol(self)


# Server local side
# ----------------------------------------------------------------------------------------------------------------------
# Exit node
class ServerProtocol(protocol.Protocol):

    def __init__(self, server_factory):
        self.server_factory = server_factory
        self.remote_protocol = None
        self.state = 'ADDRESS_FROM_SOCKS5'
        self.buffer = None

    def dataReceived(self, data):
        if self.state == 'ADDRESS_FROM_SOCKS5':
            self.handle_REMOTEADDR(data)
            self.state = 'DATA_FROM_SOCKS5'

        elif self.state == 'DATA_FROM_SOCKS5':
            self.handle_REQUEST(data)

    def handle_REMOTEADDR(self, data):
        host, port, request = self.unpack_address(data)
        logging.debug("host:{}, port:{}, length of request:{}".format(host, port, len(request)))
        # factory = self.create_client_factory()
        remote_factory = RemoteFactory(self)
        reactor.connectTCP(host, port, remote_factory)
        self.buffer = request

    def handle_REQUEST(self, data):
        if self.remote_protocol is not None:
            self.remote_protocol.write(data)
        else:
            self.buffer += data

    def unpack_address(self, data):
        data_length, = struct.unpack('>B', data[0])

        address = data[0: 1 + data_length]
        addr_type, = struct.unpack('>B', address[1])

        host = ''
        if addr_type == 3:
            length = ord(address[2])
            host = address[3:3 + length]

        port, = struct.unpack('>H', address[-2:])

        request = data[1 + data_length:]
        return host, port, request

    ############################################
    # addr_type, = struct.unpack('>B', data[0])
    #
    # target_ip = ''
    # if addr_type == 1:
    #     target_ip = socket.inet_ntoa(data[1: 5])
    #
    # elif addr_type == 3:
    #     length, = struct.unpack('>B', data[1])
    #     target_ip = data[2: 2 + length]
    #
    # target_port, = struct.unpack('>H', data[-2:])
    # return target_ip, target_port

    def write(self, data):
        self.transport.write(data)

    def connectionLost(self, reason):
        logging.error("connection lost:{}".format(reason))
        self.transport.loseConnection()


class ServerFactory(Factory):
    def __init__(self, proxy):
        self.proxy = proxy
        self.circuit_peers = []

    def buildProtocol(self, addr):
        return ServerProtocol(self)


# Remote side
# ----------------------------------------------------------------------------------------------------------------------
# Used by socks5/forwarder/server protocol
class RemoteProtocol(protocol.Protocol):

    def __init__(self, remote_factory):
        self.remote_factory = remote_factory

    def connectionMade(self):
        self.remote_factory.local_protocol.remote_protocol = self
        self.write(self.remote_factory.local_protocol.buffer)
        self.remote_factory.local_protocol.buffer = None

    def dataReceived(self, data):
        self.remote_factory.local_protocol.write(data)

    def write(self, data):
        self.transport.write(data)


class RemoteFactory(ClientFactory):

    def __init__(self, local_protocol):
        """ Initialize local protocols(socks5/forwarder/server)"""
        self.local_protocol = local_protocol

    def buildProtocol(self, addr):
        return RemoteProtocol(self)


def proxy():
    _COMMUNITIES['MultiProxy'] = MultiProxy

    for i in [1]:
        configuration = get_default_configuration()
        configuration['keys'] = [{
            'alias': "my peer",
            'generation': u"curve25519",
            'file': u"ec%d.pem" % i
        }]
        configuration['logger'] = {
            'level': 'DEBUG'
        }
        configuration['overlays'] = [{
            'class': 'MultiProxy',
            'key': "my peer",
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
    proxy()
    reactor.run()
