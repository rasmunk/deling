import unittest
import sys
import os
import _io
from random import random
from mig.io import (
    ERDASSHFSShare,
    ERDASftpShare,
    SFTPFileHandle,
)

# Test input
try:
    with open("res/sharelinks.txt", "r") as file:
        content = file.readlines()
    assert content is not None
    assert len(content) > 0
    sharelinks = dict((tuple(line.rstrip().split("=") for line in content)))
except IOError:
    # Travis
    assert "ERDA_TEST_SHARE" in os.environ

    sharelinks = {"ERDA_TEST_SHARE": os.environ["ERDA_TEST_SHARE"]}


class ERDASSHFSShareTest(unittest.TestCase):
    share = None

    def setUp(self):
        # Open connection to a sharelink
        assert "ERDA_TEST_SHARE" in sharelinks
        self.share = ERDASSHFSShare(sharelinks["ERDA_TEST_SHARE"])
        self.seed = str(random())[2:10]
        self.tmp_file = "".join(["tmp", self.seed])
        self.write_file = "".join(["write_test", self.seed])
        self.binary_file = "".join(["binary_test", self.seed])
        self.dir_path = "".join(["directory", self.seed])

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

        share_content = self.share.list()
        for f in self.files + self.directories:
            self.assertNotIn(f, share_content)
        self.share = None

    def test_share(self):
        # List files/dirs in share
        self.share.write(self.tmp_file, "sddsfsf")
        self.assertIn(self.tmp_file, self.share.list())
        # Read file directly as string
        # self.assertEqual(self.share.read(self.tmp_file), "sddsfsf")
        # Read file directly as binary
        # self.assertEqual(self.share.read_binary(self.tmp_file), b"sddsfsf")

        # Get a _io.TextIOWrapper object with automatic close
        with self.share.open(self.tmp_file, "r") as fh:
            self.assertEqual(fh.read(), "sddsfsf")

        # Get a default _io.TextIOWrapper object with manual lifetime
        fh = self.share.open(self.tmp_file, "r")
        self.assertIsInstance(fh, _io.TextIOWrapper)
        self.assertEqual(fh.read(), "sddsfsf")
        fh.close()

        # Writing strings to a file
        test_string = "Hello There"
        test_num = 42342342
        test_float = 3434.231

        with self.share.open(self.write_file, "w") as w_file:
            w_file.write(test_string)
            w_file.write(test_num)
            w_file.write(test_float)

        self.assertIn(test_string, self.share.read(self.write_file))
        self.assertIn(str(test_num), self.share.read(self.write_file))
        self.assertIn(str(test_float), self.share.read(self.write_file))

        # Writing binary to a file
        test_binary = b"Hello again"
        test_b_num = bytes(255)
        with self.share.open(self.binary_file, "wb") as b_file:
            b_file.write(test_binary)
            b_file.write(test_b_num)

        self.assertIn(test_binary, self.share.read_binary(self.binary_file))
        self.assertIn(test_b_num, self.share.read_binary(self.binary_file))

    def test_mkdir(self):
        self.assertFalse(self.share.exists(self.dir_path))
        self.share.mkdir(self.dir_path)
        self.assertIn(self.dir_path, self.share.list())


