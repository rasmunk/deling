from abc import abstractmethod


class FileHandle:
    @abstractmethod
    def open(self):
        raise NotImplementedError

    @abstractmethod
    def close(self):
        raise NotImplementedError

    @abstractmethod
    def fsetstat(self, attributes):
        raise NotImplementedError

    @abstractmethod
    def fstat(self):
        raise NotImplementedError

    @abstractmethod
    def sync(self):
        raise NotImplementedError

    @abstractmethod
    def read(self):
        raise NotImplementedError

    @abstractmethod
    def write(self, data):
        raise NotImplementedError

    @abstractmethod
    def seek(self, data, whence=0):
        raise NotImplementedError


class SFTPFileHandle(FileHandle):
    def __init__(self, fh, name, flag):
        """
        :param fh: Expects a PySFTPHandle
        """
        self.fh = fh
        self.name = name
        self.flag = flag

    def __iter__(self):
        return self

    def __next__(self):
        return self.read()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """
        Close the passed PySFTPHandles
        :return: None
        """
        self.fh.close()

    def fsetstat(self, attributes):
        """
        Set file stat attributes on handle.
        :param attributes: ssh2.sftp.SFTPAttribute
        :return: None
        """
        try:
            result = self.fh.fsetstat(attributes)
            if result == 0:
                return True
        except Exception as e:
            print(f"feststat failed with error: {e}")
        return False

    def fstat(self):
        """
        Get file stat attributes from handle.
        :return: ssh2.sftp.SFTPAttribute
        """
        return self.fh.fstat()

    def sync(self):
        """
        Sync file handle to disk.
        :return: None
        """
        self.fh.sync()

    def read(self, n=-1, encoding="utf-8"):
        """
        :param n: amount of bytes to be read, defaults to the entire file
        :return: the content of path, decoded to utf-8 string
        """
        assert "r" in self.flag
        if "b" in self.flag:
            return self.read_binary(n)
        else:
            return self.read_binary(n).decode(encoding)

    def write(self, data, encoding="utf-8"):
        """
        :param path: path to the file that should be created/written to
        :param data: data that should be written to the file, expects binary or str
        :param flag: write mode
        :return: None
        """
        assert "w" in self.flag or "a" in self.flag
        if isinstance(data, str):
            data = bytes(data, encoding=encoding)
            return self.fh.write(data)
        if isinstance(data, bytearray):
            return self.fh.write(bytes(data))
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes before it can be written")
        return self.fh.write(data)

    def seek(self, offset, whence=0):
        """Seek file to a given offset
        :param offset: amount of bytes to skip
        :param whence: defaults to 0 which means absolute file positioning
                       other values are 1 which means seek relative to
                       the current position and 2 means seek relative to the file's end.
        :return: None
        """
        if whence == 0:
            self.fh.seek64(offset)
        if whence == 1:
            # Seek relative to the current position
            current_offset = self.fh.tell64()
            self.fh.seek(current_offset + offset)
        if whence == 2:
            file_stat = self.fh.fstat()
            # Seek relative to the file end
            self.fh.seek(file_stat.filesize + offset)

    def read_binary(self, n=-1):
        """
        :param n: amount of bytes to be read
        :return: a binary string of the content within in file
        """
        data = []
        if n != -1:
            # 1, because pysftphandle returns an array -> 1 = data
            data.append(self.fh.read(n)[1])
        else:
            for size, chunk in self.fh:
                data.append(chunk)
        return b"".join(data)

    def tell(self):
        """Get the current file handle offset
        :return: int
        """
        return self.fh.tell64()
