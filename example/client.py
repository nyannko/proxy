from twisted.internet.protocol import Protocol, Factory
from twisted.internet.endpoints import clientFromString, serverFromString
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

queue = []
putter = None

class PutLine1(LineReceiver):
    def __init__(self):
        global putter
        putter = self
        print 'putline init called %s' % str(self)

    def have_data(self):
        line = queue.pop()
        self.sendLine(line)

class GetLine1(LineReceiver):
    delimiter = '\n'

    def lineReceived(self, line):
        queue.append(line)
        putter.have_data()
        self.sendLine(line)

class PutLine2(LineReceiver):
    def __init__(self):
        global putter
        putter = self
        print 'putline init called %s' % str(self)

    def have_data(self):
        line = queue.pop()
        self.sendLine(line)

class GetLine2(LineReceiver):
    delimiter = '\n'

    def lineReceived(self, line):
        queue.append(line)
        putter.have_data()
        self.sendLine(line)


def main():
    f = Factory()
    f.protocol = PutLine1
    endpoint = clientFromString(reactor, "socks5_tcp:host=localhost:port=9000")
    endpoint.connect(f)
    f = Factory()
    f.protocol = GetLine1
    endpoint2 = serverFromString(reactor, "socks5_tcp:port=9001")
    endpoint2.listen(f)

    f = Factory()
    f.protocol = PutLine2
    endpoint3 = clientFromString(reactor, "socks5_tcp:host=localhost:port=9002")
    endpoint3.connect(f)
    f = Factory()
    f.protocol = GetLine2
    endpoint4 = serverFromString(reactor, "socks5_tcp:port=9003")
    endpoint4.listen(f)

    reactor.run()

if __name__ == '__main__':
    main()