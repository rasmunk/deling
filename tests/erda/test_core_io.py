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

import os
import unittest
import random
import pytest

from deling.io.datastores.file import SFTPFileHandle
from deling.io.datastores.erda import ERDASFTPShare
from deling.utils.io import makedirs, exists, load
from common import CommonDataStoreTests, CommonDataStoreFileHandleTests
from utils import gen_random_file


@pytest.mark.erda
class ERDASFTPShareFileHandleTest(CommonDataStoreFileHandleTests, unittest.TestCase):
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


@pytest.mark.erda
class ERDASFTPShareTest(CommonDataStoreTests, unittest.TestCase):
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
        # On ERDA, you can't change the file permissions
