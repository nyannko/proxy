import socket
import struct
import threading
import logging
import select

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(thread)d %(funcName)s %(message)s')


class Client(object):

    def __init__(self):
        self.HOST = "127.0.0.1"
        self.PORT = 40000

    def create_srv_socket(self):
        socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        logging.info("Local client(socks5_twisted server for browser) listening at: {}:{}".format(self.HOST, self.PORT))
        socket_server.bind((self.HOST, self.PORT))
        socket_server.listen(5)
        return socket_server

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
                self.handle_socks(sock)
        except Exception as e:
            print e
            logging.error(e)
        finally:
            sock.close()

    def handle_socks(self, sock):
        # Handshake phase
        sock.recv(256)
        sock.send(b"\x05\x00")

        # Establish connection
        data = sock.recv(4)
        mode = struct.unpack(">B", data[1])[0]
        if mode != 1:
            logging.warn("Not a TCP connection")
            return

        addr_type = struct.unpack('>B', data[3])[0]
        addr_to_send = b"" + data[3]
        address, fqdn = "", ""
        if addr_type == 1:
            address = sock.recv(4)
            address = struct.unpack(">H", address)
            addr_to_send += address

        if addr_type == 3:
            length = struct.unpack(">B", sock.recv(1))[0]
            fqdn = sock.recv(length)
            addr_to_send += struct.pack('>B', length) + fqdn

        if addr_type == 4:
            address = sock.recv(16)

        port = sock.recv(2)
        port_number, = struct.unpack(">H", port)
        addr_to_send += port

        logging.debug("Handle request from client: " + \
                      "Address type: {}, address: {}, fqdn: {}, port number: {}" \
                      .format(addr_type, address, fqdn, port_number))

        logging.debug(addr_to_send)

        # send reply
        reply = b"\x05\x00\x00\x01"
        reply += socket.inet_aton('0.0.0.0') + struct.pack('>H', self.PORT)
        sock.send(reply)

        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # turn off Nagling

        remote.connect(('127.0.0.1', 50000))
        remote.send(addr_to_send)
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


def test_client():
    client = Client()
    socket_server = client.create_srv_socket()
    for i in range(10):
        threading.Thread(target=client.start_socks5_server, args=(socket_server,)).start()


if __name__ == "__main__":
    test_client()
