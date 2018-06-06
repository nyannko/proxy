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


master_peer_init = Peer(
    "307e301006072a8648ce3d020106052b81040024036a00040046d529db97b697d56b33d7935cd9213df309a7c3eb96a15c494ee72697f1d192c649d0666e903977de4a412649a28c970af0940155bfe7d7e0abd13e0bf7673b65f087a976deac412464c4959da06cc36945eee5017ec2007cca71841c6cddce8a84e525e64c88".decode(
        'HEX'))


class MyClient(Community):
    master_peer = master_peer_init

    def __init__(self, my_peer, endpoint, network):
        super(MyClient, self).__init__(my_peer, endpoint, network)
        # Register the message handler for messages with the
        # chr(1) identifier.
        self.decode_map[chr(1)] = self.on_message
        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # The Lamport clock this peer maintains.
        # This is for the example of global clock synchronization.
        self.HOST = "127.0.0.1"
        self.PORT = 40000
        self.addrset = set()

    def started(self):
        def start_communication():
            for p in self.get_peers():
                if p not in self.addrset:
                    self.addrset.add(p)

        self.register_task("start_communication", LoopingCall(start_communication)).start(1.0, True)
        threads.deferToThread(self.start_socks5_server())

    def start_socks5_server(self):

        socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socketServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        socketServer.bind((self.HOST, self.PORT))
        print "Local client(socks5 server for browser) listening at: {}:{}".format(self.HOST, self.PORT)

        socketServer.listen(1)

        try:
            while True:
                self.sock, addr = socketServer.accept()
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                print "Receive connection from {}".format(addr)
                # t = threading.Thread(target=self.handle_con, args=(self.sock,))
                # t.start()
                self.handle_socks(self.sock, )
        except socket.error as e:
            logging.error(e)
        except KeyboardInterrupt:
            socketServer.close()

    def handle_socks(self, sock):
        # Negotiation phase
        sock.recv(262)
        sock.send(b"\x05\x00")

        # Establish connection
        data = sock.recv(4)
        print "last", repr(data)
        mode = struct.unpack(">B", data[1])[0]
        if mode != 1:
            print "Not a TCP connection"
            return

        # conn_type = struct.unpack('>B', data[2])[0]
        # if conn_type == 1:
        #     print "This is a TCP connection"
        # if conn_type == 3:
        #     print "This is a UDP connection"

        addr_type = struct.unpack('>B', data[3])[0]
        # print "addr type:{}, data[3]:{}".format(addr_type, data[3])
        addr_to_send = b"" + data[3]
        address, fqdn = "", ""
        if addr_type == 1:
            print "IPv4 address"
            address = sock.recv(4)
            address = struct.unpack(">H", address)
            addr_to_send += address

        if addr_type == 3:
            print "FQDN address"
            length = struct.unpack(">B", sock.recv(1))[0]
            fqdn = sock.recv(length)
            addr_to_send += struct.pack('>B', length) + fqdn

        if addr_type == 4:
            address = sock.recv(16)
            print "IPv6 address, not implemented yet"

        port = sock.recv(2)
        port_number = struct.unpack(">H", port)
        addr_to_send += port
        # identifier for stage1
        addr_to_send += "stage1"

        print "Handle request from client: " + \
              "Address type: {}, address: {}, fqdn: {}, port number: {}" \
                  .format(addr_type, address, fqdn, port_number)

        print repr(addr_to_send)

        # send reply
        reply = b"\x05\x00\x00\x01"
        reply += socket.inet_aton('0.0.0.0') + struct.pack('>H', self.PORT)
        sock.send(reply)

        # stage1 send address to server
        if addr_to_send:
            for p in self.get_peers():
                print "Stage 1: send address to {}".format(p.address)
                packet = self.create_message(addr_to_send)
                self.endpoint.send(p.address, packet)

        # For message transition in stage 2
        self.handle_con(sock)

    def handle_con(self, sock):
        print "handle_socks"
        addr = [p.address for p in self.get_peers()]
        print addr
        while True:
            print "waiting for data from sock"
            # send request segment to server
            data = sock.recv(4096)
            # sock.setblocking(0)
            print "block in recv"
            print data
            if not data:
                print "ahhhhhh"
                break
            if addr:
                packet = self.create_message(data)
                self.endpoint.send(addr[0], packet)
        print "receive end"

    def create_message(self, message):
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = MyMessage(message).to_pack_list()
        return self._ez_pack(self._prefix, 1, [auth, dist, payload])

    def on_message(self, source_address, data):
        auth, dist, payload = self._ez_unpack_auth(MyMessage, data)
        # if payload.message:
        print "payload message", payload.message, self.sock
        result = self.sock.sendall(payload.message)
        if result is not None:
            raise Exception("failed to send all data")


_COMMUNITIES['MyClient'] = MyClient

for i in [2]:
    configuration = get_default_configuration()
    configuration['keys'] = [{
        'alias': "my peer",
        'generation': u"medium",
        'file': u"ec%d.pem" % i
    }]
    configuration['overlays'] = [{
        'class': 'MyClient',
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
