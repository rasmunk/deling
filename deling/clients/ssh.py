import socket
from ssh2.session import Session


class SSHClient(object):
    def __init__(self, host, authenticator, port=22, proxy=None):
        self.host = host
        self.authenticator = authenticator
        self.port = port
        self.proxy = proxy

        self.socket = None
        self.session = None
        self.channel = None

    def __del__(self):
        self.disconnect()

    def is_connected(self):
        if not self.socket:
            return False
        error_code = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if error_code == 0:
            return True
        return False

    def _init_socket(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            return True
        except Exception as e:
            print("Failed to setup socket: {}".format(e))
        return False

    def _connect_socket(self):
        if not self.socket and self._init_socket():
            return False
        try:
            connect_code = self.socket.connect_ex((self.host, self.port))
            if connect_code == 0:
                return True
        except Exception as e:
            print("Failed to connect to {}: {}".format(self.host, e))
            return False
        return False

    def _close_socket(self):
        if self.socket:
            self.socket.close()
            self.socket = None

    def _init_session(self):
        if self.session:
            return False
        self.session = Session()
        return True

    def _connect_session(self):
        if not self.is_connected():
            return False
        if not self.session and not self._init_session():
            return False
        try:
            self.session.handshake(self.socket)
        except Exception as e:
            print("Failed to open session: {}".format(e))
            return False
        return True

    def _close_session(self):
        if self.session:
            self.session.disconnect()
            self.session = None

    def open_channel(self):
        if not self.session:
            return False
        try:
            self.channel = self.session.open_session()
        except Exception as e:
            print("Failed to open channel: {}".format(e))
            return False
        return None

    def close_channel(self):
        if self.channel:
            self.channel.close()
            self.channel.wait_closed()
            self.channel = None

    def connect(self):
        print("Connecting to {} on port {}".format(self.host, self.port))
        if not self.is_connected() and not self._connect_socket():
            return False
        if not self._connect_session():
            return False
        if not self.open_channel():
            return False
        return True

    def open_tunnel(self, host, port):
        print("Opening tunnel to {} on port {}".format(host, port))

    def close_tunnel(self):
        print("Closing tunnel")

    def disconnect(self):
        self.close_tunnel()
        self.close_channel()
        self._close_session()
        if self.is_connected():
            self._close_socket()
