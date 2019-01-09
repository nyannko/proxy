from binascii import unhexlify

from flask import logging
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from pyipv8.ipv8.deprecated.community import Community
from pyipv8.ipv8_service import _COMMUNITIES, IPv8
from pyipv8.ipv8.configuration import get_default_configuration
from pyipv8.ipv8.keyvault.crypto import ECCrypto
from pyipv8.ipv8.peer import Peer

key1 = ECCrypto().generate_key(u"medium")
# master_peer_init = Peer(key1)
print key1.pub().key_to_bin().encode('HEX')
# master_peer_init = Peer(key1.pub().key_to_bin().encode('HEX').decode('HEX'))
print key1.pub().key_to_bin().encode('HEX')

class MyCommunity(Community):
    master_peer = Peer(
    "307e301006072a8648ce3d020106052b81040024036a000400d6911c823cfddc8842131e0306795ba9e652f8f0ecfe627b70d5469b30de14d3289b2899ffb655bc8e01631c9a7fbfecd5db42017718bdcd0e5acf218494e4085277e048ecb34e30218d0f3131c45627b345789753109b570d987c679ecb99a9a85c072de67bc6"
        .decode('HEX'))

    def started(self):
        def print_peers():
            print "I am:", self.endpoint.get_address(), repr(self.my_peer.mid), "\nI know:", [str(p) for p in self.get_peers()]
            print "address", self.network._all_addresses
            print "blacklist", self.network.blacklist, self.network.blacklist_mids
        # We register a Twisted task with this overlay.
        # This makes sure that the task ends when this overlay is unloaded.
        # We call the 'print_peers' function every 5.0 seconds, starting now.
        self.register_task("print_peers", LoopingCall(print_peers)).start(5.0, True)


_COMMUNITIES['MyCommunity'] = MyCommunity


for i in [4]:
    configuration = get_default_configuration()
    configuration['keys'] = [{
                'alias': "my peer",
                'generation': u"medium",
                'file': u"ec%d.pem" % i
            }]
    # We provide the 'started' function to the 'on_start'.
    # We will call the overlay's 'started' function without any
    # arguments once IPv8 is initialized.
    configuration['overlays'] = [{
        'class': 'MyCommunity',
        'key': "my peer",
        'walkers': [{
                        'strategy': "RandomWalk",
                        'peers': 10,
                        'init': {
                            'timeout': 3.0
                        }
                    }],
        'initialize': {},
        'on_start': [('started', )]
    }]
    IPv8(configuration)

reactor.run()