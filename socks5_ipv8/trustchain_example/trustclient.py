from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.python import log

from pyipv8.ipv8.attestation.trustchain.community import TrustChainCommunity

from pyipv8.ipv8.configuration import get_default_configuration
from pyipv8.ipv8.peer import Peer
from pyipv8.ipv8_service import _COMMUNITIES, IPv8
# from socks5_udp.trustchain_example.trustserver import TestBlockListener


class TrustClient(TrustChainCommunity):
    master_peer = Peer(
        "307e301006072a8648ce3d020106052b81040024036a000401142bae9f90e77434a6ddda16c9bc913a3440366b9eedc9e57a660789e10aa3f470c1f7ae769083a3494be79ad78165caed85da009a7e897bd51e531e9fd90465c038993d2bbe6646b592872cb432c818ce9fa6e3ae0382a76d39ef982fb85801279def1409a86a".decode(
            'HEX'))

    DB_NAME = 'trustchain_client'

    def __init__(self, my_peer, endpoint, network):
        super(TrustClient, self).__init__(my_peer, endpoint, network)
        # self.add_listener(TestBlockListener(), ['test'])
        self.count = 0
        self.his_key = ''
        self.my_key = self.my_peer.public_key.key_to_bin()
        self._balance = 0

    def started(self):
        def print_peers():
            print "I am:", self.my_peer, "\nI know:", [str(p) for p in self.get_peers()]
            for p in self.get_peers():
                self.his_node = p
                self.his_pubkey = p.public_key.key_to_bin()
                self.send_sign()
                self.check_db(self.count)
                self.count += 1

        self.register_task("print_peers", LoopingCall(print_peers)).start(5.0, True) \
            .addErrback(log.err)

    def check_db(self, count):
        print "persistence", count, self.persistence.get(self.his_key, count)
        # print "persistence", self.persistence._getall(u"", ())

    def send_sign(self):
        transaction = self.create_transaction()
        print transaction
        self.sign_block(self.his_node, public_key=self.his_pubkey, block_type='test', transaction=transaction)

    def create_transaction(self):
        debit = 0
        credit = 1
        self._balance += debit - credit
        bill = {'identity': 'client->', 'debit': debit, 'credit': credit, 'balance': self._balance}
        return bill


def trust_client():
    _COMMUNITIES['TrustClient'] = TrustClient

    for i in [4]:
        configuration = get_default_configuration()
        configuration['keys'] = [{
            'alias': "my peer",
            'generation': u"curve25519",
            'file': u"ec%d.pem" % i
        }]
        configuration['overlays'] = [{
            'class': 'TrustClient',
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
    trust_client()
    reactor.run()
