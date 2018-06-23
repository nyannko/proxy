from tcp_client import test_client
from tcp_server import test_server

import logging

logging.basicConfig(level=logging.DEBUG)


def start_proxy():
    test_client()
    test_server()


if __name__ == '__main__':
    """ Start a pair of proxies"""
    start_proxy()