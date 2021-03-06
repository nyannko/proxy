import struct
import socket
import logging

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet.task import LoopingCall
from twisted.internet.protocol import Factory, ClientFactory

from pyipv8.ipv8.messaging.anonymization.community import TunnelCommunity, TunnelSettings, inlineCallbacks, \
    CIRCUIT_STATE_READY
from pyipv8.ipv8.peer import Peer
from pyipv8.ipv8_service import IPv8, _COMMUNITIES
from pyipv8.ipv8.configuration import get_default_configuration
from socks5_ipv8.Message import Message

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
        self.tunnel = False
        self.socks5_factory = Socks5Factory(self)
        self.forward_factory = ForwardFactory(self)
        self.server_factory = ServerFactory(self)

        self.open_socks5_server()

        self.settings = TunnelSettings()
        self.settings.become_exitnode = False

        self.port = self.endpoint.get_address()[1]
        print "server listening at :", self.port
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
            print "_all_addresses", self.network._all_addresses
            print "I am:", self.my_peer, "\nI know:", [str(p) for p in self.get_peers()]
            for p in self.get_peers():
                if p not in self.peers_dict:
                    self.logger.info("New Host {} join the network".format(p))

        self.register_task("start_communication", LoopingCall(start_communication)).start(5.0, True).addErrback(log.err)
        self.register_task("build_tunnel", LoopingCall(self.check_circuit)).start(1.0, True).addErrback(log.err)
        # self.register_task("tunnels_ready", LoopingCall(self.tunnels_ready).start(5.0, True).addErrback(log.err))

    # first hop's address
    # exit node address
    # forwarder's address
    # only if there are new circuits available could we send the data
    def check_circuit(self):
        # loop through circuits
        for circuit_id, circuit in self.circuits.items():
            # check if the circuit is ready
            if circuit.state == CIRCUIT_STATE_READY:
                print "get new circuit", self.circuits, self.relay_from_to, self.exit_candidates
                print "first hop's address", [v.peer.address for k, v in
                                              self.circuits.items()]  # print address for next hop
            peer_address = circuit.peer.address
            self.socks5_factory.circuit_peers[circuit_id] = peer_address

            print "peer address", peer_address, "compatible", [p.address for p in self.compatible_candidates]
        print "self.socks5_factory.circuit_peers", self.socks5_factory.circuit_peers

        # select exit nodes
        exit_node = []
        print "exit node", self.exit_sockets, self.exit_candidates
        for key, peer in self.exit_candidates.items():  # change to exit_socket
            exit_address = peer.address
            self.forward_factory.circuit_peers[key] = exit_address
            exit_node.append(exit_address)
        print "self.forward_factory.circuit_peers", self.forward_factory.circuit_peers
        print "self.forward_factory.circuit_idx", self.forward_factory.circuit_id
        print "exit node address", exit_node

        if not self.forward_factory.circuit_peers:
            print "no exit nodes available."

        forwarder_addr = {}
        for circuit_id, relay_route in self.relay_from_to.items():
            forwarder_address = relay_route.peer.address
            self.forward_factory.circuit_peers[circuit_id] = forwarder_address
            forwarder_addr[circuit_id] = forwarder_address
        print "self.forward_factory.circuit_peers", self.forward_factory.circuit_peers
        print "forwarder's address", forwarder_addr

        print "self.circuits is None", self.circuits, self.relay_from_to, self.exit_candidates

    def update_address(self, cid, peer):
        self.forward_factory.circuit_peers[cid] = peer

    def update_id(self, idx, new_idx):
        self.forward_factory.circuit_id[idx] = new_idx


