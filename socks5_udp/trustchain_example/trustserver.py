from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from pyipv8.ipv8.attestation.trustchain.block import TrustChainBlock
from pyipv8.ipv8.attestation.trustchain.community import TrustChainCommunity
from pyipv8.ipv8.attestation.trustchain.listener import BlockListener
from pyipv8.ipv8.configuration import get_default_configuration
from pyipv8.ipv8.peer import Peer
from pyipv8.ipv8_service import _COMMUNITIES, IPv8

from twisted.python import log


class DummyBlock(TrustChainBlock):
    """
    This dummy block is used to verify the conversion to a specific block class during the tests.
    Other than that, it has no purpose.
    """
    pass


class TestBlockListener(BlockListener):
    """
    This block listener simply signs all blocks it receives.
    """
    BLOCK_CLASS = DummyBlock

    def should_sign(self, block):
        return True

    def received_block(self, block):
        pass


class TrustServer(TrustChainCommunity):
    master_peer = Peer(
        "307e301006072a8648ce3d020106052b81040024036a000401142bae9f90e77434a6ddda16c9bc913a3440366b9eedc9e57a660789e10aa3f470c1f7ae769083a3494be79ad78165caed85da009a7e897bd51e531e9fd90465c038993d2bbe6646b592872cb432c818ce9fa6e3ae0382a76d39ef982fb85801279def1409a86a".decode(
            'HEX'))

    def __init__(self, my_peer, endpoint, network):
        super(TrustServer, self).__init__(my_peer, endpoint, network)
        # self.add_listener(TestBlockListener(), ['test'])
        # self.my_key = self.my_peer.public_key.key_to_bin()
        self.his_pubkey = ''
        self.count = 0
        self._balance = 0

    def started(self):
        def start_communication():
            for p in self.get_peers():
                print "New host {} join the network".format(p)
                self.my_key = self.my_peer.public_key.key_to_bin()
                self.his_node = p
                self.his_pubkey = p.public_key.key_to_bin()
                self.send_sign()
                self.check_db(self.count)

        self.register_task("start_communication", LoopingCall(start_communication)).start(5.0, True) \
            .addErrback(log.err)

    def send_sign(self):
        transaction = self.create_transaction()
        print transaction
        self.sign_block(self.his_node, public_key=self.his_pubkey, block_type='test', transaction=transaction)

    def create_transaction(self):
        debit = 1
        credit = 0
        self._balance += debit - credit
        bill = {'identity': 'server->', "debit": debit, "credit": credit, "balance": self._balance}
        return bill

    def check_db(self, count):
        print "from persistence", count, self.persistence.get(self.my_key, count)


def trust_server():
    _COMMUNITIES['TrustServer'] = TrustServer

    for i in [3]:
        configuration = get_default_configuration()
        configuration['keys'] = [{
            'alias': "my peer",
            'generation': u"curve25519",
            'file': u"ec%d.pem" % i
        }]
        configuration['overlays'] = [{
            'class': 'TrustServer',
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


if __name__ == '__main__':
    trust_server()
    reactor.run()
