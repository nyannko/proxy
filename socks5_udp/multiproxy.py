import logging
import socket
import struct

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

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', filemode='a+')


# for discover peers
class MultiProxy(Community):
    master_peer = master_peer_init

    def __init__(self, my_peer, endpoint, network):
        super(MultiProxy, self).__init__(my_peer, endpoint, network)
        self.peers_dict = {}
        self.be_server = False
        self.socks5_factory = Socks5Factory(self)

        # self.forward_factory = ForwardFactory(self)

        self.port = self.endpoint._port
        if self.be_server:
            reactor.listenTCP(self.port, ForwardFactory(self))
            logging.debug("Forwarder is listening on port: {}".format(self.port))
        else:
            reactor.listenTCP(self.port, ServerFactory(self))
            logging.debug("Server is listening on port: {}".format(self.port))

        self.open_socks5_server()

    def open_socks5_server(self):
        """Start socks5 twisted server"""
        port = 40000
        for _ in range(100):
            try:
                reactor.listenTCP(port, self.socks5_factory)
                break
            except Exception as e:
                print e
                # logging.exception(e.message, " port number plus one.")
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


# Client local side
# ----------------------------------------------------------------------------------------------------------------------
# browser sends requests to here
class Socks5Protocol(protocol.Protocol):
    def __init__(self, factory):
        self.socks5_factory = factory
        self.remote_protocol = None
        self.state = 'NEGOTIATION'
        # buffer and protocol for tcp
        self.buffer = None

    def connectionMade(self):
        address = self.transport.getPeer()
        # logging.info("Receive {} connection from {}:{}".format(address.type, address.host, address.port))

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
        # print self.socks5_factory.server_peers
        # host, port = self.socks5_factory.server_peers.keys()[0].address  # todo
        reactor.connectTCP('localhost', 8091, remote_factory)
        # packed_data = self.createTCPPayload(data)
        self.buffer = data
        # print self.buffer

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

    def buildProtocol(self, addr):
        return Socks5Protocol(self)


# Client remote side
# class ClientProtocol(protocol.Protocol):
#
#     def __init__(self, client_factory):
#         self.client_factory = client_factory
#
#     def connectionMade(self):
#         self.client_factory.socks5_protocol.client_protocol = self
#         self.write(self.client_factory.socks5_protocol.buffer)
#         self.client_factory.socks5_protocol.buffer = None
#
#     def dataReceived(self, data):
#         self.client_factory.socks5_protocol.write(data)
#
#     def write(self, data):
#         self.transport.write(data)
#
#
# class ClientsFactory(ClientFactory):
#
#     def __init__(self, socks5_protocol):
#         self.socks5_protocol = socks5_protocol
#
#     def buildProtocol(self, addr):
#         return ClientProtocol(self)


# Forwarder local side
class ForwardProtocol(protocol.Protocol):

    def __init__(self, forward_factory):
        self.state = 'REQUEST'
        self.forward_factory = forward_factory
        self.remote_protocol = None
        self.buffer = None

    def connectionMade(self):
        address = self.transport.getPeer()
        # logging.debug("Receive connection from {}".format(address))

    def dataReceived(self, data):
        if self.state == 'REQUEST':
            self.handle_REQUEST(data)
            self.state = 'TRANSMISSION'

        elif self.state == 'TRANSMISSION':
            self.handle_TRANSMISSION(data)

    def handle_REQUEST(self, data):
        remote_factory = RemoteFactory(self)
        # build TCP connection with server
        # host, port = self.forward_factory.server_dict.keys()[0].address
        reactor.connectTCP('localhost', 8092, remote_factory)
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

    def buildProtocol(self, addr):
        return ForwardProtocol(self)


# Server local side
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

    # def create_client_factory(self):
    #     client_factory = protocol.ClientFactory()
    #     client_factory.protocol = ClientProtocol
    #     client_factory.socks5_protocol = self
    #     return client_factory

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

    ###
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

    def buildProtocol(self, addr):
        return ServerProtocol(self)

# Remote side
class RemoteProtocol(protocol.Protocol):

    def __init__(self, remote_factory):
        self.remote_factory = remote_factory

    def connectionMade(self):
        self.remote_factory.local_protocol.remote_protocol = self
        self.write(self.remote_factory.local_protocol.buffer)
        self.remote_factory.local_protocol.buffer = None

    def dataReceived(self, data):
        self.remote_factory.forward_protocol.write(data)

    def write(self, data):
        self.transport.write(data)


# Remote side
class RemoteFactory(ClientFactory):

    def __init__(self, local_protocol):
        """ Initialize local protocols(socks5/forwarder/server)"""
        self.local_protocol = local_protocol

    def buildProtocol(self, addr):
        return RemoteProtocol(self)


class ClientProtocol(protocol.Protocol):

    def connectionMade(self):
        self.factory.socks5_protocol.client_protocol = self
        self.write(self.factory.socks5_protocol.buffer)
        self.factory.socks5_protocol.buffer = ''

    def dataReceived(self, data):
        self.factory.socks5_protocol.write(data)

    def write(self, data):
        self.transport.write(data)


def proxy():
    _COMMUNITIES['MultiProxy'] = MultiProxy

    for i in [3]:
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