# Client local side
# ----------------------------------------------------------------------------------------------------------------------
# Browser sends requests to here
class Socks5Protocol(protocol.Protocol):
    def __init__(self, factory):
        self.socks5_factory = factory
        self.remote_protocol = None
        self.state = 'NEGOTIATION'
        # buffer and protocol for tcp
        self.buffer = bytes()

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

    def send_address(self, addr_to_send):
        # use tcp endpoint
        remote_factory = RemoteFactory(self)
        host, port = self.socks5_factory.circuit_peers.values()[0]
        self.cir_id = self.socks5_factory.circuit_peers.keys()[0]  # circuit_id
        self.buffer = Message(self.cir_id, 'addr', addr_to_send).to_bytes()
        reactor.connectTCP(host, port, remote_factory)
        logging.info("Connected to {}:{}".format(host, port))

    def handle_TRANSMISSION(self, data):
        """ Send packed data to server """
        data_send = Message(self.cir_id, 'data', data).to_bytes()
        if self.remote_protocol is not None:
            self.remote_protocol.write(data_send)
        else:
            self.buffer += data_send

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
        self.buffer = bytes()

    def connectionMade(self):
        address = self.transport.getPeer()
        logging.debug("Receive connection from {}".format(address))

    def dataReceived(self, data):
        messages, _ = Message.parse_stream(data)
        for m in messages:
            if self.state == 'REQUEST':
                self.handle_REQUEST(m)
                self.state = 'TRANSMISSION'

            elif self.state == 'TRANSMISSION':
                self.handle_TRANSMISSION(m)

    def handle_REQUEST(self, message):
        from_cir_id, msg_type, data = message.cir_id, message.msg_type, message.data
        to_cir_id = self.forward_factory.circuit_id[from_cir_id]
        host, port = self.forward_factory.circuit_peers[from_cir_id]
        logging.debug("connect to {}:{}, to_circuit id is:{}".format(host, port, to_cir_id))
        remote_factory = RemoteFactory(self)
        reactor.connectTCP(host, port, remote_factory)
        self.buffer = Message(to_cir_id, msg_type, data).to_bytes()

    def handle_TRANSMISSION(self, message):
        from_cir_id, msg_type, data = message.cir_id, message.msg_type, message.data
        to_cir_id = self.forward_factory.circuit_id[from_cir_id]
        data_to_send = Message(to_cir_id, msg_type, data).to_bytes()
        if self.remote_protocol is not None:
            self.remote_protocol.write(data_to_send)
        else:
            self.buffer += data_to_send

    def write(self, data):
        self.transport.write(data)


class ForwardFactory(Factory):
    def __init__(self, proxy):
        self.proxy = proxy
        self.circuit_peers = {}  # {1006213219: ('145.94.162.154', 8093), 1288425294L: ('145.94.162.154', 8091)}
        self.circuit_id = {}  # {1006213219: 1288425294L}

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
        self.buffer = bytes()

    def dataReceived(self, data):
        print "data received from forwarder", repr(data)[:50]
        # parse data here
        messages, _ = Message.parse_stream(data)
        for m in messages:
            msg_type = m.msg_type
            if msg_type == 'addr':
                self.handle_REMOTEADDR(m)

            elif msg_type == 'data':
                self.handle_REQUEST(m)

    def handle_REMOTEADDR(self, message):
        host, port, request = self.unpack_address(message.data)
        logging.debug("host:{}, port:{}, length of request:{}".format(host, port, len(request)))
        # factory = self.create_client_factory()
        remote_factory = RemoteFactory(self)
        reactor.connectTCP(host, port, remote_factory)
        self.buffer = request

    def handle_REQUEST(self, message):
        data_to_send = message.data
        if self.remote_protocol is not None:
            self.remote_protocol.write(data_to_send)
        else:
            self.buffer += data_to_send

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

    def write(self, data):
        self.transport.write(data)

    def connectionLost(self, reason):
        logging.error("connection lost:{}".format(reason))
        self.transport.loseConnection()


class ServerFactory(Factory):
    def __init__(self, proxy):
        self.proxy = proxy
        self.factories = {}

    def buildProtocol(self, addr):
        return ServerProtocol(self)


# Remote side
# ----------------------------------------------------------------------------------------------------------------------
# Used by socks5/forwarder/server protocol
class RemoteProtocol(protocol.Protocol):

    def __init__(self, remote_factory):
        self.remote_factory = remote_factory
        self.buffer = bytes()

    def connectionMade(self):
        self.remote_factory.local_protocol.remote_protocol = self
        self.write(self.remote_factory.local_protocol.buffer)
        self.remote_factory.local_protocol.buffer = ''

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

    for i in [2]:
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
