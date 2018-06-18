from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from pyipv8.ipv8.deprecated.community import Community
from pyipv8.ipv8_service import _COMMUNITIES, IPv8
from pyipv8.ipv8.configuration import get_default_configuration
from pyipv8.ipv8.keyvault.crypto import ECCrypto
from pyipv8.ipv8.peer import Peer


class MyCommunity(Community):
    master_peer = Peer(ECCrypto().generate_key(u"medium"))

    def started(self):
        def print_peers():
            print "I am:", self.my_peer, "\nI know:", [str(p) for p in self.get_peers()]
        # We register a Twisted task with this overlay.
        # This makes sure that the task ends when this overlay is unloaded.
        # We call the 'print_peers' function every 5.0 seconds, starting now.
        self.register_task("print_peers", LoopingCall(print_peers)).start(5.0, True)


_COMMUNITIES['MyCommunity'] = MyCommunity


for i in [1, 2]:
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