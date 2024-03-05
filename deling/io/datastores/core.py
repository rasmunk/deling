import os
import fs
from abc import abstractmethod
from fs.errors import ResourceNotFound
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
from deling.clients.ssh import SSHClient, CHANNEL_TYPE_SFTP
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
    def disconnect(self):
        raise NotImplementedError

    @abstractmethod
    def open(self, path, flag="r"):
        raise NotImplementedError

    @abstractmethod
    def exists(self, path):
        raise NotImplementedError

    @abstractmethod
    def listdir(self, path):
        raise NotImplementedError

    @abstractmethod
    def mkdir(self, path, mode=755, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def rmdir(self, path):
        raise NotImplementedError

    @abstractmethod
    def remove(self, path):
        raise NotImplementedError

    @abstractmethod
    def stat(self, path):
        raise NotImplementedError

    @abstractmethod
    def setstat(self, path, attributes):
        raise NotImplementedError

    @abstractmethod
    def close(self):
        raise NotImplementedError


class SSHFSStore(DataStore):
    def __init__(self, host=None, username=None, password=None, port="22", path="."):
        if isinstance(port, int):
            port = str(port)
        client = fs.open_fs(
            "ssh://" + username + ":" + password + "@" + host + ":" + port + "/" + path
        )
        self._is_connected = True
        super(SSHFSStore, self).__init__(client)

    def __del__(self):
        self.disconnect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def disconnect(self):
        self._client.session.disconnect()
        self._is_connected = False

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
    def __init__(self, host, port, authenticator, authenticator_prepare_kwargs=None):
        if not authenticator_prepare_kwargs:
            authenticator_prepare_kwargs = {}

        if not authenticator.is_prepared and not authenticator.prepare(
            host, port=port, **authenticator_prepare_kwargs
        ):
            raise ValueError("Authenticator could not be prepared")

        self.ssh_client = SSHClient(host, authenticator, port=port)
        connected = self.ssh_client.connect()
        if not connected:
            raise ConnectionError("Could not connect to the server")

        channel_opened = self.ssh_client.open_channel(channel_type=CHANNEL_TYPE_SFTP)
        if not channel_opened:
            raise ConnectionError("Could not open an SFTP channel")

        sftp_channel = self.ssh_client.get_channel(CHANNEL_TYPE_SFTP)
        super(SFTPStore, self).__init__(client=sftp_channel)

    def __del__(self):
        self.disconnect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def is_connected(self):
        return self.ssh_client.is_socket_connected()

    def disconnect(self):
        if self._client:
            self._client.session.disconnect()
        if self.ssh_client:
            self.ssh_client.disconnect()

    def open(self, path, flag="r"):
        """
        :param path: path to file on the sftp end
        :param flag: open mode, either 'r'=read, 'w'=write, 'a'=append
        'rb'=read binary, 'wb'=write binary or 'ab'= append binary
        :return: SFTPHandle, https://github.com/ParallelSSH/ssh2-python
        /blob/master/ssh2/sftp_handle.pyx
        """
        if flag == "r" or flag == "rb":
            r_flags = LIBSSH2_FXF_READ
            mode = LIBSSH2_SFTP_S_IWUSR
            fh = self._client.open(path, r_flags, mode)
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

    def _opendir(self, path):
        """
        :param path: path to directory on the sftp end
        :return: SFTPHandle,
        """
        return self._client.opendir(path)

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

    def listdir(self, path=None):
        """
        :param path: path to the directory which content should be listed
        :return: list of str, of items in the path directory
        """
        if not path:
            # If no path is provided, list the current directory
            path = "."
        else:
            # If the path is not the current directory and does not start with a slash
            # Discover the absolute path since self._opendir does not support relative paths
            if path[0] != os.sep:
                path = self.realpath(path)

        with self._opendir(path) as fh:
            return [name.decode("utf-8") for size, name, attrs in fh.readdir()]

    def touch(self, path):
        """
        :param path:
        path to the file that should be created
        :return:
        """
        with self.open(path, "a") as fh:
            fh.write("")

    def mkdir(self, path, mode=0o755, recursive=False, **kwargs):
        """
        :param path: path to the directory that should be created
        :return: Boolean
        """
        split_path = path.split(os.sep) if recursive else [path]

        if split_path[0] == "":
            split_path[0] = os.sep
        previous_dir = ""
        for path_part in split_path:
            current_path = os.path.join(previous_dir, path_part)
            if not self.exists(current_path):
                try:
                    self._client.mkdir(current_path, mode)
                except Exception:
                    error = self._client.last_error()
                    print(
                        "Failed to create path: {} - error_code: {}".format(
                            current_path, error
                        )
                    )
                    return False
            previous_dir = current_path
        return True

    def _rmdir(self, path):
        """
        :param path: path to the directory that should be removed
        """
        try:
            self._client.rmdir(path)
            return True
        except Exception:
            error = self._client.last_error()
            print("Failed to remove path: {} - error_code: {}".format(path, error))
            return False
        return False

    def rmdir(self, path, recursive=False):
        """
        :param path: path to the directory that should be removed
        :return: None
        """
        if not recursive:
            return self._rmdir(path)

        # TODO, update this to be able to recusively remove all
        # non specified files and directories as would be expected
        # from a recursive removal
        if os.sep in path:
            split_path = path.split(os.sep)
            new_path = os.sep.join(split_path[:-1])
            if not self._rmdir(path):
                return False
            return self.rmdir(new_path, recursive=True)
        else:
            return self.rmdir(path, recursive=False)

    def stat(self, path):
        """
        :param path: path to the file that should return it's stats
        """
        try:
            return self._client.stat(path)
        except Exception:
            return False

    def setstat(self, path, attributes):
        """
        :param path: path to the file that should have set their stat attributes
        :param attributes: SFTPAttributes that should be applied to the path file
        """
        try:
            self._client.setstat(path, attributes)
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

    def realpath(self, path):
        """
        :param path: The path that should be resolved
        """
        try:
            return self._client.realpath(path)
        except Exception:
            return False

    def rename(self, old_path, new_path):
        """
        :param old_path: The path that should be renamed
        :param new_path: The new path
        """
        try:
            self._client.rename(old_path, new_path)
            return True
        except Exception:
            return False

    def upload(self, local_path, remote_path, file_format="binary"):
        """
        :param local_path: The path to the local file
        :param remote_path: The path to the remote file
        """
        r_mode = "rb" if file_format == "binary" else "r"
        w_mode = "wb" if file_format == "binary" else "w"

        # TODO, add exception handling
        with open(local_path, r_mode) as fh:
            with self.open(remote_path, w_mode) as remote_fh:
                remote_fh.write(fh.read())
        return True

    def download(self, remote_path, local_path, file_format="binary"):
        """
        :param remote_path: The path to the remote file
        :param local_path: The path to the local file
        """

        r_mode = "rb" if file_format == "binary" else "r"
        w_mode = "wb" if file_format == "binary" else "w"

        # TODO, add exception handling
        with self.open(remote_path, r_mode) as fh:
            with open(local_path, w_mode) as local_fh:
                local_fh.write(fh.read())
        return True

    def copy(self, remote_src, remote_dest):
        """
        :param remote_src: The path to the remote source file
        :param remote_dest: The path to the remote destination file
        """
        # TODO, add exception handling
        with self.open(remote_src, "rb") as src:
            with self.open(remote_dest, "wb") as dest:
                dest.write(src.read())
        return True
