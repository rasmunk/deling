import unittest
import os
import sys
from random import random
from deling.authenticators.ssh import SSHAuthenticator
from deling.io.datastores.core import SFTPStore, SSHFSStore, SFTPFileHandle
from deling.io.datastores.erda import ERDASFTPShare


class TestDataStoreCases:
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

    # def test_list_attr_file(self):
    #     list_attr_file = "list_attr_file_{}".format(self.seed)
    #     content = "Hello There"
    #     self.assertTrue(self.share.write(list_attr_file, content))
    #     self.assertIn(list_attr_file, self.share.listdir())
    #     self.assertEqual(self.share.read(list_attr_file), content)
    #     self.assertTrue(self.share.remove(list_attr_file))
    #     self.assertNotIn(list_attr_file, self.share.listdir())


class TestDataStoreSeekOffsetCases:
    def setUp(self):
        self.seed = str(random())[2:10]
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


class SSHFSStoreTest(TestDataStoreCases, unittest.TestCase):
    def setUp(self):
        username = "mountuser"
        password = "Passw0rd!"
        home_path = os.path.join(os.sep, "home", username)
        self.share = SSHFSStore(
            host="127.0.0.1",
            port="2222",
            username=username,
            password=password,
            path=home_path,
        )
        self.seed = str(random())[2:10]

    def tearDown(self):
        self.share = None


class SFTPStoreTest(TestDataStoreCases, unittest.TestCase):
    def setUp(self):
        self.share = SFTPStore(
            host="127.0.0.1",
            port="2222",
            authenticator=SSHAuthenticator(username="mountuser", password="Passw0rd!"),
        )
        self.seed = str(random())[2:10]

    def tearDown(self):
        self.share = None


class SFTPStoreSeekOffsetTest(TestDataStoreSeekOffsetCases, unittest.TestCase):
    def setUp(self):
        self.share = SFTPStore(
            host="127.0.0.1",
            port="2222",
            authenticator=SSHAuthenticator(username="mountuser", password="Passw0rd!"),
        )
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.share = None


class SSHFSStoreSeekOffsetTest(TestDataStoreSeekOffsetCases, unittest.TestCase):
    def setUp(self):
        username = "mountuser"
        password = "Passw0rd!"
        home_path = os.path.join(os.sep, "home", username)
        self.share = SSHFSStore(
            host="127.0.0.1",
            port="2222",
            username=username,
            password=password,
            path=home_path,
        )
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.share = None


class ERDASFTPShareSeekOffsetTest(TestDataStoreSeekOffsetCases, unittest.TestCase):
    def setUp(self):
        # Load Sharelinks
        try:
            with open("res/sharelinks.txt", "r") as file:
                content = file.readlines()
            assert content is not None
            assert len(content) > 0
            sharelinks = dict((tuple(line.rstrip().split("=") for line in content)))
        except IOError:
            # CI
            assert "ERDA_TEST_SHARE" in os.environ
            sharelinks = {"ERDA_TEST_SHARE": os.environ["ERDA_TEST_SHARE"]}

        # TODO, ensure that no more than 16 concurrent sessions are open
        # since ERDA only allows 16 concurrent sessions per user
        self.share = ERDASFTPShare(
            username=sharelinks["ERDA_TEST_SHARE"],
            password=sharelinks["ERDA_TEST_SHARE"],
        )
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.share = None


class ERDASFTPShareTest(TestDataStoreCases, unittest.TestCase):
    share = None

    def setUp(self):
        # Load Sharelinks
        try:
            with open("res/sharelinks.txt", "r") as file:
                content = file.readlines()
            assert content is not None
            assert len(content) > 0
            sharelinks = dict((tuple(line.rstrip().split("=") for line in content)))
        except IOError:
            # CI
            assert "ERDA_TEST_SHARE" in os.environ
            sharelinks = {"ERDA_TEST_SHARE": os.environ["ERDA_TEST_SHARE"]}

        # TODO, ensure that no more than 16 concurrent sessions are open
        # since ERDA only allows 16 concurrent sessions per user
        self.share = ERDASFTPShare(
            username=sharelinks["ERDA_TEST_SHARE"],
            password=sharelinks["ERDA_TEST_SHARE"],
        )
        self.seed = str(random())[2:10]
        self.tmp_file = "".join(["tmp", self.seed])
        self.write_file = "".join(["write_test", self.seed])
        self.binary_file = "".join(["binary_test", self.seed])
        self.write_image = "".join(["kmeans_write.tif", self.seed])
        self.dir_path = "".join(["directory", self.seed])
        self.img = "kmeans.tif"

        self.files = [
            self.tmp_file,
            self.write_file,
            self.binary_file,
            self.write_file,
        ]
        self.directories = [self.dir_path]

    def tearDown(self):
        for f in self.files:
            if self.share.exists(f):
                self.share.remove(f)

        for d in self.directories:
            if self.share.exists(d):
                self.share.rmdir(d)

        share_content = self.share.listdir()
        for f in self.files + self.directories:
            self.assertNotIn(f, share_content)
        self.share = None

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
