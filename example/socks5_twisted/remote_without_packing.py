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
        host, port, request = self.unpack_address(data)
        logger.debug("host:{}, port:{}, length of request:{}".format(host, port, len(request)))
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

    def write(self, data):
        self.transport.write(data)

    def connectionLost(self, reason):
        logger.error("connection lost:{}".format(reason))
        self.transport.loseConnection()


class ClientProtocol(protocol.Protocol):

    def connectionMade(self):
        self.factory.socks5_protocol.client_protocol = self
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