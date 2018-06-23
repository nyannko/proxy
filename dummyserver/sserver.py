from twisted.internet import reactor, threads
from twisted.internet.task import LoopingCall
from twisted.internet.defer import Deferred

from pyipv8.ipv8.deprecated.community import Community
from pyipv8.ipv8.deprecated.payload import Payload
from pyipv8.ipv8.deprecated.payload_headers import BinMemberAuthenticationPayload, GlobalTimeDistributionPayload
from pyipv8.ipv8_service import _COMMUNITIES, IPv8
from pyipv8.ipv8.configuration import get_default_configuration
from pyipv8.ipv8.keyvault.crypto import ECCrypto
from pyipv8.ipv8.peer import Peer

import socket
import struct
import select
import threading
import logging


class MyMessage(Payload):
    # When reading data, we unpack an unsigned integer from it.
    format_list = ['raw']

    def __init__(self, message):
        self.message = message

    def to_pack_list(self):
        # We convert this object by writing 'self.clock' as
        # an unsigned int. This conforms to the 'format_list'.
        return [('raw', self.message)]

    @classmethod
    def from_unpack_list(cls, message):
        # We received arguments in the format of 'format_list'.
        # We instantiate our class using the unsigned int we
        # read from the raw input.
        return cls(message)


key1 = ECCrypto().generate_key(u"medium")
# master_peer_init = Peer(key1)
print key1.pub().key_to_bin().encode('HEX')
# master_peer_init = Peer(key1.pub().key_to_bin().encode('HEX').decode('HEX'))
master_peer_init = Peer(
    "307e301006072a8648ce3d020106052b81040024036a00040046d529db97b697d56b33d7935cd9213df309a7c3eb96a15c494ee72697f1d192c649d0666e903977de4a412649a28c970af0940155bfe7d7e0abd13e0bf7673b65f087a976deac412464c4959da06cc36945eee5017ec2007cca71841c6cddce8a84e525e64c88".decode(
        'HEX'))


class MyServer(Community):
    master_peer = master_peer_init

    def __init__(self, my_peer, endpoint, network):
        super(MyServer, self).__init__(my_peer, endpoint, network)
        # Register the message handler for messages with the
        # chr(1) identifier.
        # self.decode_map[chr(1)] = self.on_message
        # The Lamport clock this peer maintains.
        # This is for the example of global clock synchronization.
        # self.lamport_clock = 0
        self.HOST = "127.0.0.1"
        self.PORT = 50000

    def started(self):
        def start_communication():
            pass

        # self.register_task("start_communication", LoopingCall(start_communication)).start(5.0, True)
        self.register_task("start_communication", Deferred().addCallback(start_communication))

        socketServer = self.create_srv_server()
        for i in range(100):
            threads.deferToThread(self.start_socks5_server, socketServer)

    def create_srv_server(self):
        socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socketServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socketServer.bind((self.HOST, self.PORT))
        print "Local client(socks5_twisted server for browser) listening at: {}:{}".format(self.HOST, self.PORT)
        socketServer.listen(5)
        return socketServer

    def start_socks5_server(self, socketServer):
        try:
            while True:
                sock, addr = socketServer.accept()
                print "Receive connection from {}".format(addr)
                self.handle_conversation(sock, addr)
        except socket.error as e:
            logging.error(e)
        except KeyboardInterrupt:
            socketServer.close()

    def handle_conversation(self, sock, addr):
        try:
            while True:
                self.handle_con(sock)
        except Exception as e:
            print "Client {} error: {}".format(addr, e)
        finally:
            sock.close()

    def create_message(self, message):
        # Create a message with our digital signature on it.
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = MyMessage(message).to_pack_list()
        # We pack our arguments as message 1 (corresponding to the
        # 'self.decode_map' entry.
        return self._ez_pack(self._prefix, 1, [auth, dist, payload])

    def on_message(self, source_address, data):
        request_from_client = ''
        while True:
            auth, dist, payload = self._ez_unpack_auth(MyMessage, data)
            if len(payload.message) <= 0:
                break
            request_from_client += payload.message
            # print request_from_client
        print self.my_peer, "client requests:", request_from_client, source_address
        self.handle_tcp(request_from_client)

    def handle_con(self, sock):

        addrtype = ord(sock.recv(1))  # receive addr type
        addr = ''
        if addrtype == 1:
            pass
        elif addrtype == 3:
            len = ord(sock.recv(1))  # read 1 byte of len, then get 'len' bytes name
            addr = sock.recv(len)
        else:
            logging.warn('addr_type not support')
            return
        port = struct.unpack('>H', sock.recv(2))

        print "connect to {}:{}".format(addr, port)
        remote = socket.create_connection((addr, port[0]))
        print "Stage 1 finished, connect to website {}:{}".format(addr, port)

        self.handle_tcp(sock, remote)

    def handle_tcp(self, sock, remote):
        try:
            fdset = [sock, remote]
            while True:
                r, w, e = select.select(fdset, [], [])  # use select I/O multiplexing model
                if sock in r:  # if local socket is ready for reading
                    data = sock.recv(4096)
                    print data
                    if len(data) <= 0:  # received all data
                        break
                    result = remote.sendall(data)  # send data after encrypting
                    if result is not None:
                        raise Exception('failed to send all data')

                if remote in r:  # remote socket(proxy) ready for reading
                    data = remote.recv(4096)
                    print data
                    if len(data) <= 0:
                        break
                    result = sock.sendall(data)  # send to local socket(application)
                    if result is not None:
                        raise Exception('failed to send all data')
        finally:
            sock.close()
            remote.close()


_COMMUNITIES['MyServer'] = MyServer

for i in [1]:
    configuration = get_default_configuration()
    configuration['keys'] = [{
        'alias': "my peer",
        'generation': u"medium",
        'file': u"ec%d.pem" % i
    }]
    configuration['overlays'] = [{
        'class': 'MyServer',
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

reactor.run()
