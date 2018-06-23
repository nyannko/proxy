from twisted.internet import reactor

from server import server
from client import client

def start_proxy():
    server()
    client()
    reactor.run()

if __name__ == '__main__':
    start_proxy()
