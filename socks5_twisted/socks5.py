import pickle

from twisted.internet import reactor, protocol
from twisted.internet.protocol import Factory, ClientFactory

import struct
import logging
import socket
import os
from socks5_twisted.Message import Message

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.FileHandler('client_debug_pack.txt')
st = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
ch.setFormatter(formatter)
st.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(st)


class Socks5Protocol(protocol.Protocol):

    def __init__(self, factory):
        self.socks5_factory = factory
        self.state = 'NEGOTIATION'
        self.buffer = None
        self.client_protocol = None

    def connectionMade(self):
        address = self.transport.getPeer()
        logging.info("Receive {} connection from {}:{}".format(address.type, address.host, address.port))

    def dataReceived(self, data):
        if self.state == 'NEGOTIATION':
            self.handle_NEGOTIATION(data)
            self.state = 'REQUEST'

        elif self.state == 'REQUEST':
            self.handle_REQUEST(data)
            self.state = 'TRANSMISSION'

        elif self.state == 'TRANSMISSION':
            self.handle_TRANSMISSION(data)

    def handle_NEGOTIATION(self, data):
        self.transport.write('\x05\x00')

    def handle_REQUEST(self, data):
        addr_to_send = self.unpack_request_data(data)
        client_factory = ClientsFactory(self)
        self.idx = self.get_ID()
        data_to_send = Message(self.idx, addr_to_send).to_bytes()
        self.buffer = data_to_send
        reactor.connectTCP('localhost', 50000, client_factory)

    # trying to implement buffer here.
    # https://stackoverflow.com/questions/33949409/twisted-protocol-to-handle-concantenated-tcp-stream-with-custom-frame-structure
    def handle_TRANSMISSION(self, data):
        data_send = Message(self.idx, data).to_bytes()
        if self.client_protocol is not None:
            self.client_protocol.write(data_send)
        else:
            self.buffer += data_send

    def unpack_address(self, data):
        addr_type, = struct.unpack('>B', data[0])
        host = ''
        if addr_type == 3:
            length = ord(data[1])
            host = data[2:2 + length]

        port, = struct.unpack('>H', data[-2:])

        return host, port

    def unpack_request_data(self, data):
        socks_version, = struct.unpack('>B', data[0])
        cmd, = struct.unpack('>B', data[1])

        addr_type, = struct.unpack('>B', data[3])
        addr_to_send = data[3]

        if addr_type == 3:
            domain_len, = struct.unpack('>B', data[4])
            addr_to_send += data[4: 5 + domain_len]

        port, = struct.unpack('>H', data[-2:])
        addr_to_send += data[-2:]
        logger.debug("version:{}, cmd:{}, addr_type:{}, port:{}".format(socks_version, cmd, addr_type, port))

        reply = b"\x05\x00\x00\x01"
        reply += socket.inet_aton('0.0.0.0') + struct.pack('>H', port)
        self.transport.write(reply)

        length = struct.pack('>B', len(addr_to_send))

        addr_to_send = length + addr_to_send

        return addr_to_send

    def write(self, data):
        self.transport.write(data)

    def connectionLost(self, reason):
        logger.error("connection lost:{}".format(reason))
        self.transport.loseConnection()

    def get_ID(self):
        self.socks5_factory.seq_id = '%32d' % (int(self.socks5_factory.seq_id) + 1)
        # self.socks5_factory.seq_id = os.urandom(4)
        # print "id from client", self.socks5_factory.seq_id
        # while seq_id not in self.socks5_factory.socks:
        seq_id = self.socks5_factory.seq_id
        self.socks5_factory.socks[seq_id] = self
        return seq_id


class Socks5Factory(Factory):

    def __init__(self):
        self.socks = {}
        self.seq_id = 0

    def buildProtocol(self, addr):
        return Socks5Protocol(self)


class ClientProtocol(protocol.Protocol):

    def __init__(self, client_factory):
        self.client_factory = client_factory

    def connectionMade(self):
        self.client_factory.socks5_protocol.client_protocol = self
        if self.client_factory.socks5_protocol.buffer is not None:
            self.write(self.client_factory.socks5_protocol.buffer)
        self.client_factory.socks5_protocol.buffer = ''

    def dataReceived(self, data):
        self.client_factory.socks5_protocol.write(data)

    def write(self, data):
        self.transport.write(data)


class ClientsFactory(ClientFactory):

    def __init__(self, socks5_protocol):
        self.socks5_protocol = socks5_protocol

    def buildProtocol(self, addr):
        return ClientProtocol(self)


def socks5():
    reactor.listenTCP(40000, Socks5Factory())
    logger.debug("socks5_twisted server is listening at port 40000")
    reactor.run()


if __name__ == '__main__':
    socks5()
