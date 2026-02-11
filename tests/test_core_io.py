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

import unittest
import os
import stat
import random
from ssh2.sftp import LIBSSH2_SFTP_ATTR_PERMISSIONS
from deling.authenticators.ssh import SSHAuthenticator
from deling.io.datastores.core import SFTPStore
from deling.utils.io import makedirs, exists
from common import CommonDataStoreTests, CommonDataStoreFileHandleTests
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


class SFTPStoreTest(CommonDataStoreTests, unittest.TestCase):
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
        self.assertEqual(stat.S_IMODE(new_stats.permissions), new_permissions)


class SFTPStoreFileHandleTest(CommonDataStoreFileHandleTests, unittest.TestCase):
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

            new_file_stat = _file.fstat()
            self.assertEqual(stat.S_IMODE(new_file_stat.permissions), new_permissions)
