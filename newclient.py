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

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(thread)d %(funcName)s %(message)s')


class MyMessage(Payload):
    format_list = ['raw']

    def __init__(self, message):
        self.message = message

    def to_pack_list(self):
        return [('raw', self.message)]

    @classmethod
    def from_unpack_list(cls, message):
        return cls(message)


master_peer_init = Peer(
    "307e301006072a8648ce3d020106052b81040024036a00040046d529db97b697d56b33d7935cd9213df309a7c3eb96a15c494ee72697f1d192c649d0666e903977de4a412649a28c970af0940155bfe7d7e0abd13e0bf7673b65f087a976deac412464c4959da06cc36945eee5017ec2007cca71841c6cddce8a84e525e64c88".decode(
        'HEX'))

num_threads = 0

Lock = threading.Lock()


class MyClient(Community):
    master_peer = master_peer_init

    def __init__(self, my_peer, endpoint, network):
        super(MyClient, self).__init__(my_peer, endpoint, network)
        self.decode_map[chr(1)] = self.on_message
        self.HOST = "127.0.0.1"
        self.PORT = 40000
        self.addr_set = set()
        self.conn_socks = {}

    def started(self):
        def start_communication():
            for p in self.get_peers():
                if p not in self.addr_set:
                    self.addr_set.add(p)

        # Finding peers
        self.register_task("start_communication", LoopingCall(start_communication)).start(1.0, True)

        socketServer = self.create_srv_server()
        threads.deferToThread(self.start_socks5_server, socketServer)

    def create_srv_server(self):
        socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socketServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socketServer.bind((self.HOST, self.PORT))
        logging.info("Local client(socks5 server for browser) listening at: {}:{}".format(self.HOST, self.PORT))
        socketServer.listen(5)
        return socketServer

    def increase_sock_index(self):
        global num_threads
        num_threads += 1

    def start_socks5_server(self, socketServer):
        try:
            while True:
                sock, addr = socketServer.accept()
                logging.info("Receive connection from {}".format(addr))

                Lock.acquire()
                self.increase_sock_index()
                Lock.release()

                self.conn_socks[num_threads] = sock
                # threading.Thread(target=self.handle_conversation, args=(sock, addr)).start()
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
            logging.error(e)
        finally:
            sock.close()

    def handle_socks(self, sock):
        # Negotiation phase
        sock.recv(262)
        sock.send(b"\x05\x00")

        # Establish connection
        data = sock.recv(4)
        mode, = struct.unpack(">B", data[1])
        if mode != 1:
            logging.warn("Not a TCP connection")
            return

        addr_type, = struct.unpack('>B', data[3])
        addr_to_send = struct.pack('>i', num_threads)

        addr_to_send += data[3]
        address, fqdn = "", ""

        # IPv4
        if addr_type == 1:
            address = sock.recv(4)
            address = struct.unpack(">H", address)
            addr_to_send += address

        # Domain
        if addr_type == 3:
            length, = struct.unpack(">B", sock.recv(1))
            fqdn = sock.recv(length)
            addr_to_send += struct.pack('>B', length) + fqdn

        # IPv6
        if addr_type == 4:
            address = sock.recv(16)

        port = sock.recv(2)
        port_number = struct.unpack(">H", port)
        addr_to_send += port
        # identifier for stage1
        addr_to_send += "stage1"

        logging.debug("Handle request from client: " + \
                      "Address type: {}, address: {}, fqdn: {}, port number: {}" \
                      .format(addr_type, address, fqdn, port_number))

        logging.debug(repr(addr_to_send))

        # send reply
        reply = b"\x05\x00\x00\x01"
        reply += socket.inet_aton('0.0.0.0') + struct.pack('>H', self.PORT)
        sock.send(reply)

        # stage1 send address to server
        if addr_to_send:
            for p in self.get_peers():
                packet = self.create_message(addr_to_send)
                self.endpoint.send(p.address, packet)

        # For message transition in stage 2
        self.handle_con(sock)

    def handle_con(self, sock):
        addr = [p.address for p in self.get_peers()]
        while True:
            # send request segment to server
            data = sock.recv(4096)
            id = struct.pack('>i', num_threads)
            logging.debug("num_threads:{}, id:{}".format(num_threads, repr(id)))
            if not data:
                logging.info('No more data from browser')
                break
            if addr:
                packet = self.create_message(id + data)
                self.endpoint.send(addr[0], packet)

    def create_message(self, message):
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = MyMessage(message).to_pack_list()
        return self._ez_pack(self._prefix, 1, [auth, dist, payload])

    def on_message(self, source_address, data):
        auth, dist, payload = self._ez_unpack_auth(MyMessage, data)
        id, = struct.unpack("!i", payload.message[0:4])
        logging.debug(self.conn_socks)
        sock = self.conn_socks[id]
        response = payload.message[4:]
        result = sock.sendall(response)
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
