from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.python import log

from pyipv8.ipv8.deprecated.community import Community
from pyipv8.ipv8.messaging.anonymization.community import TunnelCommunity, TunnelSettings
from pyipv8.ipv8_service import _COMMUNITIES, IPv8
from pyipv8.ipv8.configuration import get_default_configuration
from pyipv8.ipv8.keyvault.crypto import ECCrypto
from pyipv8.ipv8.peer import Peer


class MyCommunity(TunnelCommunity):
    master_peer = Peer(
        "307e301006072a8648ce3d020106052b81040024036a00040112bc352a3f40dd5b6b34f28c82636b3614855179338a1c2f9ac87af17f5af3084955c4f58d9a48d35f6216aac27d68e04cb6c200025046155983a3ae1378320d93e3d865c6ab63b3f11a6c74fc510fa67b2b5f448de756b4114f765c80069e9faa51476604d9d4"
        .decode('HEX'))

    def __init__(self, my_peer, endpoint, network):
        super(MyCommunity, self).__init__(my_peer, endpoint, network)
        self.settings = TunnelSettings()
        self.settings.become_exitnode = True
        print self.settings.become_exitnode

    def started(self):
        def print_peers():
            print "I am:", self.my_peer, "\nI know:", [str(p) for p in self.get_peers()]
            print self.settings.become_exitnode
            print "relay_session_keys", self.relay_session_keys
            for p in self.get_peers():
                print("any node", [c.peer.address for c in self.circuits.values()], "exit node",
                  [c.address for c in self.exit_candidates.values()])
        # We register a Twisted task with this overlay.
        # This makes sure that the task ends when this overlay is unloaded.
        # We call the 'print_peers' function every 5.0 seconds, starting now.
        self.register_task("print_peers", LoopingCall(print_peers)).start(5.0, True).addErrback(log.err)


_COMMUNITIES['MyCommunity'] = MyCommunity

for i in [2]:
    configuration = get_default_configuration()
    configuration['keys'] = [{
        'alias': "my peer",
        'generation': u"curve25519",
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
        'on_start': [('started',)]
    }]
    IPv8(configuration)

reactor.run()
