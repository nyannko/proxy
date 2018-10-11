from pyipv8.ipv8.attestation.trustchain.listener import BlockListener


class TestBlock(object):
    pass


class ProxyBlockListener(BlockListener):

    BLOCK_CLASS = TestBlock

    def should_sign(self, block):
        return True

    def received_block(self, block):
        pass
