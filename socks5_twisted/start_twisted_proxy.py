from twisted.internet import reactor

from socks5 import Socks5Factory
from remote import RemoteFactory

import logging

logging.basicConfig(level=logging.DEBUG)


def start_proxy():
    reactor.listenTCP(40000, Socks5Factory())
    reactor.listenTCP(50000, RemoteFactory())
    logging.debug("socks5_twisted server listening at port 40000")
    logging.debug("remote server listening at port 50000")
    reactor.run()


if __name__ == '__main__':
    """ Start a pair of proxies"""
    start_proxy()
