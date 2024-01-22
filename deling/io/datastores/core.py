import fs
import socket
from abc import abstractmethod
from fs.errors import ResourceNotFound
from ssh2.session import Session
from ssh2.exceptions import SFTPProtocolError
from ssh2.sftp import (
    LIBSSH2_FXF_READ,
    LIBSSH2_FXF_WRITE,
    LIBSSH2_FXF_CREAT,
    LIBSSH2_SFTP_S_IRUSR,
    LIBSSH2_SFTP_S_IWUSR,
    LIBSSH2_SFTP_S_IRGRP,
    LIBSSH2_SFTP_S_IROTH,
    LIBSSH2_FXF_APPEND,
)
from deling.io.datastores.file import SFTPFileHandle


class DataStore:
    _client = None

    def __init__(self, client):
        """
        :param client:
        This is the sshfs client instance,
        that is used to access the datastore
        """
        self._client = client

    @abstractmethod
    def open(self, path, flag="r"):
        pass

    @abstractmethod
    def exists(self, path):
        pass

    @abstractmethod
    def listdir(self, path):
        pass

    @abstractmethod
    def mkdir(self, path, mode=755, **kwargs):
        pass

    @abstractmethod
    def rmdir(self, path):
        pass

    @abstractmethod
    def remove(self, path):
        pass

    @abstractmethod
    def close(self):
        pass


class SSHFSStore(DataStore):
    def __init__(self, host=None, username=None, password=None, port="22", path="."):
        if isinstance(port, int):
            port = str(port)
        client = fs.open_fs(
            "ssh://" + username + ":" + password + "@" + host + ":" + port + "/" + path
        )
        super(SSHFSStore, self).__init__(client)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def geturl(self, path):
        return self._client.geturl(path)

    def open(self, path, flag="r"):
        """
        Used to get a python filehandler object
        :param path:
        the name of the file to be opened
        :param flag:
        which mode should the file be opened in
        :return:
        a _io.TextIOWrapper object with utf-8 encoding
        """

        if "b" in flag:
            return self._openbin(path, flag)
        return self._client.open(path, flag)

    def _openbin(self, path, flag="rb"):
        return self._client.openbin(path, flag)

    def close(self):
        self._client.close()

    def exists(self, path):
        """
        :param path: the path we are checking whether it exists
        :return: Boolean
        """
        return self._client.exists(path)

    def listdir(self, path="."):
        """
        :param path:
        file system path which items will be returned
        :return:
        A list of items in the path.
        There is no distinction between files and dirs
        """
        return self._client.listdir(path)

    def touch(self, path):
        """
        :param path:
        path to the file that should be created
        :return:
        """
        with self.open(path, "a") as fh:
            fh.write("")

    def read(self, path, datatype=str):
        """
        :param file:
        File to be read
        :return:
        a string of the content within file
        """
        if datatype != str and datatype != bytes and datatype != bytearray:
            raise ValueError(
                "datatype must be either str, bytes or bytearray, is: {}".format(
                    datatype
                )
            )

        if datatype == bytes or datatype == bytearray:
            with self.open(path, "rb") as _file:
                return _file.read()

        if datatype == str:
            with self.open(path, "r") as _file:
                return _file.read()
        return False

    def write(self, path, data):
        """
        :param path:
        path to the file being written
        :param data: data to being written
        :param flag: write flag, defaults to append
        :return:
        """
        if isinstance(data, (bytes, bytearray)):
            with self.open(path, "wb") as fh:
                fh.write(data)
            return True
        if isinstance(data, (int, float)):
            with self.open(path, "w") as fh:
                fh.write(str(data))
            return True

        with self.open(path, "w") as fh:
            fh.write(data)
            return True
        return False

    def append(self, path, data):
        """
        :param path:
        path to the file being written
        :param data: data to being written
        :return:
        """
        if isinstance(data, (bytes, bytearray)):
            with self.open(path, "ab") as fh:
                fh.write(data)
            return True

        if isinstance(data, (int, float)):
            with self.open(path, "a") as fh:
                fh.write(str(data))
            return True

        with self.open(path, "a") as fh:
            fh.write(data)
            return True

    def remove(self, path):
        """
        :param path:
        path to the file that should be removed
        :return:
        Bool, whether a file was removed or not
        """
        try:
            self._client.remove(path)
            return True
        except ResourceNotFound:
            return False

    def rmdir(self, path):
        """
        :param path:
        path to the dir that should be removed
        :return:
        Bool, whether a dir was removed or not
        """
        try:
            self._client.removedir(path)
            return True
        except ResourceNotFound:
            return False

    def mkdir(self, path):
        """
        :param path: path to the directory that should be created
        """
        try:
            self._client.makedir(path)
            return True
        except ResourceNotFound:
            return False

    def info(self, path):
        """
        :param path:
        directory path to be listed
        :return:
        A list of .SFTPAttributes objects
        """
        return self._client.getinfo(path, namespaces=["lstat"])


