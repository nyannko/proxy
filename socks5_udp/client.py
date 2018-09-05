from twisted.internet import reactor, protocol
from twisted.internet.protocol import Factory
from twisted.internet.task import LoopingCall
from twisted.python import log

from pyipv8.ipv8.attestation.trustchain.community import TrustChainCommunity
from pyipv8.ipv8.deprecated.payload_headers import BinMemberAuthenticationPayload, GlobalTimeDistributionPayload
from pyipv8.ipv8_service import _COMMUNITIES, IPv8
from pyipv8.ipv8.configuration import get_default_configuration
from pyipv8.ipv8.peer import Peer

import socket
import struct
import os

import time
import random

from payload import IdentityRequestPayload, IdentityResponsePayload, TargetAddressPayload, Message, PayoutPayload

master_peer_init = Peer(
    "307e301006072a8648ce3d020106052b81040024036a00040112bc352a3f40dd5b6b34f28c82636b3614855179338a1c2f9ac87af17f5af3084955c4f58d9a48d35f6216aac27d68e04cb6c200025046155983a3ae1378320d93e3d865c6ab63b3f11a6c74fc510fa67b2b5f448de756b4114f765c80069e9faa51476604d9d4"
        .decode('HEX'))


class Client(TrustChainCommunity):
    master_peer = master_peer_init

    DB_NAME = 'trustchain_client'

    def __init__(self, my_peer, endpoint, network):
        super(Client, self).__init__(my_peer, endpoint, network)
        self.host_dict = {}
        self.server_dict = {}
        self.socks5_factory = Socks5Factory(self)

        self._balance = 0

        self.decode_map.update({
            chr(7): self.on_identity_request,
            chr(8): self.on_identity_response,
            chr(10): self.on_message
        })

    def started(self):

        def start_communication():
            for p in self.get_peers():
                if p not in self.host_dict:
                    self.logger.info("New Host {} join the network".format(p))
                    self.send_identity_request("identity?", p)
                    self.host_dict.update({p: None})

        self.register_task("start_communication", LoopingCall(start_communication)).start(1.0, True).addErrback(log.err)

    # run in an enclave(?)
    def create_client_transaction(self):
        timestamp = int(round(time.time() * 1000))
        debit = 0
        credit = 1
        self._balance += debit - credit
        bill = {'time': timestamp, 'identity': 'client->', 'debit': debit, 'credit': credit, 'balance': self._balance}
        return bill

    # choose a random peer to sign the tx
    def send_sign(self):
        random_peer = random.choice(self.host_dict.keys())
        random_peer_pubkey = random_peer.public_key.key_to_bin()
        transaction = self.create_client_transaction()
        self.sign_block(random_peer, public_key=random_peer_pubkey, block_type='test', transaction=transaction)

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
            self.send_identity_response("client", source_address)
        else:
            self.logger("client id request error, {}".format(response))

    def on_identity_response(self, source_address, data):
        auth, dist, payload = self._ez_unpack_auth(IdentityResponsePayload, data)
        response = payload.message
        # todo check server or client
        if response == 'server':
            self.logger.info("server comes from: {}".format(source_address))
            for host in self.host_dict.keys():
                if host.address == source_address:
                    self.server_dict.update({host: None})
                    self.logger.info("server.dict: {}, host.dict: {}".format(self.server_dict, self.host_dict))

            self.register_task("start_credit", LoopingCall(self.send_sign)).start(30.0, True).addErrback(log.err)

        elif response == 'client':
            self.logger.info("client comes from: {}".format(source_address))

    def create_identity_response(self, data):
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = IdentityResponsePayload(data).to_pack_list()
        return self._ez_pack(self._prefix, 8, [auth, dist, payload])

    def send_identity_response(self, data, source_address):
        packet = self.create_identity_response(data)
        self.endpoint.send(source_address, packet)

        # Start socks5 twisted server
        port = 40000
        try:
            reactor.listenTCP(port, self.socks5_factory)
        except Exception as e:
            self.logger.debug(e.message)
            port += 1
            reactor.listenTCP(port, self.socks5_factory)

        self.logger.info("socks5_twisted server listening at port {}".format(port))

    def create_target_address(self, data):
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = TargetAddressPayload(data).to_pack_list()
        # print "payload", payload
        return self._ez_pack(self._prefix, 9, [auth, dist, payload])

    def send_target_address(self, data, p):
        packet = self.create_target_address(data)
        self.endpoint.send(p.address, packet)

    def create_message(self, message):
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = Message(message).to_pack_list()
        # print "payload message", payload
        return self._ez_pack(self._prefix, 10, [auth, dist, payload])

    def on_message(self, source_address, data):
        """ Write response from server to browser """

        auth, dist, payload = self._ez_unpack_auth(Message, data)
        res = payload.message
        # print "onmessage", res
        seq_id = res[0:4]
        # print seq_id
        response = res[4:]
        # print response
        # logging.debug("send back response id:{} to protocol:{}", repr(seq_id), self.socks5_factory.socks[seq_id])
        # print "self.socks5_factory.socks", self.socks5_factory.socks
        # print repr(seq_id), "browser!!!", repr(response)
        # print self.socks5_factory
        self.socks5_factory.socks[seq_id].transport.write(response)
        # self.socks5_factory.socks.transport.write(response)


