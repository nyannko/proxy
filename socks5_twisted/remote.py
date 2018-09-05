from twisted.internet import reactor, protocol
from twisted.internet.protocol import Factory

import struct
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)


class RemoteProtocol(protocol.Protocol):

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
        host, port, request, index = self.unpack_address(data, 4)
        logger.debug("host:{}, port:{}, length of request:{}".format(host, port, len(request)))
        factory = self.create_client_factory()
        # buffer without id
        self.buffer = request
        print "request in remote addr",host, port,request,"selfbuffer",self.buffer
        print "index", index
        reactor.connectTCP(host, port, factory)

        # self.buffer = request[4:]

    def handle_REQUEST(self, data):
        print "request data", data
        index = data
        # data1 = data[4:]
        if self.client_protocol is not None:
            print "index", index, "request", data
            data1 = data[4:]
            self.client_protocol.write(data1)
        else:
            print "buffer before", self.buffer
            data2 = data[4:]
            self.buffer = self.buffer + data2
            print "self.buffer", self.buffer

    def create_client_factory(self):
        client_factory = protocol.ClientFactory()
        client_factory.protocol = ClientProtocol
        client_factory.socks5_protocol = self
        return client_factory

    def unpack_address(self, data, offset):
        print "dataaaa", data
        # print "data", data[0:4]
        index = data[0:offset]

        data_length, = struct.unpack('>B', data[0 + offset])
        address = data[0 + offset: 1 + offset + data_length]
        addr_type, = struct.unpack('>B', address[1])
        print addr_type

        host = ''
        if addr_type == 3:
            length = ord(address[2])
            host = address[3:3 + length]

        port, = struct.unpack('>H', address[-2:])

        request = data[1 + offset + data_length:]
        print "request!!!", request
        return host, port, request, index

    def write(self, data):
        self.transport.write(data)

    def connectionLost(self, reason):
        logger.error("connection lost:{}".format(reason))
        self.transport.loseConnection()


class ClientProtocol(protocol.Protocol):

    def connectionMade(self):
        self.factory.socks5_protocol.client_protocol = self
        print "write to", self.factory.socks5_protocol.buffer
        if self.factory.socks5_protocol.buffer.startswith("0"):
            self.factory.socks5_protocol.buffer=self.factory.socks5_protocol.buffer[5:]
            print "write to2", self.factory.socks5_protocol.buffer
        self.write(self.factory.socks5_protocol.buffer)
        self.factory.socks5_protocol.buffer = ''

    def dataReceived(self, data):
        self.factory.socks5_protocol.write(data)

    def write(self, data):
        self.transport.write(data)


class RemoteFactory(Factory):

    def __init__(self):
        pass

    def buildProtocol(self, addr):
        return RemoteProtocol(self)


def remote():
    reactor.listenTCP(50000, RemoteFactory())
    logger.debug("remote server is listening at port 50000")
    reactor.run()


if __name__ == '__main__':
    remote()
