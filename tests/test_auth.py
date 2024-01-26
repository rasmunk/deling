import unittest
import os
from random import random
from deling.authenticators.ssh import SSHAuthenticator
from deling.io.datastores.core import SFTPStore
from deling.utils.io import exists, makedirs
from deling.authenticators.ssh import (
    gen_ssh_key_pair,
    load_rsa_key_pair,
    ssh_credentials_exists,
    remove_ssh_credentials,
)


class AuthenticationTestCases:
    def test_username_password_authentication(self):
        datastore = SFTPStore(
            host="127.0.0.1",
            port="2222",
            authenticator=SSHAuthenticator(
                username=self.username, password=self.password
            ),
        )
        self.assertTrue(datastore.is_connected())
        datastore.disconnect()
        self.assertFalse(datastore.is_connected())

    def test_ed25519_file_key_authentication(self):
        key_type = "ed25519"
        key_name = "id_{}_{}".format(key_type, self.seed)
        self.assertTrue(gen_ssh_key_pair(key_name=key_name, key_type=key_type))
        self.assertTrue(
            ssh_credentials_exists(
                key_name=key_name,
            )
        )
        ssh_credentials = load_rsa_key_pair(key_name=key_name)
        self.assertIsNotNone(ssh_credentials)
        datastore = SFTPStore(
            host="127.0.0.1",
            port="2222",
            authenticator=SSHAuthenticator(
                username=self.username,
                private_key_file=ssh_credentials.private_key_file,
            ),
        )
        self.assertTrue(datastore.is_connected())
        datastore.disconnect()
        self.assertFalse(datastore.is_connected())
        self.assertTrue(remove_ssh_credentials(key_name=key_name))
        self.assertFalse(ssh_credentials_exists(key_name=key_name))


class SFTPStoreTestED25519KeyAuthentication(AuthenticationTestCases, unittest.TestCase):
    def setUp(self):
        self.seed = str(random())[2:10]
        tmp_test_dir = os.path.join(os.getcwd(), "tests", "tmp")
        if not exists(tmp_test_dir):
            self.assertTrue(makedirs(tmp_test_dir))

        self.username = "mountuser"
        self.password = "Passw0rd!"
        # Until ssh2-python supports libssh2 1.11.0,
        # RSA keys are not hashed with SHA256 but with the
        # deprecated and unsecure SHA1
        # https://github.com/ParallelSSH/ssh2-python/issues/183
        # https://github.com/libssh2/libssh2/releases/tag/libssh2-1.11.0
        # For now, use ED25519 keys

    def tearDown(self):
        self.share = None
