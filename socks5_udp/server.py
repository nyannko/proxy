from twisted.internet import reactor, protocol
from twisted.internet.protocol import ClientFactory
from twisted.internet.task import LoopingCall

from pyipv8.ipv8.deprecated.community import Community
from pyipv8.ipv8.deprecated.payload import Payload
from pyipv8.ipv8.deprecated.payload_headers import BinMemberAuthenticationPayload, GlobalTimeDistributionPayload
from pyipv8.ipv8.keyvault.crypto import ECCrypto
from pyipv8.ipv8_service import _COMMUNITIES, IPv8
from pyipv8.ipv8.configuration import get_default_configuration
from pyipv8.ipv8.peer import Peer

import socket
import struct
import logging

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


key1 = ECCrypto().generate_key(u"medium")
# master_peer_init = Peer(key1)
logging.info(key1.pub().key_to_bin().encode('HEX'))
# master_peer_init = Peer(key1.pub().key_to_bin().encode('HEX').decode('HEX'))
master_peer_init = Peer(
    "307e301006072a8648ce3d020106052b81040024036a00040046d529db97b697d56b33d7935cd9213df309a7c3eb96a15c494ee72697f1d192c649d0666e903977de4a412649a28c970af0940155bfe7d7e0abd13e0bf7673b65f087a976deac412464c4959da06cc36945eee5017ec2007cca71841c6cddce8a84e525e64c88".decode(
        'HEX'))


class Server(Community):
    master_peer = master_peer_init

    def __init__(self, my_peer, endpoint, network):
        super(Server, self).__init__(my_peer, endpoint, network)
        self.decode_map[chr(1)] = self.on_message
        self.addr_set = set()
        self.state = 'DATA_FROM_SOCKS5'
        self.socks = {}

    def started(self):
        def start_communication():
            for p in self.get_peers():
                self.addr_set.add(p)

        self.register_task("start_communication", LoopingCall(start_communication)).start(1.0, True)

    def create_message(self, message):
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = Message(message).to_pack_list()
        return self._ez_pack(self._prefix, 1, [auth, dist, payload])

    def on_message(self, source_address, data):
        """ Receive request from client """

        auth, dist, payload = self._ez_unpack_auth(Message, data)

        print repr(payload.message)
        if self.state == 'DATA_FROM_SOCKS5':
            self.handle_REQUEST(payload.message)

    def handle_REQUEST(self, data):
        id, source_ip, source_port, target_ip, target_port, request = self.unpack_data(data)

        logger.debug("id:{}, source_ip:{}, source_port:{}".format(repr(id), source_ip, source_port))
        logger.debug("target_ip:{}, target_port:{}".format(target_ip, target_port))

        remote_factory = RemoteFactory(self, id, request)

        print "remote, factory", remote_factory, id, request
        reactor.connectTCP(target_ip, target_port, remote_factory)

    def unpack_data(self, data):
        id = data[0:4]
        print "id from unpack", repr(id)
        source_ip, source_port = self.get_source_address(data[4:10])
        length = ord(data[10])
        target_ip, target_port = self.get_target_address(data[11:11 + length])
        data = data[11 + length:]

        return id, source_ip, source_port, target_ip, target_port, data

    def get_source_address(self, data, offset=0):
        source_ip = socket.inet_ntoa(data[offset:offset + 4])
        offset += 4
        source_port, = struct.unpack('>H', data[offset:offset + 2])
        return source_ip, source_port

    def get_target_address(self, data):
        addr_type, = struct.unpack('>B', data[0])

        target_ip = ''
        if addr_type == 3:
            length, = struct.unpack('>B', data[1])
            target_ip = data[2: 2 + length]

        target_port, = struct.unpack('>H', data[-2:])

        return target_ip, target_port

    def send(self, data):
        addr = [p.address for p in self.addr_set]
        packet = self.create_message(data)
        self.endpoint.send(addr[0], packet)


class RemoteProtocol(protocol.Protocol):

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        print self.factory.request
        self.transport.write(self.factory.request)

    # Send data to local proxy
    def dataReceived(self, data):
        self.send_all(data)

    def send_all(self, data):
        bytes_sent = 0
        while bytes_sent < len(data):
            chunk_data = data[bytes_sent:bytes_sent + 4096]
            packed_data = self.pack_data(chunk_data)
            self.factory.server.send(packed_data)  # endpoint send
            bytes_sent += 4096

    def pack_data(self, data):
        seq_id = self.factory.id
        print "new id", repr(seq_id)
        target_address = self.transport.getHost()
        target_ip, target_port = self.get_packed_address(target_address)
        source_address = self.transport.getPeer()
        source_ip, source_port = self.get_packed_address(source_address)

        # """test unpack"""
        # print struct.unpack('>I', id)
        # print "target:", struct.unpack('>H', target_port), socket.inet_ntoa(target_ip)
        # print "source:", struct.unpack('>H', source_port), socket.inet_ntoa(source_ip)
        # """test unpack"""

        packed_data = seq_id + target_ip + target_port + source_ip + source_port + data

        return packed_data

    def get_packed_address(self, address):
        packed_ip = socket.inet_aton(address.host)
        packed_port = struct.pack('>H', address.port)
        return packed_ip, packed_port

    def clientConnectionFailed(self, connector, reason):
        print connector, reason


class RemoteFactory(ClientFactory):

    def __init__(self, server, id, request):
        self.server = server
        self.id = id
        self.request = request

    def buildProtocol(self, addr):
        return RemoteProtocol(self)


def server():
    _COMMUNITIES['Server'] = Server

    for i in [1]:
        configuration = get_default_configuration()
        configuration['keys'] = [{
            'alias': "my peer",
            'generation': u"medium",
            'file': u"ec%d.pem" % i
        }]
        configuration['overlays'] = [{
            'class': 'Server',
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
    server()
    reactor.run()
