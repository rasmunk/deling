import unittest
import os
import sys
import stat
import random
from ssh2.sftp import LIBSSH2_SFTP_ATTR_PERMISSIONS
from deling.authenticators.ssh import SSHAuthenticator
from deling.io.datastores.core import SFTPStore, SSHFSStore, SFTPFileHandle
from deling.io.datastores.erda import ERDASFTPShare
from deling.utils.io import hashsum, makedirs, exists, load
from utils import gen_random_file
from helpers import (
    make_container,
    wait_for_container_output,
    remove_container,
    wait_for_session,
)

IMAGE_OWNER = "ucphhpc"
IMAGE_NAME = "ssh-mount-dummy"
IMAGE_TAG = "latest"
IMAGE = "".join([IMAGE_OWNER, "/", IMAGE_NAME, ":", IMAGE_TAG])


class TestDataStoreCases:
    def setUp(self):
        self.seed = str(random.random())[2:10]

    def test_open_write(self):
        content = "sddsfeqwfiopqiodnqodniasd"
        write_file = "write_file_{}".format(self.seed)
        with self.share.open(write_file, "w") as w_file:
            w_file.write(content)

        with self.share.open(write_file, "r") as r_file:
            read_content = r_file.read()
            self.assertIsInstance(read_content, str)
            self.assertEqual(read_content, content)

        self.assertTrue(self.share.remove(write_file))
        self.assertNotIn(write_file, self.share.listdir())

    def test_open_write_bytes(self):
        content = b"sddsfeqwfiopqiodnqodniasd"
        write_file = "write_file_bytes_{}".format(self.seed)
        with self.share.open(write_file, "wb") as w_file:
            w_file.write(content)

        with self.share.open(write_file, "rb") as r_file:
            read_content = r_file.read()
            self.assertIsInstance(read_content, bytes)
            self.assertEqual(read_content, content)

        self.assertTrue(self.share.remove(write_file))
        self.assertNotIn(write_file, self.share.listdir())

    def test_open_write_bytearray(self):
        content = bytearray("sddsfeqwfiopqiodnqodniasd", "utf-8")
        write_file = "write_file_bytearray_{}".format(self.seed)
        with self.share.open(write_file, "wb") as w_file:
            w_file.write(content)

        with self.share.open(write_file, "rb") as r_file:
            read_content = r_file.read()
            self.assertIsInstance(read_content, bytes)
            self.assertEqual(bytearray(read_content), content)

        self.assertTrue(self.share.remove(write_file))
        self.assertNotIn(write_file, self.share.listdir())

    def test_open_write_int(self):
        content = 42342342
        write_file = "write_file_int_{}".format(self.seed)
        with self.share.open(write_file, "w") as w_file:
            w_file.write(str(content))

        with self.share.open(write_file, "r") as r_file:
            read_content = r_file.read()
            self.assertIsInstance(read_content, str)
            self.assertEqual(int(read_content), content)

        self.assertTrue(self.share.remove(write_file))
        self.assertNotIn(write_file, self.share.listdir())

    def test_open_write_float(self):
        content = 4234.234324
        write_file = "write_file_float_{}".format(self.seed)
        with self.share.open(write_file, "w") as w_file:
            w_file.write(str(content))

        with self.share.open(write_file, "r") as r_file:
            read_content = r_file.read()
            self.assertIsInstance(read_content, str)
            self.assertEqual(float(read_content), content)

        self.assertTrue(self.share.remove(write_file))
        self.assertNotIn(write_file, self.share.listdir())

    def test_directory(self):
        make_directory = "directory_{}".format(self.seed)
        self.assertTrue(self.share.mkdir(make_directory))
        self.assertIn(make_directory, self.share.listdir())
        self.assertTrue(self.share.rmdir(make_directory))
        self.assertNotIn(make_directory, self.share.listdir())

    def test_make_nested_directory(self):
        nested_directory_name = "nested"
        make_nested_directory = "nested_directory_{}".format(self.seed)
        nested_directory = os.path.join(make_nested_directory, nested_directory_name)
        self.assertTrue(self.share.mkdir(nested_directory, recursive=True))
        self.assertIn(make_nested_directory, self.share.listdir())
        self.assertIn(
            nested_directory_name, self.share.listdir(path=make_nested_directory)
        )
        self.assertTrue(self.share.rmdir(nested_directory))
        self.assertNotIn(
            nested_directory_name, self.share.listdir(path=make_nested_directory)
        )
        self.assertTrue(self.share.rmdir(make_nested_directory))
        self.assertNotIn(make_nested_directory, self.share.listdir())

    def test_make_absolute_nested_directory(self):
        first_directory_name = "nested_directory_{}".format(self.seed)
        second_directory_name = "nested"
        absolute_top_dir_path = os.path.join(os.sep, "tmp", "tests")
        make_first_directory = os.path.join(absolute_top_dir_path, first_directory_name)
        make_second_directory = os.path.join(
            make_first_directory, second_directory_name
        )

        self.assertTrue(self.share.mkdir(make_second_directory, recursive=True))
        self.assertIn(first_directory_name, self.share.listdir(absolute_top_dir_path))
        self.assertIn(second_directory_name, self.share.listdir(make_first_directory))
        self.assertTrue(self.share.rmdir(make_second_directory))
        self.assertNotIn(
            second_directory_name, self.share.listdir(make_first_directory)
        )
        self.assertTrue(self.share.rmdir(make_first_directory))
        self.assertNotIn(
            first_directory_name, self.share.listdir(absolute_top_dir_path)
        )

    def test_remove_recursive_directory(self):
        first_directory_name = "remove_nested_directory_{}".format(self.seed)
        second_directory_name = "nested"
        make_directory_path = os.path.join(first_directory_name, second_directory_name)
        self.assertTrue(self.share.mkdir(make_directory_path, recursive=True))
        self.assertIn(first_directory_name, self.share.listdir())
        self.assertIn(second_directory_name, self.share.listdir(first_directory_name))
        self.assertTrue(self.share.rmdir(make_directory_path, recursive=True))
        self.assertNotIn(first_directory_name, self.share.listdir())

    def test_directory_exists(self):
        make_directory = "make_directory_exists_{}".format(self.seed)
        self.assertTrue(self.share.mkdir(make_directory))
        self.assertTrue(self.share.exists(make_directory))
        self.assertTrue(self.share.rmdir(make_directory))
        self.assertFalse(self.share.exists(make_directory))

    def test_touch_file(self):
        touch_file = "touch_file_{}".format(self.seed)
        self.share.touch(touch_file)
        self.assertIn(touch_file, self.share.listdir())
        self.assertEqual(self.share.read(touch_file), "")
        self.assertTrue(self.share.remove(touch_file))
        self.assertNotIn(touch_file, self.share.listdir())

    def test_touch_file_exists(self):
        touch_file_existing = "touch_file_exists_{}".format(self.seed)
        self.assertFalse(self.share.exists(touch_file_existing))
        self.share.touch(touch_file_existing)
        self.assertTrue(self.share.exists(touch_file_existing))
        self.assertIn(touch_file_existing, self.share.listdir())

        self.assertTrue(self.share.remove(touch_file_existing))
        self.assertNotIn(touch_file_existing, self.share.listdir())
        self.assertFalse(self.share.exists(touch_file_existing))

    def test_touch_existing_file(self):
        touch_file_existing = "touch_file_existing_{}".format(self.seed)
        self.share.touch(touch_file_existing)
        self.assertIn(touch_file_existing, self.share.listdir())
        self.assertEqual(self.share.read(touch_file_existing), "")
        # TODO, get the timestamp for the file and compare it
        # after a new touch

        self.share.touch(touch_file_existing)
        self.assertIn(touch_file_existing, self.share.listdir())
        self.assertEqual(self.share.read(touch_file_existing), "")
        self.assertTrue(self.share.remove(touch_file_existing))
        self.assertNotIn(touch_file_existing, self.share.listdir())

    def test_make_file_with_content(self):
        content_file = "content_file_{}".format(self.seed)
        self.assertTrue(self.share.write(content_file, "sddsfsf"))
        self.assertIn(content_file, self.share.listdir())
        self.assertEqual(self.share.read(content_file), "sddsfsf")
        self.assertTrue(self.share.remove(content_file))
        self.assertNotIn(content_file, self.share.listdir())

    def test_overwrite_file(self):
        overwrite_file = "overwrite_file_{}".format(self.seed)
        self.assertTrue(self.share.write(overwrite_file, "sddsfsf"))
        self.assertIn(overwrite_file, self.share.listdir())
        self.assertEqual(self.share.read(overwrite_file), "sddsfsf")
        self.assertTrue(self.share.write(overwrite_file, "sddsfsf"))
        self.assertEqual(self.share.read(overwrite_file), "sddsfsf")
        self.assertTrue(self.share.remove(overwrite_file))
        self.assertNotIn(overwrite_file, self.share.listdir())

    def test_append_file(self):
        append_file = "append_file_{}".format(self.seed)
        self.assertTrue(self.share.write(append_file, "sddsfsf"))
        self.assertIn(append_file, self.share.listdir())
        self.assertEqual(self.share.read(append_file), "sddsfsf")
        self.assertTrue(self.share.append(append_file, "sddsfsf"))
        self.assertEqual(self.share.read(append_file), "sddsfsfsddsfsf")
        self.assertTrue(self.share.remove(append_file))
        self.assertNotIn(append_file, self.share.listdir())

    def test_write_string(self):
        content = "Hello There"
        write_file_string = "write_string_{}".format(self.seed)
        self.assertTrue(self.share.write(write_file_string, content))
        self.assertIn(write_file_string, self.share.listdir())
        self.assertEqual(self.share.read(write_file_string), content)
        self.assertTrue(self.share.remove(write_file_string))
        self.assertNotIn(write_file_string, self.share.listdir())

    def test_write_bytes(self):
        write_bytes_file = "write_bytes_{}".format(self.seed)
        content = b"Hello There"
        self.assertTrue(self.share.write(write_bytes_file, content))
        self.assertIn(write_bytes_file, self.share.listdir())
        self.assertEqual(self.share.read(write_bytes_file, datatype=bytes), content)
        self.assertTrue(self.share.remove(write_bytes_file))
        self.assertNotIn(write_bytes_file, self.share.listdir())

    def test_test_bytearray(self):
        write_bytearray_file = "write_bytearray_{}".format(self.seed)
        content = bytearray("Hello There", "utf-8")
        self.assertTrue(self.share.write(write_bytearray_file, content))
        self.assertIn(write_bytearray_file, self.share.listdir())
        self.assertEqual(
            self.share.read(write_bytearray_file, datatype=bytearray), content
        )
        self.assertTrue(self.share.remove(write_bytearray_file))
        self.assertNotIn(write_bytearray_file, self.share.listdir())

    def test_write_int(self):
        write_int_file = "write_int_{}".format(self.seed)
        content = 42342342
        self.assertTrue(self.share.write(write_int_file, content))
        self.assertIn(write_int_file, self.share.listdir())
        self.assertEqual(int(self.share.read(write_int_file)), content)
        self.assertTrue(self.share.remove(write_int_file))
        self.assertNotIn(write_int_file, self.share.listdir())

    def test_write_float(self):
        write_float_file = "write_float_{}".format(self.seed)
        content = 4234.234324
        self.assertTrue(self.share.write(write_float_file, content))
        self.assertIn(write_float_file, self.share.listdir())
        self.assertEqual(float(self.share.read(write_float_file)), content)
        self.assertTrue(self.share.remove(write_float_file))
        self.assertNotIn(write_float_file, self.share.listdir())

    def test_upload_download_file(self):
        filename = "test_file_{}".format(self.seed)
        tmp_test_dir = os.path.join(os.getcwd(), "tests", "tmp")
        if not exists(tmp_test_dir):
            self.assertTrue(makedirs(tmp_test_dir))
        upload_file = os.path.join(tmp_test_dir, filename)
        # 100 MB
        size = 1024 * 1024 * 100
        self.assertTrue(gen_random_file(upload_file, size=size))
        self.assertTrue(os.path.exists(upload_file))
        upload_hash = hashsum(upload_file)

        self.assertTrue(self.share.upload(upload_file, filename))
        self.assertIn(filename, self.share.listdir())

        download_name = "downloaded_{}".format(filename)
        download_path = os.path.join(tmp_test_dir, download_name)
        self.assertTrue(self.share.download(filename, download_path))
        self.assertTrue(os.path.exists(download_path))
        self.assertEqual(upload_hash, hashsum(download_path))

        self.assertTrue(self.share.remove(filename))
        self.assertNotIn(filename, self.share.listdir())

    def test_remote_copy(self):
        filename = "test_file_{}".format(self.seed)
        tmp_test_dir = os.path.join(os.getcwd(), "tests", "tmp")
        if not exists(tmp_test_dir):
            self.assertTrue(makedirs(tmp_test_dir))
        upload_file = os.path.join(tmp_test_dir, filename)

        size = 1024 * 1024
        self.assertTrue(gen_random_file(upload_file, size=size))
        self.assertTrue(os.path.exists(upload_file))
        upload_hash = hashsum(upload_file)

        self.assertTrue(self.share.upload(upload_file, filename))
        self.assertIn(filename, self.share.listdir())

        self.assertTrue(self.share.copy(filename, filename + "_copy"))

        download_name = "downloaded_{}".format(filename)
        download_path = os.path.join(tmp_test_dir, download_name)
        self.assertTrue(self.share.download(filename + "_copy", download_path))
        self.assertTrue(os.path.exists(download_path))
        self.assertEqual(upload_hash, hashsum(download_path))

        # Remove the original
        self.assertTrue(self.share.remove(filename))
        self.assertNotIn(filename, self.share.listdir())

        # Remove the copy
        self.assertTrue(self.share.remove(filename + "_copy"))
        self.assertNotIn(filename + "_copy", self.share.listdir())

    def test_stat(self):
        filename = "stat_file_{}".format(self.seed)
        tmp_test_dir = os.path.join(os.getcwd(), "tests", "tmp")
        if not exists(tmp_test_dir):
            self.assertTrue(makedirs(tmp_test_dir))
        upload_file = os.path.join(tmp_test_dir, filename)

        size = 1024 * 1024
        self.assertTrue(gen_random_file(upload_file, size=size))
        self.assertTrue(os.path.exists(upload_file))

        self.assertTrue(self.share.upload(upload_file, filename))
        self.assertIn(filename, self.share.listdir())

        file_stat = self.share.stat(filename)
        self.assertNotEqual(file_stat, False)
        self.assertEqual(file_stat.filesize, size)

        self.assertTrue(self.share.remove(filename))
        self.assertNotIn(filename, self.share.listdir())

    def test_setstat(self):
        filename = "set_stat_file_{}".format(self.seed)
        tmp_test_dir = os.path.join(os.getcwd(), "tests", "tmp")
        if not exists(tmp_test_dir):
            self.assertTrue(makedirs(tmp_test_dir))
        upload_file = os.path.join(tmp_test_dir, filename)

        size = 1024 * 1024
        self.assertTrue(gen_random_file(upload_file, size=size))
        self.assertTrue(os.path.exists(upload_file))

        self.assertTrue(self.share.upload(upload_file, filename))
        self.assertIn(filename, self.share.listdir())
        current_stats = self.share.stat(filename)
        self.assertNotEqual(current_stats, False)

        new_permissions = 0o0000700 | 0o0000070 | 0o0000007
        current_stats.permissions = new_permissions
        current_stats.flags = LIBSSH2_SFTP_ATTR_PERMISSIONS
        self.assertTrue(self.share.setstat(filename, current_stats))

        new_stats = self.share.stat(filename)
        self.assertNotEqual(new_stats, False)
        # FIXME, on ERDA the file permissions cannot be changed
        # self.assertEqual(stat.S_IMODE(new_stats.permissions), new_permissions)


