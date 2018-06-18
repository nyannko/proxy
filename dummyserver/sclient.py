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
import select
import SocketServer


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
        self.request = ""
        self.HOST = "127.0.0.1"
        self.PORT = 40000
        self.res = b""
        self.messagecount = 0

    def started(self):
        def start_communication():
            if not self.request:
                for p in self.get_peers():
                    print "I'm {}, I know my server peer: {}".format(self.my_peer, p)
                    packet = self.create_message(self.request)
            else:
                self.cancel_pending_task("start_communication")

        # self.register_task("start_communication", LoopingCall(start_communication)).start(20.0, True)
        self.register_task("start_communication", Deferred().addCallback(start_communication))

        socketServer = self.create_srv_socket()
        for i in range(100):
            threads.deferToThread(self.start_socks5_server, socketServer)
        #self.start_socks5_server(socketServer)

    def create_srv_socket(self):
        socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socketServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        socketServer.bind((self.HOST, self.PORT))
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
                self.handle_socks(sock)
        except Exception as e:
            print "Client {} error {}".format(addr, e)
        finally:
            sock.close()

    def handle_socks(self, sock):

        # Handshake phase
        sock.recv(256)
        sock.send(b"\x05\x00")

        # Establish connection
        data = sock.recv(4)
        mode = struct.unpack(">B", data[1])[0]
        if mode != 1:
            print "Not a TCP connection"
            return

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

        print "Handle request from client: " + \
              "Address type: {}, address: {}, fqdn: {}, port number: {}" \
                  .format(addr_type, address, fqdn, port_number)

        print addr_to_send

        # send reply
        reply = b"\x05\x00\x00\x01"
        reply += socket.inet_aton('0.0.0.0') + struct.pack('>H', self.PORT)
        sock.send(reply)

        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # turn off Nagling
        print fqdn, port_number[0]

        remote.connect(('127.0.0.1', 50000))
        remote.send(addr_to_send)
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
                    if len(data) <= 0:
                        break
                    result = sock.sendall(data)  # send to local socket(application)
                    if result is not None:
                        raise Exception('failed to send all data')
        finally:
            sock.close()
            remote.close()

    def create_message(self, message):
        # Create a message with our digital signature on it.
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = MyMessage(message).to_pack_list()
        # We pack our arguments as message 1 (corresponding to the
        # 'self.decode_map' entry.
        return self._ez_pack(self._prefix, 1, [auth, dist, payload])

    def on_message(self, source_address, data):
        # We received a message with identifier 1.
        # Try unpacking it.
        auth, dist, payload = self._ez_unpack_auth(MyMessage, data)
        # If unpacking was successful, update our Lamport clock.
        self.messagecount += 1
        print "This is the {} time to call on_message.".format(self.messagecount)
        response = payload.message
        # print self.my_peer, "server response:", response
        print response
        self.res += response
        # Then synchronize with the rest of the network again.
        # packet = self.create_message(response)
        # self.endpoint.send(source_address, packet)


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