class Socks5Protocol(protocol.Protocol):

    def __init__(self, factory):
        self.socks5_factory = factory
        self.state = 'NEGOTIATION'
        self.target_address = None

    def connectionMade(self):
        address = self.transport.getPeer()
        # logger.info("Receive {} connection from {}:{}".format(address.type, address.host, address.port))

    def dataReceived(self, data):
        if self.state == 'NEGOTIATION':
            # logger.debug("1.start socks5_twisted handshake")
            self.handle_NEGOTIATION(data)
            self.state = 'REQUEST'

        elif self.state == 'REQUEST':
            # logger.debug("2.handshake success, start request phase")
            self.handle_REQUEST(data)
            self.state = 'TRANSMISSION'

        elif self.state == 'TRANSMISSION':
            # logger.debug("3.start data transmission")
            self.handle_TRANSMISSION(data)

    def handle_NEGOTIATION(self, data):
        self.transport.write('\x05\x00')

    def handle_REQUEST(self, data):
        # print "mydata2", data
        target_address, target_port = self.unpack_request_data(data)
        self.seq_id = self.get_ID()
        # print "ididididhandle", self.seq_id
        target_address = self.seq_id + target_address
        print self.seq_id
        # send id with address
        self.send_address(target_address)

    def send_address(self, data):
        for p in self.socks5_factory.client.server_dict.keys():
            packet = self.socks5_factory.client.create_target_address(data)
            self.socks5_factory.client.endpoint.send(p.address, packet)

    def handle_TRANSMISSION(self, data):
        """ Send packed data to server """
        # seq_id = self.register_ID()
        # print "length of data", len(data)
        # print "idididid", self.seq_id
        self.send_data(self.seq_id + data)

        # check encode
        test_packet = self.socks5_factory.client.create_message(data)
        auth, dist, payload = self.socks5_factory.client._ez_unpack_auth(Message, test_packet)
        # if data == payload.message:
        #     print "encode correct"
        # else:
        #     print "encode wrong"
        # check encode

        # self.send_data(self.seq_id, data)
        # print "whatsinsocks", self.socks5_factory

    def get_ID(self):
        self.socks5_factory.seq_id = '%04d' % (int(self.socks5_factory.seq_id) + 1)
        # print "id from client", self.socks5_factory.seq_id
        # while seq_id not in self.socks5_factory.socks:
        seq_id = self.socks5_factory.seq_id
        self.socks5_factory.socks[seq_id] = self
        return seq_id

    def register_ID(self):
        seq_id = os.urandom(4)
        # print "id from client", repr(seq_id)
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

        if addr_type == 1:
            # logging.debug(socket.inet_ntoa(data[offset: offset + 4]))
            target_address += data[offset: offset + 4]
            offset += 4

        if addr_type == 3:
            domain_len, = struct.unpack('>B', data[offset])
            target_address += data[offset: offset + 1 + domain_len]
            offset += domain_len + 1

        port, = struct.unpack('>H', data[offset:offset + 2])
        target_address += data[offset:offset + 2]
        # logger.debug("version:{}, cmd:{}, addr_type:{}, port:{}".format(socks_version, cmd, addr_type, port))

        reply = b'\x05\x00\x00\x01'
        host_address = self.transport.getHost()
        # logging.debug("socks5_twisted send success message to {}".format(host_address))
        reply += ''.join(self.get_packed_address(host_address))
        self.transport.write(reply)

        return target_address, port

    # Send to peer(not chunk)
    def send_data(self, data):
        for p in self.socks5_factory.client.server_dict.keys():
            packet = self.socks5_factory.client.create_message(data)
            self.socks5_factory.client.endpoint.send(p.address, packet)

    # Send to peer(chunked)
    # def send_data(self, id, data):
    #     for p in self.socks5_factory.client.server_dict.keys():
    #         bytes_sent = 0
    #         while bytes_sent < len(data):
    #             chunk_data = data[bytes_sent:bytes_sent + 4096]
    #             packet = self.socks5_factory.client.create_message(id + chunk_data)
    #             self.socks5_factory.client.endpoint.send(p.address, packet)
    #             bytes_sent += 4096

    def write(self, data):
        self.transport.write(data)

    def connectionLost(self, reason):
        # if self.seq_id in self.socks5_factory.socks:
        #     del self.socks5_factory.socks[self.seq_id]
        # logger.debug("connection lost:{}".format(reason.getErrorMessage()))
        self.transport.loseConnection()


class Socks5Factory(Factory):

    def __init__(self, client):
        self.client = client
        self.socks = {}
        self.seq_id = 0

    def buildProtocol(self, addr):
        return Socks5Protocol(self)


def client():
    _COMMUNITIES['Client'] = Client

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
