import os
import struct
import socket
import logging
import argparse

from twisted.python import log
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet.task import LoopingCall
from twisted.internet.protocol import Factory, ClientFactory

from pyipv8.ipv8.peer import Peer
from socks5_ipv8.Message import Message
from pyipv8.ipv8_service import IPv8, _COMMUNITIES
from pyipv8.ipv8.configuration import get_default_configuration
from pyipv8.ipv8.messaging.anonymization.community import TunnelCommunity, TunnelSettings, CIRCUIT_STATE_READY

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
        self.socks5_factory = Socks5Factory(self)

        self.addr, self.port = self.endpoint.get_address()
        self.socks5_port = self.open_socks5_server()

    def open_socks5_server(self):
        """Start socks5 twisted server"""
        port = 40000
        for _ in range(100):
            try:
                reactor.listenTCP(port, self.socks5_factory)
                break
            except:
                port += 1
                continue
        logging.info("socks5_twisted server listening at port {}".format(port))
        return port

    def started(self):
        def start_communication():
            # print "I am:", self.my_peer, "\nI know:", [str(p) for p in self.get_peers()]
            for p in self.get_peers():
                if p not in self.peers_dict:
                    self.logger.info("New Host {} join the network".format(p))
                self.peers_dict[p] = None

        self.register_task("start_communication", LoopingCall(start_communication)).start(5.0, True).addErrback(log.err)
        self.register_task("check_circuit", LoopingCall(self.check_circuit)).start(2.0, True).addErrback(log.err)
        # self.register_task("tunnels_ready", LoopingCall(self.tunnels_ready).start(5.0, True).addErrback(log.err))

    def check_circuit(self):
        """
        Implemented by class MultiProxyClient
        """
        pass


class MultiProxyClient(MultiProxy):

    def __init__(self, my_peer, endpoint, network):
        super(MultiProxyClient, self).__init__(my_peer, endpoint, network)
        self.settings = TunnelSettings()
        self.settings.become_exitnode = False
        self.forward_factory = ForwardFactory(self)
        reactor.listenTCP(self.port, self.forward_factory)

    def check_circuit(self):
        # Update first hop address
        for circuit_id, circuit in self.circuits.items():
            # check if the circuit is ready
            if circuit.state == CIRCUIT_STATE_READY:
                self.logger.debug("{}:{}, {}, Get new circuit {};{};{}"
                                  .format(self.addr, self.port, self.__class__.__name__,
                                          self.circuits, self.relay_from_to, self.exit_candidates, ))
                first_hops = [v.peer.address for k, v in self.circuits.items()]
                self.logger.debug("{}:{}, {}, First hop address is {}"
                                  .format(self.addr, self.port, self.__class__.__name__, first_hops))

                peer_address = circuit.peer.address
                self.socks5_factory.circuit_peers[circuit_id] = peer_address

        self.logger.debug("{}:{}, {}, Update first hop {}"
                          .format(self.addr, self.port, self.__class__.__name__, self.socks5_factory.circuit_peers))

        # Update forwarder addresses
        for circuit_id, relay_route in self.relay_from_to.items():
            forwarder_address = relay_route.peer.address
            self.forward_factory.circuit_peers[circuit_id] = forwarder_address
        self.logger.debug("{}:{}, {}, Update forward address {}"
                          .format(self.addr, self.port, self.__class__.__name__, self.forward_factory.circuit_peers))

        # Update exit nodes
        self.update_exit_node(self.socks5_factory)
        exit_node = self.socks5_factory.exit_node.values()[0] if self.socks5_factory.exit_node else 'None'
        self.logger.debug("{}:{}, {}, Update exit nodes {}"
                          .format(self.addr, self.port, self.__class__.__name__, exit_node))

        self.update_exit_node(self.forward_factory)
        exit_node = self.forward_factory.exit_node.values()[0] if self.socks5_factory.exit_node else 'None'
        self.logger.debug("{}:{}, {}, Update exit nodes {}"
                          .format(self.addr, self.port, self.__class__.__name__, exit_node))

    def update_exit_node(self, factory):
        for key, peer in self.exit_candidates.items():  # change to exit_socket?
            exit_address = peer.address
            if key not in factory.exit_node:
                factory.exit_node[key] = exit_address

    def update_address(self, cid, peer):
        self.forward_factory.circuit_peers[cid] = peer

    def update_id(self, idx, new_idx):
        self.forward_factory.circuit_id[idx] = new_idx


class MultiProxyInitiator(MultiProxyClient):

    def __init__(self, my_peer, endpoint, network):
        super(MultiProxyInitiator, self).__init__(my_peer, endpoint, network)
        self.logger.debug("{}:{}, {}, Initialized at {}"
                          .format(self.addr, self.port, self.__class__.__name__, self.socks5_port))

        self.build_tunnels(3)


class MultiProxyForwarder(MultiProxyClient):

    def __init__(self, my_peer, endpoint, network):
        super(MultiProxyForwarder, self).__init__(my_peer, endpoint, network)
        self.logger.debug("{}:{}, {} initialized at {}"
                          .format(self.addr, self.port, self.__class__.__name__, self.socks5_port))


class MultiProxyServer(MultiProxy):

    def __init__(self, my_peer, endpoint, network):
        super(MultiProxyServer, self).__init__(my_peer, endpoint, network)
        self.settings = TunnelSettings()
        self.settings.become_exitnode = True
        self.server_factory = ServerFactory(self)
        reactor.listenTCP(self.port, self.server_factory)
        self.logger.debug("{}:{}, {} initialized at {}"
                          .format(self.addr, self.port, self.__class__.__name__, self.socks5_port))