class TestDataStoreFileHandleCases:
    def setUp(self):
        self.seed = str(random.random())[2:10]
        self.seek_file = "".join(["seek_file", self.seed])
        self.data = "Hello World"
        self.data_bytes = bytes(self.data, "utf-8")
        self.space_offset = 6
        with self.share.open(self.seek_file, "w") as _file:
            _file.write(self.data)

        self.files = [self.seek_file]

    def tearDown(self):
        for f in self.files:
            if self.share.exists(f):
                self.share.remove(f)

        share_content = self.share.listdir()
        for f in self.files:
            self.assertNotIn(f, share_content)
        self.share = None

    def test_seek_offset_whence_0(self):
        # Seek to the absolute position
        # Characters
        whence = 0
        with self.share.open(self.seek_file, "r") as _file:
            content = _file.read()
            self.assertEqual(content, self.data)

            # offset to the middle space
            _file.seek(self.space_offset, whence)
            offset_content = _file.read()
            self.assertEqual(offset_content, "World")

        # binary
        with self.share.open(self.seek_file, "rb") as _file:
            content = _file.read()
            self.assertEqual(content, self.data_bytes)

            # offset to the middle space
            _file.seek(self.space_offset, whence)
            offset_content = _file.read()
            self.assertEqual(offset_content, b"World")

    def test_seek_offset_whence_1(self):
        # Seek relative to the current position
        whence = 1
        # https://docs.python.org/3.2/tutorial/inputoutput.html#methods-of-file-objects
        # Relative seeks from other than the beginning or the end
        # is only allowed in binary mode
        with self.share.open(self.seek_file, "rb") as _file:
            content = _file.read()
            self.assertEqual(content, self.data_bytes)
            # Go to the middle
            _file.seek(self.space_offset)
            # Move forward 3 offsets
            _file.seek(3, whence)

            # Reading the file moves the offset to the end
            end_content = _file.read()
            self.assertEqual(end_content, b"ld")

            # Move back 8 chars from the end
            _file.seek(-8, whence)
            rewind_content = _file.read()
            self.assertEqual(rewind_content, b"lo World")

    def test_seek_offset_whence_2(self):
        # Seek relative to the file end
        whence = 2
        with self.share.open(self.seek_file, "r") as _file:
            content = _file.read()
            self.assertEqual(content, self.data)
            # offset to the end
            # only zero offset of the end is allowed in non-binary modes
            _file.seek(0, whence)
            offset_content = _file.read()
            self.assertEqual(offset_content, "")

        # binary
        with self.share.open(self.seek_file, "rb") as _file:
            content = _file.read()
            self.assertEqual(content, self.data_bytes)
            # offset to the end
            _file.seek(0, whence)
            offset_content = _file.read()
            # Should be empty
            self.assertEqual(offset_content, b"")

            # Binary mode supports non-zero offset relative to the end
            _file.seek(-6, whence)
            end_content = _file.read()
            self.assertEqual(end_content, b" World")

    def test_fstat_get(self):
        with self.share.open(self.seek_file, "r") as _file:
            file_stat = _file.fstat()
            self.assertEqual(file_stat.filesize, len(self.data))

        with self.share.open(self.seek_file, "rb") as _file:
            file_stat = _file.fstat()
            self.assertEqual(file_stat.filesize, len(self.data_bytes))

    def test_fstatset(self):
        with self.share.open(self.seek_file, "r") as _file:
            file_stat = _file.fstat()
            self.assertEqual(file_stat.filesize, len(self.data))
            # 777
            new_permissions = 0o0000700 | 0o0000070 | 0o0000007
            file_stat.permissions = new_permissions
            file_stat.flags = LIBSSH2_SFTP_ATTR_PERMISSIONS
            self.assertTrue(_file.fsetstat(file_stat))
            _file.fstat()
            # FIXME, on ERDA the file permissions cannot be changed
            # self.assertEqual(stat.S_IMODE(new_file_stat.permissions), new_permissions)


