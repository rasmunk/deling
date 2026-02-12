# Copyright (C) 2024  rasmunk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import socket
from ssh2.session import Session


CHANNEL_TYPE_SESSION = "session"
CHANNEL_TYPE_SFTP = "sftp"
CHANNEL_TYPES = [CHANNEL_TYPE_SESSION, CHANNEL_TYPE_SFTP]


class SSHClient:
    def __init__(self, host, authenticator, port=22, proxy=None):
        self.host = host
        self.authenticator = authenticator
        if isinstance(port, str):
            self.port = int(port)
        else:
            self.port = port
        self.proxy = proxy

        self.socket = None
        self.session = None
        self.channel = None
        self.sftp_channel = None
        self._is_session_connected = False

    def __del__(self):
        self._close_session()

    def __enter__(self):
        return self

    def __exit__(self, execution_type, execption_value, traceback):
        self._close_session()

    def is_socket_connected(self):
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
        except Exception:
            return False
        return False

    def _connect_socket(self):
        if self._init_socket() and not self.socket:
            return False
        try:
            connect_code = self.socket.connect_ex((self.host, self.port))
            if connect_code == 0:
                return True
        except Exception:
            return False
        return False

    def _close_socket(self):
        if self.socket:
            self.socket.close()
            self.socket = None

    def is_session_connected(self):
        if not self.session:
            return False
        return self._is_session_connected

    def _init_session(self):
        if self.session:
            return False
        self.session = Session()
        return True

    def _connect_session(self):
        if not self.is_socket_connected():
            return False
        if not self.session and not self._init_session():
            return False
        try:
            self.session.handshake(self.socket)
            self._is_session_connected = True
        except Exception:
            self._is_session_connected = False
        return self.is_session_connected()

    def _close_session(self):
        if self.session:
            self.session.disconnect()
            self.session = None
        self._is_session_connected = False

    def open_channel(self, channel_type=CHANNEL_TYPE_SESSION):
        if channel_type not in CHANNEL_TYPES:
            return False
        if not self.session:
            return False
        try:
            if channel_type == CHANNEL_TYPE_SESSION:
                self.channel = self.session.open_session()
            elif channel_type == CHANNEL_TYPE_SFTP:
                self.sftp_channel = self.session.sftp_init()
            else:
                return False
        except Exception:
            return False
        return True

    def get_channel(self, channel_type=CHANNEL_TYPE_SESSION):
        if channel_type not in CHANNEL_TYPES:
            return False
        if channel_type == CHANNEL_TYPE_SESSION:
            return self.channel
        if channel_type == CHANNEL_TYPE_SFTP:
            return self.sftp_channel
        return False

    def close_channel(self, channel_type=CHANNEL_TYPE_SESSION):
        if channel_type not in CHANNEL_TYPES:
            return False
        if channel_type == CHANNEL_TYPE_SESSION:
            if self.channel:
                self.channel.close()
                self.channel.wait_closed()
                self.channel = None
        if channel_type == CHANNEL_TYPE_SFTP:
            self.sftp_channel = None

    def _authenticate(self):
        if not self.authenticator:
            return False
        if not self.session:
            return False
        return self.authenticator.authenticate(self.session)

    def connect(self):
        if not self._connect_socket():
            return False
        if not self.is_socket_connected():
            return False
        if not self._connect_session():
            return False
        if not self.is_session_connected():
            return False
        if not self._authenticate():
            return False
        return True

    def disconnect(self):
        self.close_channel(CHANNEL_TYPE_SESSION)
        self.close_channel(CHANNEL_TYPE_SFTP)
        self._close_session()
        if self.is_socket_connected():
            self._close_socket()

    def exec_command(self, command):
        if not self.is_session_connected():
            return False, ""
        channel = self.get_channel()
        if not channel:
            return False, ""

        return_code = channel.execute(command)
        if return_code != 0:
            return False, ""

        return read_channel_response(channel)


def read_channel_response(channel):
    response = ""
    size, data = channel.read()
    while size > 0:
        try:
            decoded_data = data.decode("utf-8")
            response += decoded_data
        except UnicodeDecodeError:
            return False, ""
        size, data = channel.read(size)
    return True, response
