from twisted.internet import reactor, protocol
from twisted.internet.protocol import Factory
from twisted.internet.task import LoopingCall

from pyipv8.ipv8.deprecated.community import Community
from pyipv8.ipv8.deprecated.payload import Payload
from pyipv8.ipv8.deprecated.payload_headers import BinMemberAuthenticationPayload, GlobalTimeDistributionPayload
from pyipv8.ipv8_service import _COMMUNITIES, IPv8
from pyipv8.ipv8.configuration import get_default_configuration
from pyipv8.ipv8.peer import Peer

import socket
import struct
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)


class Message(Payload):
    format_list = ['raw']

    def __init__(self, message):
        self.message = message

    def to_pack_list(self):
        return [('raw', self.message)]

    @classmethod
    def from_unpack_list(cls, message):
        return cls(message)


master_peer_init = Peer(
    "307e301006072a8648ce3d020106052b81040024036a00040046d529db97b697d56b33d7935cd9213df309a7c3eb96a15c494ee72697f1d192c649d0666e903977de4a412649a28c970af0940155bfe7d7e0abd13e0bf7673b65f087a976deac412464c4959da06cc36945eee5017ec2007cca71841c6cddce8a84e525e64c88".decode(
        'HEX'))


class Client(Community):
    master_peer = master_peer_init

    def __init__(self, my_peer, endpoint, network):
        super(Client, self).__init__(my_peer, endpoint, network)
        self.decode_map[chr(1)] = self.on_message
        self.addr_set = set()
        self.socks5_factory = Socks5Factory(self)

    def started(self):
        def start_communication():
            for p in self.get_peers():
                self.addr_set.add(p)

        # Find peers
        self.register_task("start_communication", LoopingCall(start_communication)).start(1.0, True)

        reactor.listenTCP(40000, self.socks5_factory)
        logger.debug("socks5_twisted server listening at port 40000")

    def create_message(self, message):
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = Message(message).to_pack_list()
        return self._ez_pack(self._prefix, 1, [auth, dist, payload])

    def on_message(self, source_address, data):
        """ Write response from server to browser """

        auth, dist, payload = self._ez_unpack_auth(Message, data)
        seq_id, response = self.unpack_data(payload.message)
        logging.debug("send back response id:{} to protocol:{}", repr(seq_id), self.socks5_factory.socks[seq_id])
        self.socks5_factory.socks[seq_id].transport.write(response)

    def unpack_data(self, data, offset=0):
        """ Unpack response from server """

        seq_id = data[offset:offset + 4]
        offset += 4
        target_ip, target_port = self.unpack_socket_address(data[offset:offset + 6])
        offset += 6
        host_ip, host_port = self.unpack_socket_address(data[offset:offset + 6])
        offset += 6
        response = data[offset:]

        return seq_id, response

    def unpack_socket_address(self, data, offset=0):
        ip = socket.inet_ntoa(data[offset:offset + 4])
        offset += 4
        port, = struct.unpack('>H', data[offset:offset + 2])

        return ip, port


class Socks5Protocol(protocol.Protocol):

    def __init__(self, factory):
        self.socks5_factory = factory
        self.state = 'NEGOTIATION'
        self.target_address = None

    def connectionMade(self):
        address = self.transport.getPeer()
        logging.info("Receive {} connection from {}:{}".format(address.type, address.host, address.port))

    def dataReceived(self, data):
        if self.state == 'NEGOTIATION':
            logger.debug("1.start socks5_twisted handshake")
            self.handle_NEGOTIATION(data)
            self.state = 'REQUEST'

        elif self.state == 'REQUEST':
            logger.debug("2.handshake success, start request phase")
            self.handle_REQUEST(data)
            self.state = 'TRANSMISSION'

        elif self.state == 'TRANSMISSION':
            logger.debug("3.start data transmission")
            self.handle_TRANSMISSION(data)

    def handle_NEGOTIATION(self, data):
        self.transport.write('\x05\x00')

    def handle_REQUEST(self, data):
        self.target_address = self.unpack_request_data(data)

    def handle_TRANSMISSION(self, data):
        """ Send packed data to server """

        seq_id = self.register_ID()

        address = self.transport.getHost()
        host_ip, host_port = self.get_packed_address(address)

        logger.debug("id:{}, host_ip:{}, host_port:{}".format(repr(seq_id), host_ip, host_port))
        logger.debug("addr_to_send:{}".format(self.target_address))

        packed_data = seq_id + host_ip + host_port + self.target_address + data

        print "packed_data", repr(packed_data)
        self.send_data(packed_data)

    def register_ID(self):
        seq_id = os.urandom(4)
        print "id from client", repr(seq_id)
        while seq_id not in self.socks5_factory.socks:
            self.socks5_factory.socks[seq_id] = self
        return seq_id

    def get_packed_address(self, address):
        packed_ip = socket.inet_aton(address.host)
        packed_port = struct.pack('>H', address.port)
        return packed_ip, packed_port

    def unpack_request_data(self, data, offset=0):
        socks_version, = struct.unpack('>B', data[offset])
        offset += 1
        cmd, = struct.unpack('>B', data[offset])
        offset += 2

        addr_type, = struct.unpack('>B', data[offset])
        target_address = data[offset]
        offset += 1

        if addr_type == 3:
            domain_len, = struct.unpack('>B', data[offset])
            target_address += data[offset: offset + 1 + domain_len]
            offset += domain_len + 1

        port, = struct.unpack('>H', data[offset:offset + 2])
        target_address += data[offset:offset + 2]
        logger.debug("version:{}, cmd:{}, addr_type:{}, port:{}".format(socks_version, cmd, addr_type, port))

        reply = b'\x05\x00\x00\x01'
        host_address = self.transport.getHost()
        logging.debug("socks5_twisted send success message to {}".format(host_address))
        reply += ''.join(self.get_packed_address(host_address))
        self.transport.write(reply)

        length = struct.pack('>B', len(target_address))

        target_address = length + target_address

        return target_address

    # Send to peer(not chunk)
    def send_data(self, data):
        for p in self.socks5_factory.client.get_peers():
            packet = self.socks5_factory.client.create_message(data)
            self.socks5_factory.client.endpoint.send(p.address, packet)

    def write(self, data):
        self.transport.write(data)

    def connectionLost(self, reason):
        logger.error("connection lost:{}".format(reason))
        self.transport.loseConnection()


class Socks5Factory(Factory):

    def __init__(self, client):
        self.client = client
        self.socks = {}

    def buildProtocol(self, addr):
        return Socks5Protocol(self)


def client():
    _COMMUNITIES['Client'] = Client

    for i in [2]:
        configuration = get_default_configuration()
        configuration['keys'] = [{
            'alias': "my peer",
            'generation': u"medium",
            'file': u"ec%d.pem" % i
        }]
        configuration['overlays'] = [{
            'class': 'Client',
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
    client()
    reactor.run()