class SFTPStore(DataStore):
    def __init__(self, host, port, authenticator):
        if isinstance(port, str):
            port = int(port)
        if not authenticator.is_prepared and not authenticator.prepare(host):
            raise ValueError("Authenticator could not be prepared")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        s = Session()
        s.handshake(sock)
        # Use private key authentication if a private key is provided
        if authenticator.credentials.private_key:
            s.userauth_publickey_frommemory(
                authenticator.credentials.username,
                authenticator.credentials.private_key,
                authenticator.credentials.password,
            )
        elif authenticator.credentials.private_key_file:
            s.userauth_publickey_fromfile(
                authenticator.credentials.username,
                authenticator.credentials.private_key_file,
                authenticator.credentials.password,
            )
        elif authenticator.credentials.password:
            s.userauth_password(
                authenticator.credentials.username, authenticator.credentials.password
            )
        else:
            raise ValueError("No authentication method provided")

        s.open_session()
        client = s.sftp_init()
        super(SFTPStore, self).__init__(client=client)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self, path, flag="r"):
        """
        :param path: path to file on the sftp end
        :param flag: open mode, either 'r'=read, 'w'=write, 'a'=append
        'rb'=read binary, 'wb'=write binary or 'ab'= append binary
        :return: SFTPHandle, https://github.com/ParallelSSH/ssh2-python
        /blob/master/ssh2/sftp_handle.pyx
        """
        if flag == "r" or flag == "rb":
            fh = self._client.open(path, LIBSSH2_FXF_READ, LIBSSH2_SFTP_S_IWUSR)
        else:
            w_flags = None
            if flag == "w" or flag == "wb":
                w_flags = LIBSSH2_FXF_CREAT | LIBSSH2_FXF_WRITE
            elif flag == "a" or flag == "ab":
                w_flags = LIBSSH2_FXF_CREAT | LIBSSH2_FXF_WRITE | LIBSSH2_FXF_APPEND
            mode = (
                LIBSSH2_SFTP_S_IRUSR
                | LIBSSH2_SFTP_S_IWUSR
                | LIBSSH2_SFTP_S_IRGRP
                | LIBSSH2_SFTP_S_IROTH
            )
            fh = self._client.open(path, w_flags, mode)
        return SFTPFileHandle(fh, path, flag)

    def close(self):
        self._client.close()

    def read(self, path, datatype=str):
        """
        :param path: path to file on the sftp end
        :return: the content of path, decoded to utf-8 string
        """

        if datatype != str and datatype != bytes and datatype != bytearray:
            raise ValueError(
                "datatype must be either str, bytes or bytearray, is: {}".format(
                    datatype
                )
            )

        if datatype == bytes or datatype == bytearray:
            with self.open(path, "rb") as _file:
                return _file.read()

        if datatype == str:
            with self.open(path, "r") as _file:
                return _file.read()
        return False

    def write(self, path, data):
        """
        :param path: path to the file that should be created/written to
        :param data: data that should be written to the file, expects binary or str
        :param flag: write mode
        :return: None
        """
        if isinstance(data, (bytes, bytearray)):
            with self.open(path, "wb") as fh:
                fh.write(data)
            return True

        if isinstance(data, (int, float)):
            with self.open(path, "w") as fh:
                fh.write(str(data))
            return True

        with self.open(path, "w") as fh:
            fh.write(data)
            return True

    def append(self, path, data):
        """
        :param path: path to the file that should be created/written to
        :param data: data that should be written to the file, expects binary or str
        :param flag: write mode
        :return: None
        """
        if isinstance(data, (bytes, bytearray)):
            with self.open(path, "ab") as fh:
                fh.write(data)
            return True

        if isinstance(data, (int, float)):
            with self.open(path, "a") as fh:
                fh.write(str(data))
            return True

        with self.open(path, "a") as fh:
            fh.write(data)
            return True

    def exists(self, path):
        """
        :param path: the path we are checking whether it exists
        :return: Boolean
        """
        # There is no direct way to check if it exists
        # See if we can stat the designated path instead
        try:
            self._client.stat(path)
            return True
        except SFTPProtocolError:
            return False
        return False

    def listdir(self, path="."):
        """
        :param path: path to the directory which content should be listed
        :return: list of str, of items in the path directory
        """
        with self._client.opendir(path) as fh:
            return [name.decode("utf-8") for size, name, attrs in fh.readdir()]

    def touch(self, path):
        """
        :param path:
        path to the file that should be created
        :return:
        """
        with self.open(path, "a") as fh:
            fh.write("")

    def mkdir(self, path, mode=755, **kwargs):
        """
        :param path: path to the directory that should be created
        :return: Boolean
        """
        try:
            self._client.mkdir(path, mode)
            return True
        except Exception:
            return False

    def rmdir(self, path):
        """
        :param path: path to the directory that should be removed
        :return: None
        """
        try:
            self._client.rmdir(path)
            return True
        except Exception:
            return False

    def remove(self, path):
        """
        :param path: path to the file that should be removed
        """
        try:
            self._client.unlink(path)
            return True
        except Exception:
            return False