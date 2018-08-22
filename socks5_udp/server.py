from twisted.internet import reactor, protocol
from twisted.internet.task import LoopingCall
from twisted.internet.protocol import ClientFactory

from pyipv8.ipv8.deprecated.community import Community
from pyipv8.ipv8.deprecated.payload_headers import BinMemberAuthenticationPayload, GlobalTimeDistributionPayload
from pyipv8.ipv8.keyvault.crypto import ECCrypto
from pyipv8.ipv8_service import _COMMUNITIES, IPv8
from pyipv8.ipv8.configuration import get_default_configuration
from pyipv8.ipv8.peer import Peer

import socket
import struct
import logging
import time

from socks5_udp.database import ProxyDatabase
from socks5_udp.payload import IdentityRequestPayload, IdentityResponsePayload, TargetAddressPayload, Message

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)

key1 = ECCrypto().generate_key(u"medium")
# master_peer_init = Peer(key1)
logging.info(key1.pub().key_to_bin().encode('HEX'))
# master_peer_init = Peer(key1.pub().key_to_bin().encode('HEX').decode('HEX'))
print key1.pub().key_to_bin().encode('HEX')
# master_peer_init = Peer(
#     "307e301006072a8648ce3d020106052b81040024036a00040046d529db97b697d56b33d7935cd9213df309a7c3eb96a15c494ee72697f1d192c649d0666e903977de4a412649a28c970af0940155bfe7d7e0abd13e0bf7673b65f087a976deac412464c4959da06cc36945eee5017ec2007cca71841c6cddce8a84e525e64c88".decode(
#         'HEX'))

master_peer_init = Peer(
    "307e301006072a8648ce3d020106052b81040024036a000401142bae9f90e77434a6ddda16c9bc913a3440366b9eedc9e57a660789e10aa3f470c1f7ae769083a3494be79ad78165caed85da009a7e897bd51e531e9fd90465c038993d2bbe6646b592872cb432c818ce9fa6e3ae0382a76d39ef982fb85801279def1409a86a".decode(
        'HEX'))