# Client local side
# ----------------------------------------------------------------------------------------------------------------------
# Browser sends requests to here
class Socks5Protocol(protocol.Protocol):

    def __init__(self, factory):
        self.socks5_factory = factory
        self.remote_protocol = None
        self.state = 'NEGOTIATION'
        self.buffer = bytes()

    def connectionMade(self):
        address = self.transport.getPeer()
        self.host_address = self.transport.getHost()
        logging.info("{}:{}, {}, Receive {} connection from {}:{}"
                     .format(self.host_address.host, self.host_address.port,
                             self.__class__.__name__, address.type, address.host, address.port))

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
        logging.info("{}:{}, {}, Connected to {}:{}"
                     .format(self.host_address.host, self.host_address.port, self.__class__.__name__, host, port))

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
        self.exit_node = {}

    def buildProtocol(self, addr):
        return Socks5Protocol(self)


# Forwarder local side
# ----------------------------------------------------------------------------------------------------------------------
# Receive data from other peers
class ForwardProtocol(protocol.Protocol):

    def __init__(self, forward_factory):
        self.forward_factory = forward_factory
        self.remote_protocol = None
        self.buffer = bytes()

    def connectionMade(self):
        address = self.transport.getPeer()
        self.host_address = self.transport.getHost()
        logging.debug("{}:{}, {}, Receive connection from {}:{}"
                      .format(self.host_address.host, self.host_address.port, self.__class__.__name__,
                              address.host, address.port))

    def dataReceived(self, data):
        messages, _ = Message.parse_stream(data)
        for m in messages:
            if m.msg_type == 'addr':
                self.handle_REQUEST(m)

            if m.msg_type == 'data':
                self.handle_TRANSMISSION(m)

    def handle_REQUEST(self, message):
        from_cir_id, msg_type, data = message.cir_id, message.msg_type, message.data
        to_cir_id = self.forward_factory.circuit_id[from_cir_id]
        host, port = self.forward_factory.circuit_peers[from_cir_id]
        logging.debug("{}:{}, {}, Connect to {}:{}, to_circuit id is:{}"
                      .format(self.host_address.host, self.host_address.port,
                              self.__class__.__name__, host, port, to_cir_id))
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
        self.exit_node = {}

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

    def connectionMade(self):
        address = self.transport.getPeer()
        self.host_address = self.transport.getHost()
        logging.debug("{}:{}, {}, Receive requests from {}:{}"
                      .format(self.host_address.host, self.host_address.port, self.__class__.__name__,
                              address.host, address.port))

    def dataReceived(self, data):
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
        logging.debug("{}:{}, {}, Forward to target server {}:{}"
                      .format(self.host_address.host, self.host_address.port, self.__class__.__name__,
                              host, port))
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
        print "self.remote_factory.local_protocol",  self.remote_factory.local_protocol

    def write(self, data):
        self.transport.write(data)


class RemoteFactory(ClientFactory):

    def __init__(self, local_protocol):
        """ Initialize local protocols(socks5/forwarder/server)"""
        self.local_protocol = local_protocol

    def buildProtocol(self, addr):
        return RemoteProtocol(self)


def proxy(nodes_num):
    _COMMUNITIES['MultiProxyInitiator'] = MultiProxyInitiator
    _COMMUNITIES['MultiProxyForwarder'] = MultiProxyForwarder
    _COMMUNITIES['MultiProxyServer'] = MultiProxyServer

    client_num, forwarder_num, server_num = nodes_num
    logging.debug("Initialize {} clients, {} forwarder, {} server"
                  .format(client_num, forwarder_num, server_num))

    def set_nodes(role, id_with_key):
        configuration = get_default_configuration()
        configuration['keys'] = [{
            'alias': "my peer",
            'generation': u"curve25519",
            'file': u"ec_{1}{0}.pem".format(*id_with_key)
            # 'file': u"ec{}_{}_{!r}.pem".format(*((id_with_key)+(os.urandom(2),)))
        }]
        configuration['logger'] = {
            'level': 'DEBUG'
        }
        configuration['overlays'] = [{
            'class': role,
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

    key = 1
    for _ in range(client_num):
        set_nodes('MultiProxyInitiator', (key, 'c'))
        key += 1

    for _ in range(forwarder_num):
        set_nodes('MultiProxyForwarder', (key, 'f'))
        key += 1

    for _ in range(server_num):
        set_nodes('MultiProxyServer', (key, 's'))
        key += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Please input the node identity and the number of nodes")
    parser.add_argument('--client', type=int, nargs='?', const=0, dest='client_number',
                        help="The number of the clients")
    parser.add_argument('--forwarder', type=int, nargs='?', const=0, dest='forwarder_number',
                        help="The number of the forwarders")
    parser.add_argument('--server', type=int, nargs='?', const=0, dest='server_number',
                        help="The number of the servers")
    args = parser.parse_args()
    nodes = [args.client_number, args.forwarder_number, args.server_number]
    nodes = [i if i else 0 for i in nodes]
    print(nodes)
    proxy(nodes)
    reactor.run()
    # Usage: python multiproxy.py --client 2 --forwarder 1 --server 2
    # Usage: python multiproxy.py --client 1
