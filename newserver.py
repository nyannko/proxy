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
import select
import time
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
        self.decode_map[chr(1)] = self.on_message
        self.remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.addrset = set()
        self.HOST = '127.0.0.1'
        self.PORT = '50000'

    def started(self):
        def start_communication():
            for p in self.get_peers():
                self.addrset.add(p)

        self.register_task("start_communication", LoopingCall(start_communication)).start(1.0, True)

    def create_message(self, message):
        auth = BinMemberAuthenticationPayload(self.my_peer.public_key.key_to_bin()).to_pack_list()
        dist = GlobalTimeDistributionPayload(self.claim_global_time()).to_pack_list()
        payload = MyMessage(message).to_pack_list()
        return self._ez_pack(self._prefix, 1, [auth, dist, payload])

    def on_message(self, source_address, data):
        auth, dist, payload = self._ez_unpack_auth(MyMessage, data)
        request_from_client = payload.message
        print self.my_peer, "client requests:", request_from_client, source_address
        self.handle_con(request_from_client)

    def handle_con(self, request):
        stage = request[-6:]
        print "stage is {}".format(stage)
        if stage == 'stage1':
            print repr(request)
            conn_type = struct.unpack(">B", request[0])[0]
            address, fqdn = "", ""
            if conn_type == 1:
                # address = struct.unpack(">H",request[1:4])[0]
                address = socket.inet_ntoa(request[1:4])
            if conn_type == 3:
                length = struct.unpack(">B", request[1])[0]
                print "request:{}, length:{}".format(request[1], length)
                fqdn = request[2:2 + length]
            if conn_type == 4:
                address = struct.unpack(">H", request[1:16])[0]
            port_number = struct.unpack(">H", request[-8:-6])[0]

            print "conn type:{}, address:{}, fqdn:{}, port number:{}".format(conn_type, address, fqdn, port_number)

            port = int(port_number)
            self.HOST = fqdn
            self.PORT = port

            print "Stage 1 finished, start to connect to website {}:{}".format(fqdn, port)

        else:
            print "Start stage 2, connect to remote website"
            if self.PORT == 80:
                self.remote = socket.create_connection((self.HOST, self.PORT))
            else:
                try:
                    host, port = self.remote.getpeername()
                    print "remote pair", host, port
                except:
                    print "handle exception, create connection to"
                    # if hostname doesn't exist
                    self.remote = socket.create_connection((self.HOST, self.PORT))

            self.handle_tcp(request)

    def handle_tcp(self, request):
        print "The length of request", len(request)
        addr = [p.address for p in self.addrset]
        if request:
            print request
            self.remote.sendall(request)
            response = ''
            while True:
                data = self.remote.recv(4096)
                if not data:
                    break
                packet = self.create_message(data)
                self.endpoint.send(addr[0], packet)
                response += data
            print "response:{}, length:{}".format(response, len(response))
            print "sent done"
            # self.remote.close()


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

# example request
# request = "GET / HTTP/1.1\r\n" + \
#           "Host: www.moe.edu.cn\r\n" + \
#           "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:60.0) Gecko/20100101 Firefox/60.0\r\n" + \
#           "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n" + \
#           "Accept-Language: en-US,en;q=0.5\r\n" + \
#           "Accept-Encoding: gzip, deflate\r\n" + \
#           "DNT: 1\r\n" + \
#           "Connection: keep-alive\r\n" + \
#           "Upgrade-Insecure-Requests: 1\r\n\r\n"
