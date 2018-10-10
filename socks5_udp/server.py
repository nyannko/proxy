from twisted.internet import reactor, protocol
from twisted.internet.task import LoopingCall
from twisted.internet.protocol import ClientFactory, Factory
from twisted.python import log

from pyipv8.ipv8.attestation.trustchain.community import TrustChainCommunity
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
import random

from socks5_udp.database import ProxyDatabase
from socks5_udp.payload import IdentityRequestPayload, IdentityResponsePayload, TargetAddressPayload, Message, \
    ACKPayload

key1 = ECCrypto().generate_key(u"medium")
# master_peer_init = Peer(key1)
logging.info(key1.pub().key_to_bin().encode('HEX'))
# master_peer_init = Peer(key1.pub().key_to_bin().encode('HEX').decode('HEX'))
print key1.pub().key_to_bin().encode('HEX')

master_peer_init = Peer(
    "307e301006072a8648ce3d020106052b81040024036a00040112bc352a3f40dd5b6b34f28c82636b3614855179338a1c2f9ac87af17f5af3084955c4f58d9a48d35f6216aac27d68e04cb6c200025046155983a3ae1378320d93e3d865c6ab63b3f11a6c74fc510fa67b2b5f448de756b4114f765c80069e9faa51476604d9d4"
        .decode('HEX'))


class Server(Community):
    master_peer = master_peer_init
    DB_NAME = 'trustchain_server'

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
        self._balance = 0

        self.logger.level = logging.DEBUG

        # listen tcp connection
        self.port = self.endpoint._port
        reactor.listenTCP(self.port, RemoteFactory_TCP())
        print("server is listening at port", self.port)

        self.decode_map.update({
            chr(7): self.on_identity_request,
            chr(8): self.on_identity_response,
            chr(9): self.on_target_address,
            chr(10): self.on_message
        })

    def started(self):
        def start_communication():
            for p in self.get_peers():
                if p not in self.host_dict:
                    self.logger.debug("New host {} join the network".format(p))
                    self.send_identity_request("identity?", p)
                    self.host_dict.update({p: None})
                    print self.port

                    # print "all blocks", len(self.persistence.get_all_blocks())

        self.register_task("start_communication", LoopingCall(start_communication)).start(1.0, True).addErrback(log.err)

    # run in an enclave(?)
    def create_server_transaction(self):
        timestamp = int(round(time.time() * 1000))
        debit = 1
        credit = 0
        self._balance += debit - credit
        bill = {'time': timestamp, 'identity': 'server->', "debit": debit, "credit": credit, "balance": self._balance}
        return bill

    # choose a random peer to sign the tx
    def send_sign(self):
        random_peer = random.choice(self.host_dict.keys())
        random_peer_pubkey = random_peer.public_key.key_to_bin()
        transaction = self.create_server_transaction()
        self.sign_block(random_peer, public_key=random_peer_pubkey, block_type='test', transaction=transaction)

    def get_target_address(self, data):
        addr_type, = struct.unpack('>B', data[0])

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
        return self._ez_pack(self._prefix, 7, [auth, dist, payload])

    def send_identity_request(self, data, p):
        packet = self.create_identity_request(data)
        self.endpoint.send(p.address, packet)

    def on_identity_request(self, source_address, data):
        auth, dist, payload = self._ez_unpack_auth(IdentityRequestPayload, data)
        response = payload.message
        if response == 'identity?':
            # todo challenge-response here (to prove as a server)
            # if cr is True:
            # identity = "server"
            # else:
            # identity = "client"
            # self.send_identity_response(identity, source_address)
            self.send_identity_response("server", source_address)
        else:
            self.logger.debug("server id request error")

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
            self.logger.info("client comes from: {}".format(source_address))
            for host in self.host_dict.keys():
                if host.address == source_address:
                    self.client_dict.update({host: None})
                    self.logger.info("client.dict: {}, host.dict: {}".format(self.client_dict, self.host_dict))

            # self.register_task("on_payment", LoopingCall(self.send_sign)).start(30.0, True).addErrback(log.err)

        elif response == 'server':
            self.logger.info("server comes from: {}".format(source_address))

    def create_message(self, proto_id, message):
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = Message(proto_id, '0000', message).to_pack_list()
        return self._ez_pack(self._prefix, 10, [auth, dist, payload])

    # Establish connection to remote server
    def on_target_address(self, source_address, data):
        auth, dist, payload = self._ez_unpack_auth(TargetAddressPayload, data)
        proto_id = payload.proto_id[0]
        seq_id = payload.seq_id[0]
        target_address = payload.message
        address = self.get_target_address(target_address)
        self.logger.debug("Target address: {}".format(address))
        target_ip, target_port = address

        # connectTCP
        remote_factory = RemoteFactory(self, proto_id)
        self.factories[proto_id] = remote_factory
        reactor.connectTCP(target_ip, target_port, remote_factory)

    def create_ack(self, proto_id, seq_id):
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = ACKPayload(proto_id, seq_id).to_pack_list()
        return self._ez_pack(self._prefix, 11, [auth, dist, payload])

    def send_ack(self, address, proto_id, seq_id):
        ack = self.create_ack(proto_id, seq_id)
        self.endpoint.send(address, ack)

    def on_message(self, source_address, data):
        """ Receive request from client """
        auth, dist, payload = self._ez_unpack_auth(Message, data)
        proto_id = payload.proto_id[0]
        seq_id = payload.seq_id[0]
        print proto_id, seq_id
        self.send_ack(source_address, proto_id, seq_id)  # send back ack

        remote_request = payload.message
        self.logger.debug("received request id {} from client".format(proto_id))
        remote_factory = self.factories[proto_id]
        remote_factory.proto_id = proto_id
        remote_factory.request = remote_request
        if remote_factory.protocol:
            remote_factory.protocol.transport.write(remote_request)

    def send(self, proto_id, data):
        addr = [p.address for p in self.client_dict.keys()]
        packet = self.create_message(proto_id, data)
        self.endpoint.send(addr[0], packet)

class RemoteProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.factory.protocol = self

    # establish connection with remote server
    def connectionMade(self):
        if self.factory.request:
            self.transport.write(self.factory.request)
        # self.transport.loseConnection()

    # Send data to local proxy
    def dataReceived(self, data):
        # logging.info("Send response to client: ", len(data), self.factory.proto_id)
        self.send_all(data)

    def send_all(self, data):
        bytes_sent = 0
        while bytes_sent < len(data):
            chunk_data = data[bytes_sent:bytes_sent + 8096]
            self.factory.server.send(self.factory.proto_id, chunk_data)  # endpoint send
            bytes_sent += 8096

    def clientConnectionLost(self, connector, reason):
        logging.debug("connection failed", reason.getErrorMessage())

    def clientConnectionFailed(self, connector, reason):
        logging.debug("connection lost", reason.getErrorMessage())


class RemoteFactory(ClientFactory):
    def __init__(self, server, proto_id, request=None):
        self.server = server
        self.proto_id = proto_id
        self.request = request

    def buildProtocol(self, addr):
        return RemoteProtocol(self)



logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', filemode='a+')

#________
class RemoteProtocol_TCP(protocol.Protocol):

    def __init__(self, factory):
        self.factory = factory
        self.state = 'ADDRESS_FROM_SOCKS5'
        self.buffer = None
        self.client_protocol = None


    def dataReceived(self, data):
        if self.state == 'ADDRESS_FROM_SOCKS5':
            self.handle_REMOTEADDR(data)
            self.state = 'DATA_FROM_SOCKS5'

        elif self.state == 'DATA_FROM_SOCKS5':
            self.handle_REQUEST(data)

    def handle_REMOTEADDR(self, data):
        host, port, request = self.unpack_address(data)
        logging.debug("host:{}, port:{}, length of request:{}".format(host, port, len(request)))
        factory = self.create_client_factory()
        reactor.connectTCP(host, port, factory)
        self.buffer = request

    def handle_REQUEST(self, data):
        if self.client_protocol is not None:
            self.client_protocol.write(data)
        else:
            self.buffer += data

    def create_client_factory(self):
        client_factory = protocol.ClientFactory()
        client_factory.protocol = ClientProtocol
        client_factory.socks5_protocol = self
        return client_factory

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

class RemoteFactory_TCP(Factory):

    def __init__(self):
        pass

    def buildProtocol(self, addr):
        return RemoteProtocol_TCP(self)

class ClientProtocol(protocol.Protocol):

    def connectionMade(self):
        self.factory.socks5_protocol.client_protocol = self
        self.write(self.factory.socks5_protocol.buffer)
        self.factory.socks5_protocol.buffer = ''

    def dataReceived(self, data):
        self.factory.socks5_protocol.write(data)

    def write(self, data):
        self.transport.write(data)

def server():
    _COMMUNITIES['Server'] = Server

    for i in [1]:
        configuration = get_default_configuration()
        configuration['keys'] = [{
            'alias': "my peer2",
            'generation': u"curve25519",
            'file': u"ec%d.pem" % i
        }]
        configuration['logger'] = {
            'level': 'DEBUG'
        }
        configuration['overlays'] = [{
            'class': 'Server',
            'key': "my peer2",
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