class SSHFSStoreTest(TestDataStoreCases, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start dummy mount container where the public key is an
        # authorized key.
        # Expose a random SSH port on the host that can be used for SSH
        # testing againt the container
        username = "mountuser"
        password = "Passw0rd!"

        cls.host = "127.0.0.1"
        cls.random_ssh_port = random.randint(2200, 2299)
        ssh_dummy_cont = {
            "image": IMAGE,
            "detach": True,
            "ports": {22: cls.random_ssh_port},
        }
        cls.container = make_container(ssh_dummy_cont)
        assert cls.container
        assert cls.container.status == "running"
        assert wait_for_container_output(cls.container.id, "Running the OpenSSH Server")
        try:
            assert wait_for_session(cls.host, cls.random_ssh_port, max_attempts=10)
            home_path = os.path.join(os.sep, "home", username)
            cls.share = SSHFSStore(
                host="127.0.0.1",
                port=f"{cls.random_ssh_port}",
                username=username,
                password=password,
                path=home_path,
            )
        except AssertionError:
            assert remove_container(cls.container.id)

    @classmethod
    def tearDownClass(cls):
        # Remove container
        assert remove_container(cls.container.id)
        cls.share = None


class SFTPStoreTest(TestDataStoreCases, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start dummy mount container where the public key is an
        # authorized key.
        # Expose a random SSH port on the host that can be used for SSH
        # testing againt the container
        cls.host = "127.0.0.1"
        cls.random_ssh_port = random.randint(2200, 2299)
        ssh_dummy_cont = {
            "image": IMAGE,
            "detach": True,
            "ports": {22: cls.random_ssh_port},
        }
        cls.container = make_container(ssh_dummy_cont)
        assert cls.container
        assert cls.container.status == "running"
        assert wait_for_container_output(cls.container.id, "Running the OpenSSH Server")
        try:
            assert wait_for_session(cls.host, cls.random_ssh_port, max_attempts=10)
            cls.share = SFTPStore(
                host=cls.host,
                port=f"{cls.random_ssh_port}",
                authenticator=SSHAuthenticator(
                    username="mountuser", password="Passw0rd!"
                ),
            )
        except AssertionError:
            assert remove_container(cls.container.id)

    @classmethod
    def tearDownClass(cls):
        # Remove container
        assert remove_container(cls.container.id)
        cls.share = None


class SFTPStoreFileHandleTest(TestDataStoreFileHandleCases, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start dummy mount container where the public key is an
        # authorized key.
        # Expose a random SSH port on the host that can be used for SSH
        # testing againt the container
        cls.host = "127.0.0.1"
        cls.random_ssh_port = random.randint(2200, 2299)
        ssh_dummy_cont = {
            "image": IMAGE,
            "detach": True,
            "ports": {22: cls.random_ssh_port},
        }
        cls.container = make_container(ssh_dummy_cont)
        assert cls.container
        assert cls.container.status == "running"
        assert wait_for_container_output(cls.container.id, "Running the OpenSSH Server")
        try:
            assert wait_for_session(cls.host, cls.random_ssh_port, max_attempts=10)
            cls.share = SFTPStore(
                host=cls.host,
                port=f"{cls.random_ssh_port}",
                authenticator=SSHAuthenticator(
                    username="mountuser", password="Passw0rd!"
                ),
            )
        except AssertionError:
            assert remove_container(cls.container.id)

    @classmethod
    def tearDownClass(cls):
        # Remove container
        assert remove_container(cls.container.id)
        cls.share = None


class SSHFSStoreFileHandleTest(TestDataStoreFileHandleCases, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start dummy mount container where the public key is an
        # authorized key.
        # Expose a random SSH port on the host that can be used for SSH
        # testing againt the container
        cls.host = "127.0.0.1"
        cls.random_ssh_port = random.randint(2200, 2299)
        ssh_dummy_cont = {
            "image": IMAGE,
            "detach": True,
            "ports": {22: cls.random_ssh_port},
        }
        cls.container = make_container(ssh_dummy_cont)
        assert cls.container
        assert cls.container.status == "running"
        assert wait_for_container_output(cls.container.id, "Running the OpenSSH Server")
        try:
            assert wait_for_session(cls.host, cls.random_ssh_port, max_attempts=10)

            username = "mountuser"
            password = "Passw0rd!"
            home_path = os.path.join(os.sep, "home", username)
            cls.share = SSHFSStore(
                host=cls.host,
                port=cls.random_ssh_port,
                username=username,
                password=password,
                path=home_path,
            )
        except AssertionError:
            assert remove_container(cls.container.id)

    @classmethod
    def tearDownClass(cls):
        # Remove container
        assert remove_container(cls.container.id)
        cls.share = None


class ERDASFTPShareFileHandleTest(TestDataStoreFileHandleCases, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        username = None
        password = None
        if "ERDA_TEST_SHARE" in os.environ:
            username = os.environ["ERDA_TEST_SHARE"]
            password = os.environ["ERDA_TEST_SHARE"]
        else:
            sharelinks_file_path = os.path.join("res", "sharelinks.txt")
            if not exists(sharelinks_file_path):
                raise Exception(
                    f"Neither the 'ERDA_TEST_SHARE' environment variable has been set, nor is the {sharelinks_file_path} file present in the res directory that can be used for ERDA authentication"
                )
            sharelinks_content = load(sharelinks_file_path, readlines=True)
            if not sharelinks_content:
                raise Exception(f"No content found in {sharelinks_file_path}")
            sharelinks = dict(
                (tuple(line.rstrip().split("=") for line in sharelinks_content))
            )
            username = sharelinks["ERDA_TEST_SHARE"]
            password = sharelinks["ERDA_TEST_SHARE"]
        if not username:
            raise Exception("No username found for ERDA authentication")
        if not password:
            raise Exception("No password found for ERDA authentication")
        cls.share = ERDASFTPShare(
            username=username,
            password=password,
        )

    @classmethod
    def tearDownClass(cls):
        cls.share = None


class ERDASFTPShareTest(TestDataStoreCases, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        username = None
        password = None
        if "ERDA_TEST_SHARE" in os.environ:
            username = os.environ["ERDA_TEST_SHARE"]
            password = os.environ["ERDA_TEST_SHARE"]
        else:
            sharelinks_file_path = os.path.join("res", "sharelinks.txt")
            if not exists(sharelinks_file_path):
                raise Exception(
                    f"Neither the 'ERDA_TEST_SHARE' environment variable has been set, nor is the {sharelinks_file_path} file present in the res directory that can be used for ERDA authentication"
                )
            sharelinks_content = load(sharelinks_file_path, readlines=True)
            if not sharelinks_content:
                raise Exception(f"No content found in {sharelinks_file_path}")
            sharelinks = dict(
                (tuple(line.rstrip().split("=") for line in sharelinks_content))
            )
            username = sharelinks["ERDA_TEST_SHARE"]
            password = sharelinks["ERDA_TEST_SHARE"]
        if not username:
            raise Exception("No username found for ERDA authentication")
        if not password:
            raise Exception("No password found for ERDA authentication")
        cls.share = ERDASFTPShare(
            username=username,
            password=password,
        )

        cls.seed = str(random.random())[2:10]
        cls.tmp_file = "".join(["tmp", cls.seed])
        cls.write_file = "".join(["write_test", cls.seed])
        cls.binary_file = "".join(["binary_test", cls.seed])
        cls.write_image = "".join(["kmeans_write.tif", cls.seed])
        cls.dir_path = "".join(["directory", cls.seed])
        cls.img = "kmeans.tif"

        cls.files = [
            cls.tmp_file,
            cls.write_file,
            cls.binary_file,
            cls.write_file,
        ]
        cls.directories = [cls.dir_path]

    @classmethod
    def tearDownClass(cls):
        for f in cls.files:
            if cls.share.exists(f):
                cls.share.remove(f)

        for d in cls.directories:
            if cls.share.exists(d):
                cls.share.rmdir(d)

        share_content = cls.share.listdir()
        for f in cls.files + cls.directories:
            assert f not in share_content
        cls.share = None

    def test_share(self):
        tmp_share = self.share.open(self.tmp_file, "wb")
        tmp_share.write(bytes("sddsfsf", "utf-8"))
        tmp_share.close()
        self.assertIn(self.tmp_file, self.share.listdir())

        # Read file directly as string
        tmp_share = self.share.open(self.tmp_file, "r")
        self.assertEqual(tmp_share.read(), "sddsfsf")
        tmp_share.close()

        # Read file directly as binary
        tmp_share = self.share.open(self.tmp_file, "rb")
        self.assertEqual(tmp_share.read(), b"sddsfsf")
        tmp_share.close()

        # Get a SFTPHandle object with automatic close
        with self.share.open(self.tmp_file, "r") as tmp:
            self.assertEqual(tmp.read(), "sddsfsf")

        # Get a default SFTPHandle object with manual lifetime
        fh = self.share.open(self.tmp_file, "r")
        self.assertIsInstance(fh, SFTPFileHandle)
        self.assertEqual(fh.read(), "sddsfsf")
        fh.close()

        # Writing strings to a file
        test_string = "Hello There"
        test_num = 42342342
        test_float = 4234.234324

        with self.share.open(self.write_file, "a") as w_file:
            w_file.write(test_string)
            w_file.write(str(test_num))
            w_file.write(str(test_float))

        with self.share.open(self.write_file, "r") as w_file:
            f_content = w_file.read()
            self.assertIn(test_string, f_content)
            self.assertIn(str(test_num), f_content)
            self.assertIn(str(test_float), f_content)

        # Writing binary to a file
        test_binary = b"Hello again"
        test_b_num = bytes(255)
        with self.share.open(self.binary_file, "ab") as b_file:
            b_file.write(test_binary)
            b_file.write(test_b_num)

        b_file = self.share.open(self.binary_file, "rb")
        f_content = b_file.read()
        self.assertIn(test_binary, f_content)
        self.assertIn(test_b_num, f_content)
        b_file.close()

        # Read 100 mb image
        with self.share.open(self.img, "rb") as b_file:
            img = b_file.read()
            self.assertGreaterEqual(sys.getsizeof(img), 133246888)

            # write 100 mb image
            with self.share.open(self.write_image, "wb") as new_b_file:
                new_b_file.write(img)

            # check that it is written
            with self.share.open(self.write_image, "rb") as new_b_file:
                new_image = new_b_file.read()
                self.assertGreaterEqual(sys.getsizeof(new_image), 133246888)
