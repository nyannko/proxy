from twisted.internet import reactor
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


key1 = ECCrypto().generate_key(u"medium")
# master_peer_init = Peer(key1)
logging.info(key1.pub().key_to_bin().encode('HEX'))
# master_peer_init = Peer(key1.pub().key_to_bin().encode('HEX').decode('HEX'))
master_peer_init = Peer(
    "307e301006072a8648ce3d020106052b81040024036a00040046d529db97b697d56b33d7935cd9213df309a7c3eb96a15c494ee72697f1d192c649d0666e903977de4a412649a28c970af0940155bfe7d7e0abd13e0bf7673b65f087a976deac412464c4959da06cc36945eee5017ec2007cca71841c6cddce8a84e525e64c88".decode(
        'HEX'))


class MyServer(Community):
    master_peer = master_peer_init

    def __init__(self, my_peer, endpoint, network):
        super(MyServer, self).__init__(my_peer, endpoint, network)
        self.decode_map[chr(1)] = self.on_message
        self.addr_set = set()
        self.conn_socks = {}

    def started(self):
        def start_communication():
            for p in self.get_peers():
                self.addr_set.add(p)

        self.register_task("start_communication", LoopingCall(start_communication)).start(1.0, True)

    def create_message(self, message):
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = MyMessage(message).to_pack_list()
        return self._ez_pack(self._prefix, 1, [auth, dist, payload])

    # Message API
    def on_message(self, source_address, data):
        auth, dist, payload = self._ez_unpack_auth(MyMessage, data)
        request_from_client = payload.message
        logging.debug(self.my_peer, "client requests:", request_from_client, source_address)
        self.handle_con(request_from_client)

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock

    def handle_con(self, request):
        stage = request[-6:]
        if stage == 'stage1':
            logging.debug("stage 1, {}".format(request))
            # '\x00\x00\x00\x01\x03\x0ewww.moe.edu.cn\x00Pstage1'
            id, = struct.unpack("!i", request[0:4])

            conn_type, = struct.unpack(">B", request[4])
            address, fqdn = "", ""
            if conn_type == 1:
                address = socket.inet_ntoa(request[6:9])
            if conn_type == 3:
                length, = struct.unpack(">B", request[5])
                logging.debug("request:{}, length:{}".format(request[5], length))
                fqdn = request[6:6 + length]
            if conn_type == 4:
                address, = struct.unpack(">H", request[1:16])
            port_number, = struct.unpack(">H", request[-8:-6])
            logging.debug(
                "conn type:{}, address:{}, fqdn:{}, port number:{}".format(conn_type, address, fqdn, port_number))

            port = int(port_number)
            self.conn_socks[id] = (fqdn, port)

        else:
            id, = struct.unpack(">i", request[0:4])
            logging.info("Start stage 2, connect to remote website")
            fqdn, port = self.conn_socks[id]
            logging.debug(self.conn_socks)
            logging.debug(fqdn, port)
            new_request = request[4:]
            logging.debug(new_request)

            if port == 80:
                threading.Thread(target=self.start_remote_sock, args=(fqdn, port, new_request, request[0:4])).start()

            # else:
            #     try:
            #         sock = self.create_socket()
            #         host, port = sock.getpeername()
            #         print "remote pair", host, port
            #         print "handle exception, create connection to"
            #         # if hostname doesn't exist
            #     except Exception as e:
            #         # sock = socket.create_connection((self.HOST, self.PORT))
            #         print e

    def start_remote_sock(self, fqdn, port, newrequest, id):
        sock = socket.create_connection((fqdn, port))
        self.handle_tcp(sock, newrequest, id)

    def handle_tcp(self, sock, request, id):
        logging.debug("The length of request: {}, id: {}".format(len(request), repr(id)))
        addr = [p.address for p in self.addr_set]
        if request:
            sock.sendall(request)
            response = ''
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                packet = self.create_message(id + data)
                self.endpoint.send(addr[0], packet)
                response += data
            logging.info("response length:{}".format(len(response)))
            logging.info("sent done")


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
