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
import random
from deling.authenticators.ssh import SSHAuthenticator
from deling.io.datastores.core import SFTPStore
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


class SFTPStoreLifeTimeTests(unittest.TestCase):
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
        except AssertionError:
            assert remove_container(cls.container.id)

    @classmethod
    def tearDownClass(cls):
        # Remove container
        assert remove_container(cls.container.id)
        cls.share = None

    def test_store(self):
        datastore = SFTPStore(
            host=SFTPStoreLifeTimeTests.host,
            port=f"{SFTPStoreLifeTimeTests.random_ssh_port}",
            authenticator=SSHAuthenticator(username="mountuser", password="Passw0rd!"),
        )
        self.assertIsNotNone(datastore)
        self.assertIsNotNone(datastore.ssh_client)
        self.assertIsNotNone(datastore.sftp_channel)
        self.assertTrue(datastore.is_connected())

    def test_with_store(self):
        with SFTPStore(
            host=SFTPStoreLifeTimeTests.host,
            port=f"{SFTPStoreLifeTimeTests.random_ssh_port}",
            authenticator=SSHAuthenticator(username="mountuser", password="Passw0rd!"),
        ) as _share:
            self.assertIsNotNone(_share)
            self.assertIsNotNone(_share.ssh_client)
            self.assertIsNotNone(_share.sftp_channel)
            self.assertTrue(_share.is_connected())
        # Validate that the cleanup has been done
        self.assertFalse(_share.is_connected())

    def test_with_store_state(self):
        with SFTPStore(
            host=SFTPStoreLifeTimeTests.host,
            port=f"{SFTPStoreLifeTimeTests.random_ssh_port}",
            authenticator=SSHAuthenticator(username="mountuser", password="Passw0rd!"),
        ) as _share:
            self.assertIsNotNone(_share)
            self.assertIsNotNone(_share.ssh_client)
            self.assertIsNotNone(_share.sftp_channel)
            self.assertTrue(_share.is_connected())
        # Validate that the cleanup has been done
        self.assertFalse(_share.is_connected())
