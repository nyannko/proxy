import socket
import struct
import select
import threading
import logging

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(thread)d %(funcName)s %(message)s')

class MyServer(object):

    def __init__(self):
        self.HOST = "127.0.0.1"
        self.PORT = 50000

    def create_srv_server(self):
        socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socketServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socketServer.bind((self.HOST, self.PORT))
        logging.info("Local client(socks5 server for browser) listening at: {}:{}".format(self.HOST, self.PORT))
        socketServer.listen(5)
        return socketServer

    def start_socks5_server(self, socketServer):
        try:
            while True:
                sock, addr = socketServer.accept()
                logging.info("Receive connection from {}".format(addr))
                self.handle_conversation(sock, addr)
        except socket.error as e:
            logging.error(e)
        except KeyboardInterrupt:
            socketServer.close()

    def handle_conversation(self, sock, addr):
        try:
            while True:
                self.handle_con(sock)
        except Exception as e:
            logging.error(e)
        finally:
            sock.close()

    def handle_con(self, sock):

        addrtype = ord(sock.recv(1))  # receive addr type
        addr = ''
        if addrtype == 1:
            pass
        elif addrtype == 3:
            len = ord(sock.recv(1))  # read 1 byte of len, then get 'len' bytes name
            addr = sock.recv(len)
        else:
            logging.warn('addr_type not support')
            return
        port, = struct.unpack('>H', sock.recv(2))

        logging.info("connect to {}:{}".format(addr, port))
        remote = socket.create_connection((addr, port))

        self.handle_tcp(sock, remote)

    def handle_tcp(self, sock, remote):
        try:
            fdset = [sock, remote]
            while True:
                r, w, e = select.select(fdset, [], [])  # use select I/O multiplexing model
                if sock in r:  # if local socket is ready for reading
                    data = sock.recv(4096)
                    if len(data) <= 0:  # received all data
                        break
                    result = remote.sendall(data)  # send data after encrypting
                    if result is not None:
                        raise Exception('failed to send all data')

                if remote in r:  # remote socket(proxy) ready for reading
                    data = remote.recv(4096)
                    if len(data) <= 0:
                        break
                    result = sock.sendall(data)  # send to local socket(application)
                    if result is not None:
                        raise Exception('failed to send all data')
        finally:
            sock.close()
            remote.close()


if __name__ == '__main__':
    server = MyServer()
    socketServer = server.create_srv_server()
    for i in range(10):
        threading.Thread(target=server.start_socks5_server, args=(socketServer,)).start()
    # server.start_socks5_server(socketServer)