class ERDASFTPShareTest(unittest.TestCase):
    share = None

    def setUp(self):
        assert "ERDA_TEST_SHARE" in sharelinks
        self.share = ERDASftpShare(
            sharelinks["ERDA_TEST_SHARE"], sharelinks["ERDA_TEST_SHARE"]
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

        share_content = self.share.list()
        for f in self.files + self.directories:
            self.assertNotIn(f, share_content)
        self.share = None

    def test_share(self):
        tmp_share = self.share.open(self.tmp_file, "w")
        tmp_share.write(bytes("sddsfsf", "utf-8"))
        tmp_share.close()
        self.assertIn(self.tmp_file, self.share.list())

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
            w_file.write(bytes(test_float))

        with self.share.open(self.write_file, "r") as w_file:
            f_content = w_file.read()
            self.assertIn(test_string, f_content)
            self.assertIn(test_num, f_content)
            self.assertIn(test_float, f_content)

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

    def test_mkdir(self):
        self.assertFalse(self.share.exists(self.dir_path))
        self.share.mkdir(self.dir_path)
        self.assertIn(self.dir_path, self.share.list())


class ShareSFTPSeekOffsetTest(unittest.TestCase):
    share = None

    def setUp(self):
        assert "ERDA_TEST_SHARE" in sharelinks
        self.share = ERDASftpShare(
            sharelinks["ERDA_TEST_SHARE"], sharelinks["ERDA_TEST_SHARE"]
        )
        self.seed = str(random())[2:10]
        self.seek_file = "".join(["seek_file", self.seed])
        self.data = "Hello World"
        self.space_offset = 6
        with self.share.open(self.seek_file, "w") as _file:
            _file.write(self.data)

        self.files = [self.seek_file]

    def tearDown(self):
        for f in self.files:
            if self.share.exists(f):
                self.share.remove(f)

        share_content = self.share.list()
        for f in self.files:
            self.assertNotIn(f, share_content)
        self.share = None

    def test_seek_offset(self):
        tmp_share = self.share.open(self.seek_file, "w")
        tmp_share.write("Hello World")

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
            self.assertEqual(content, self.data)

            # offset to the middle space
            _file.seek(self.space_offset, whence)
            offset_content = _file.read()
            self.assertEqual(offset_content, "World")

    def test_seek_offset_whence_1(self):
        # Seek relative to the current position
        whence = 1
        # https://docs.python.org/3.2/tutorial/inputoutput.html#methods-of-file-objects
        # Relative seeks from other than the beginning or the end
        # is only allowed in binary mode
        with self.share.open(self.seek_file, "rb") as _file:
            content = _file.read()
            self.assertEqual(content, self.data)
            # Go to the middle
            _file.seek(self.space_offset)
            # Move forward 3 offsets
            _file.seek(3, whence)

            # Reading the file moves the offset to the end
            end_content = _file.read()
            self.assertEqual(end_content, "ld")

            # Move back 8 chars from the end
            _file.seek(-8, whence)
            rewind_content = _file.read()
            self.assertEqual(rewind_content, "lo World")

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
            self.assertEqual(content, self.data)
            # offset to the end
            _file.seek(0, whence)
            offset_content = _file.read()
            # Should be empty
            self.assertEqual(offset_content, "")

            # Binary mode supports non-zero offset relative to the end
            _file.seek(-6, whence)
            end_content = _file.read()
            self.assertEqual(end_content, " World")


class ShareSSHFSSeekOffsetTest(unittest.TestCase):
    share = None

    def setUp(self):
        assert "ERDA_TEST_SHARE" in sharelinks
        self.share = ERDASSHFSShare(sharelinks["ERDA_TEST_SHARE"])
        self.seed = str(random())[2:10]
        self.seek_file = "".join(["seek_file", self.seed])
        self.data = "Hello World"
        self.space_offset = 6
        with self.share.open(self.seek_file, "w") as _file:
            _file.write(self.data)

        self.files = [self.seek_file]

    def tearDown(self):
        for f in self.files:
            if self.share.exists(f):
                self.share.remove(f)

        share_content = self.share.list()
        for f in self.files:
            self.assertNotIn(f, share_content)
        self.share = None

    def test_seek_offset(self):
        tmp_share = self.share.open(self.seek_file, "w")
        tmp_share.write("Hello World")

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
            self.assertEqual(content, self.data)

            # offset to the middle space
            _file.seek(self.space_offset, whence)
            offset_content = _file.read()
            self.assertEqual(offset_content, "World")

    def test_seek_offset_whence_1(self):
        # Seek relative to the current position
        whence = 1
        # https://docs.python.org/3.2/tutorial/inputoutput.html#methods-of-file-objects
        # Relative seeks from other than the beginning or the end
        # is only allowed in binary mode
        with self.share.open(self.seek_file, "rb") as _file:
            content = _file.read()
            self.assertEqual(content, self.data)
            # Go to the middle
            _file.seek(self.space_offset)
            # Move forward 3 offsets
            _file.seek(3, whence)

            # Reading the file moves the offset to the end
            end_content = _file.read()
            self.assertEqual(end_content, "ld")

            # Move back 8 chars from the end
            _file.seek(-8, whence)
            rewind_content = _file.read()
            self.assertEqual(rewind_content, "lo World")

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
            self.assertEqual(content, self.data)
            # offset to the end
            _file.seek(0, whence)
            offset_content = _file.read()
            # Should be empty
            self.assertEqual(offset_content, "")

            # Binary mode supports non-zero offset relative to the end
            _file.seek(-6, whence)
            end_content = _file.read()
            self.assertEqual(end_content, " World")
