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
from ssh2.utils import handle_error_codes
from enum import Enum


CHANNEL_TYPE_SESSION = "session"
CHANNEL_TYPE_SFTP = "sftp"
CHANNEL_TYPES = [CHANNEL_TYPE_SESSION, CHANNEL_TYPE_SFTP]


class SSHClientResultCode(Enum):

    SUCCESS = 0
    STDERR_RESPONSE = 1
    CONNECTION_ERROR = 10
    CHANNEL_OPEN_ERROR = 11
    CHANNEL_EXECUTE_ERROR = 12
    CHANNEL_READ_ERROR = 13
    UNKNOWN_ERROR = 99

    def is_success(self):
        return self.value == SSHClientResultCode.SUCCESS

    def is_stderr_response(self):
        return self.value == SSHClientResultCode.STDERR_RESPONSE

    def is_error(self):
        return not self.is_success()


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
        self.disconnect()

    def __enter__(self):
        return self

    def __exit__(self, execution_type, execption_value, traceback):
        self.disconnect()

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
        if not self.is_session_connected():
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
            return None
        if channel_type == CHANNEL_TYPE_SESSION:
            return self.channel
        if channel_type == CHANNEL_TYPE_SFTP:
            return self.sftp_channel
        return None

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
        if not self.is_socket_connected() and not self._connect_socket():
            return False

        if not self.is_session_connected() and not self._connect_session():
            return False

        if not self._authenticate():
            return False
        return True

    def disconnect(self):
        self.close_channel(CHANNEL_TYPE_SESSION)
        self.close_channel(CHANNEL_TYPE_SFTP)
        if self.is_session_connected():
            self._close_session()
        if self.is_socket_connected():
            self._close_socket()

    def exec_command(self, command, channel=None):
        if not channel:
            if not self.open_channel():
                return (
                    SSHClientResultCode.CHANNEL_OPEN_ERROR,
                    {
                        "output": f"Failed to open a channel to execute the command: {command}",
                    }
                )
            channel = self.get_channel()

        channel_return_code = handle_error_codes(channel.execute(command))
        if channel_return_code != 0:
            # An unkown error occurred
            return_dict["channel_error_code"] = channel_return_code
            return_dict["output"] = f"An unknown error code was returned from executing the command: {command}"
            return (
                SSHClientResultCode.CHANNEL_EXECUTE_ERROR,
                return_dict
            )

        stderr_success, stderr_response = read_channel_response_stderr(channel)
        exit_code = read_channel_exit_status(channel)
        return_dict = {
            "exit_code": exit_code
        }
        if not stderr_success:
            return_dict["output"] = f"Failed to read the channel stderr of the command: {command}",
            return (
                SSHClientResultCode.CHANNEL_READ_ERROR,
                return_dict
            )

        if stderr_response:
            return_dict["output"] = stderr_response
            return SSHClientResultCode.STDERR_RESPONSE, return_dict

        stdout_success, stdout_response = read_channel_response_stdout(channel)
        if not stdout_success:
            return_dict["output"] = f"Failed to read the channel stdout of the command: {command}",
            return (
                SSHClientResultCode.CHANNEL_READ_ERROR, return_dict
            )

        return_dict["output"] = stdout_response
        return SSHClientResultCode.SUCCESS, return_dict

    def run_single_command(self, command):
        with self as _client:
            if not _client.connect():
                return (
                    SSHClientResultCode.CONNECTION_ERROR,
                    {
                        "output": f"Failed to run command: {command}, not connected to: {self.host}:{self.port}",
                    }
                )

            if not _client.open_channel():
                return (
                    SSHClientResultCode.CHANNEL_OPEN_ERROR,
                    {
                        "output": f"Failed to run command: {command}, no open channel available",
                    }
                )

            channel = _client.get_channel()
            return _client.exec_command(command, channel=channel)
        return (
            SSHClientResultCode.UNKNOWN_ERROR,
            {
                "output": f"Failed to run command: {command}, unknown error happend during the connection phase",
            }
        )

    def run_multiple_commands(self, commands):
        responses = []
        with self as _client:
            if not _client.connect():
                return (
                    SSHClientResultCode.CONNECTION_ERROR,
                    {
                        "output": f"Failed to run commands: {commands}, not connected to: {self.host}:{self.port}"
                    }
                )
            for command in commands:
                if not _client.open_channel():
                    responses.append(
                        (
                            SSHClientResultCode.CHANNEL_OPEN_ERROR,
                            {
                                "output": f"Failed to run command: {command}, could not open a channel"
                            }
                        )
                    )
                else:
                    channel = _client.get_channel()
                    responses.append(_client.exec_command(command, channel=channel))
                    _client.close_channel()
        return responses


def read_channel_response_stdout(channel):
    response = ""
    size, data = channel.read()
    while size > 0:
        response_str = decode_bytes_to_string(data)
        if not response_str:
            return False, ""
        response += response_str
        size, data = channel.read(size)
    return True, response


def read_channel_response_stderr(channel):
    response = ""
    size, data = channel.read_stderr()
    while size > 0:
        response_str = decode_bytes_to_string(data)
        if not response_str:
            return False, ""
        response += response_str
        size, data = channel.read_stderr(size)
    return True, response


def read_channel_exit_status(channel):
    return channel.get_exit_status()


def decode_bytes_to_string(bytes_data):
    try:
        decoded_data = bytes_data.decode("utf-8")
        return decoded_data
    except UnicodeDecodeError:
        return False
    return False
