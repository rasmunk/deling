import pytest
import unittest
import os
import random
from deling.authenticators.ssh import SSHAuthenticator
from deling.io.datastores.core import SFTPStore
from deling.utils.io import exists, makedirs, removedirs, write, remove, chmod
from deling.authenticators.ssh import (
    gen_ssh_key_pair,
    load_rsa_key_pair,
    ssh_credentials_exists,
    remove_ssh_credentials,
)
from tests.helpers import make_container, wait_for_container_output, remove_container

IMAGE_OWNER = "ucphhpc"
IMAGE_NAME = "ssh-mount-dummy"
IMAGE_TAG = "latest"
IMAGE = "".join([IMAGE_OWNER, "/", IMAGE_NAME, ":", IMAGE_TAG])


class AuthenticationTestCases:
    def test_username_password_authentication(self):
        datastore = SFTPStore(
            host="127.0.0.1",
            port=f"{self.random_ssh_port}",
            authenticator=SSHAuthenticator(
                username=self.ssh_credentials.username,
                password=self.ssh_credentials.password,
            ),
        )
        self.assertTrue(datastore.is_connected())
        datastore.disconnect()
        self.assertFalse(datastore.is_connected())

    def test_ed25519_file_key_authentication(self):
        datastore = SFTPStore(
            host="127.0.0.1",
            port=f"{self.random_ssh_port}",
            authenticator=SSHAuthenticator(
                username=self.ssh_credentials.username,
                private_key_file=self.ssh_credentials.private_key_file,
                public_key_file=self.ssh_credentials.public_key_file,
            ),
        )
        self.assertTrue(datastore.is_connected())
        datastore.disconnect()
        self.assertFalse(datastore.is_connected())

    def test_ed25519_key_memory_authentication(self):
        datastore = SFTPStore(
            host="127.0.0.1",
            port=f"{self.random_ssh_port}",
            authenticator=SSHAuthenticator(
                username=self.ssh_credentials.username,
                private_key=self.ssh_credentials.private_key,
                public_key=self.ssh_credentials.public_key,
            ),
        )
        self.assertTrue(datastore.is_connected())
        datastore.disconnect()
        self.assertFalse(datastore.is_connected())


class SFTPStoreTestAuthentication(AuthenticationTestCases, unittest.TestCase):
    def setUp(self):
        self.seed = str(random.random())[2:10]
        tmp_test_dir = os.path.join(os.getcwd(), "tests", "tmp")
        self.test_ssh_dir = os.path.join(tmp_test_dir, "ssh-{}".format(self.seed))
        if not exists(self.test_ssh_dir):
            self.assertTrue(makedirs(self.test_ssh_dir))
        # Until ssh2-python supports libssh2 1.11.0,
        # RSA keys are not hashed with SHA256 but with the
        # deprecated and unsecure SHA1
        # https://github.com/ParallelSSH/ssh2-python/issues/183
        # https://github.com/libssh2/libssh2/releases/tag/libssh2-1.11.0
        # For now, use ED25519 keys

        # Create an ssh key pair for testing
        key_type = "ed25519"
        key_name = "id_{}_{}".format(key_type, self.seed)
        self.assertTrue(
            gen_ssh_key_pair(
                ssh_dir_path=self.test_ssh_dir, key_name=key_name, key_type=key_type
            )
        )
        self.assertTrue(
            ssh_credentials_exists(
                ssh_dir_path=self.test_ssh_dir,
                key_name=key_name,
            )
        )
        self.ssh_credentials = load_rsa_key_pair(
            ssh_dir_path=self.test_ssh_dir, key_name=key_name
        )
        self.assertIsNotNone(self.ssh_credentials)
        self.ssh_credentials.username = "mountuser"
        self.ssh_credentials.password = "Passw0rd!"

        # Create an authorized key file that can be mounted inside the
        # dummy mount container.
        self.authorized_key_file = os.path.join(self.test_ssh_dir, "authorized_keys")
        self.assertTrue(
            write(self.authorized_key_file, self.ssh_credentials.public_key)
        )
        self.assertTrue(chmod(self.authorized_key_file, 0o600))

        # Start dummy mount container where the public key is an
        # authorized key.
        # Expose a random SSH port on the host that can be used for SSH
        # testing againt the container
        self.random_ssh_port = random.randint(2200, 2299)
        ssh_dummy_cont = {
            "image": IMAGE,
            "detach": True,
            "ports": {22: self.random_ssh_port},
            "volumes": [
                f"{self.authorized_key_file}:/home/mountuser/.ssh/authorized_keys"
            ],
        }
        self.container = make_container(ssh_dummy_cont)
        self.assertNotEqual(self.container, False)
        self.assertEqual(self.container.status, "running")
        self.assertTrue(
            wait_for_container_output(self.container.id, "Running the OpenSSH Server")
        )

    def tearDown(self):
        # Remove every file from test_ssh_dir
        if exists(self.test_ssh_dir):
            self.assertTrue(removedirs(self.test_ssh_dir, recursive=True))
        # Remove container
        self.assertTrue(remove_container(self.container.id))
        self.share = None