class Server(Community):
    master_peer = master_peer_init

    def __init__(self, my_peer, endpoint, network):
        super(Server, self).__init__(my_peer, endpoint, network)
        self.host_dict = {}
        self.client_dict = {}
        self.state = 'ADDRESS_FROM_SOCKS5'
        self.remote_protocol = None
        self.remote_factory = None
        self.buffer = None
        self.client_protocol = None
        self.factories = {}

        self.database = ProxyDatabase(working_directory='.', db_name='server_ledger')
        self._balance = self.get_balance()
        logger.info("init balance: %s", self._balance)

        self.decode_map.update({
            chr(7): self.on_identity_request,
            chr(8): self.on_identity_response,
            chr(9): self.on_target_address,
            chr(10): self.on_message,
        })

    def started(self):

        def start_communication():
            for p in self.get_peers():
                if p not in self.host_dict:
                    print "New host {} join the network".format(p)
                    self.send_identity_request("identity?", p)
                    self.host_dict.update({p: None})

                    # print "all blocks", len(self.persistence.get_all_blocks())

        self.register_task("start_communication", LoopingCall(start_communication)).start(1.0, True)
        self.register_task("on_payment", LoopingCall(self.debit)).start(60.0, True)

    def get_balance(self):
        """
        Get current balance from database
        :return: balance
        """
        balance = self.database.get_balance()
        return balance

    def debit(self):
        """
        Insert token to database
        :return: None
        """
        timestamp = int(round(time.time() * 1000))
        debit = 1
        credit = 0
        self._balance += debit - credit
        self.database.debit(timestamp, debit, credit, self._balance)
        logger.debug("Latest record in server database: %s", self.database.get_last())

    def get_target_address(self, data):
        addr_type, = struct.unpack('>B', data[0])
        print "addr_type", addr_type

        target_ip = ''
        if addr_type == 1:
            target_ip = socket.inet_ntoa(data[1: 5])

        elif addr_type == 3:
            length, = struct.unpack('>B', data[1])
            target_ip = data[2: 2 + length]

        target_port, = struct.unpack('>H', data[-2:])
        return target_ip, target_port

    def create_identity_request(self, data):
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = IdentityRequestPayload(data).to_pack_list()
        print self.my_peer.public_key.key_to_bin().encode('HEX')
        # print "auth, dist, payload", auth, dist, payload
        return self._ez_pack(self._prefix, 7, [auth, dist, payload])

    def send_identity_request(self, data, p):
        packet = self.create_identity_request(data)
        self.endpoint.send(p.address, packet)

    def on_identity_request(self, source_address, data):
        auth, dist, payload = self._ez_unpack_auth(IdentityRequestPayload, data)
        response = payload.message
        if response == 'identity?':
            self.send_identity_response("server", source_address)
        else:
            print "server id request error"

    def create_identity_response(self, data):
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = IdentityResponsePayload(data).to_pack_list()
        return self._ez_pack(self._prefix, 8, [auth, dist, payload])

    def send_identity_response(self, data, source_address):
        packet = self.create_identity_response(data)
        self.endpoint.send(source_address, packet)

    def on_identity_response(self, source_address, data):
        auth, dist, payload = self._ez_unpack_auth(IdentityResponsePayload, data)
        response = payload.message
        # check server or client
        if response == 'client':
            print "client comes from: ", source_address
            print "update host dict", self.client_dict, self.host_dict
            for host in self.host_dict.keys():
                if host.address == source_address:
                    self.client_dict.update({host: None})
                    print "update client dict", self.client_dict

        elif response == 'server':
            print "server comes from: ", source_address

    def create_message(self, message):
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = Message(message).to_pack_list()
        return self._ez_pack(self._prefix, 10, [auth, dist, payload])

    # Establish connection to remote server
    def on_target_address(self, source_address, data):
        auth, dist, payload = self._ez_unpack_auth(TargetAddressPayload, data)
        target_address = payload.message
        print "target address", target_address, "target address"
        seq_id = target_address[0:4]
        target_address = target_address[4:]
        address = self.get_target_address(target_address)
        print address
        target_ip, target_port = address

        # connectTCP
        remote_factory = RemoteFactory(self, seq_id)
        self.factories[seq_id] = remote_factory
        reactor.connectTCP(target_ip, target_port, remote_factory)

        ### Endpoints
        # self.endpoints = TCP4ClientEndpoint(reactor, target_ip, target_port)
        # remote_factory = RemoteFactory(self)
        # self.factories[seq_id] = remote_factory

    def on_message(self, source_address, data):
        """ Receive request from client """

        auth, dist, payload = self._ez_unpack_auth(Message, data)

        message = payload.message
        seq_id = message[0:4]
        request = message[4:]
        print "id and message", repr(seq_id), " ||| ", len(data)
        print "self.factories", self.factories
        remote_factory = self.factories[seq_id]
        remote_factory.seq_id = seq_id
        remote_factory.request = request
        if remote_factory.protocol:
            print "send from server"
            remote_factory.protocol.transport.write(request)

        # Modify values in factory
        # remote_factory = RemoteFactory(self)
        # remote_factory.requests[seq_id] = request

        # Get last protocol

        # remote_factory.proto[seq_id] = None
        # print "remote_factory.protocol ", remote_factory.protocol

        # print "remote_factory", remote_factory

        # Connect to remote factory
        # whenConnected = self.endpoints.connect(remote_factory)
        # print self.endpoints
        # print "whenConnected", remote_factory
        # whenConnected.addCallbacks(self.cbConnected, self.ebConnectError)

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
        print "addr_type", addr_type

        target_ip = ''
        if addr_type == 1:
            target_ip = socket.inet_ntoa(data[1: 5])

        elif addr_type == 3:
            length, = struct.unpack('>B', data[1])
            target_ip = data[2: 2 + length]

        target_port, = struct.unpack('>H', data[-2:])
        return target_ip, target_port

    def send(self, data):
        addr = [p.address for p in self.client_dict.keys()]
        packet = self.create_message(data)
        self.endpoint.send(addr[0], packet)


class RemoteProtocol(protocol.Protocol):

    def __init__(self, factory):
        self.factory = factory
        self.factory.protocol = self

    # establish connection with remote server
    def connectionMade(self):
        if self.factory.request:
            print "send from protocol"
            self.transport.write(self.factory.request)
        else:
            print "no data"
        # record protocol
        # print "self.factory", self.factory
        # request = self.factory.requests
        # protocol = self.factory.proto
        # print "request", request
        # self.seq_id, message = request.popitem()

        # record protocol
        # self.factory.proto[self.seq_id] = self
        # print "self.factory.proto", self.factory.proto

        # print "self.seq_id, message", self.seq_id, self
        # self.transport.write(message)

    # Send data to local proxy
    def dataReceived(self, data):
        print len(data), self.factory.request
        self.send_all(data)

    def send_all(self, data):
        bytes_sent = 0
        while bytes_sent < len(data):
            chunk_data = data[bytes_sent:bytes_sent + 4096]
            packed_data = self.factory.seq_id + chunk_data
            self.factory.server.send(packed_data)  # endpoint send
            bytes_sent += 4096

    def clientConnectionLost(self, connector, reason):
        logging.debug("connection failed", reason.getErrorMessage())

    def clientConnectionFailed(self, connector, reason):
        logging.debug("connection lost", reason.getErrorMessage())


class RemoteFactory(ClientFactory):

    def __init__(self, server, seq_id, request=None):
        self.server = server
        self.seq_id = seq_id
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
