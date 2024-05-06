import pytest
import unittest
import os
import random
from deling.authenticators.ssh import SSHAuthenticator
from deling.io.datastores.core import SFTPStore
from deling.utils.io import exists, makedirs, removedirs
from deling.authenticators.ssh import (
    gen_ssh_key_pair,
    load_rsa_key_pair,
    ssh_credentials_exists,
    remove_ssh_credentials,
)
from tests.helpers import make_container, wait_for_container_output



# Set the test salt to use for hashing the known_hosts entry hostname
knownhost_salt = "testsalt"

IMAGE_OWNER = "ucphhpc"
IMAGE_NAME = "ssh-mount-dummy"
IMAGE_TAG = "edge"
IMAGE = ''.join([IMAGE_OWNER, "/", IMAGE_NAME, ":", IMAGE_TAG])

class AuthenticationTestCases:
    def test_username_password_authentication(self):
        datastore = SFTPStore(
            host="127.0.0.1",
            port="2222",
            authenticator=SSHAuthenticator(
                username=self.username, password=self.password
            ),
            authenticator_prepare_kwargs={"knownhost_salt": knownhost_salt},
        )
        self.assertTrue(datastore.is_connected())
        datastore.disconnect()
        self.assertFalse(datastore.is_connected())

    def test_ed25519_file_key_authentication(self):
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
        ssh_credentials = load_rsa_key_pair(
            ssh_dir_path=self.test_ssh_dir, key_name=key_name
        )
        self.assertIsNotNone(ssh_credentials)
        # Start dummy mount container where the public key is an
        # authorized key
        random_ssh_port = random.randint(2200, 2299)
        ssh_dummy_cont = {
            'image': IMAGE,
            'detach': True,
            'ports': {22: random_ssh_port},
            'volumes': {
                ssh_credentials.public_key_file: {
                    'bind': '/home/mountuser/.ssh/authorized_keys',
                    'mode': 'rw',
                }
            },
        }
        container = make_container(ssh_dummy_cont)
        self.assertNotEqual(container, False)
        self.assertEqual(container.status, "running")
        self.assertTrue(wait_for_container_output(container.id, "Running the OpenSSH Server"))

        datastore = SFTPStore(
            host="127.0.0.1",
            port=f"{random_ssh_port}",
            authenticator=SSHAuthenticator(
                username=self.username,
                private_key_file=ssh_credentials.private_key_file,
                public_key_file=ssh_credentials.public_key_file,
            ),
        )
        self.assertTrue(datastore.is_connected())
        datastore.disconnect()
        self.assertFalse(datastore.is_connected())
        self.assertTrue(
            remove_ssh_credentials(ssh_dir_path=self.test_ssh_dir, key_name=key_name)
        )
        self.assertFalse(
            ssh_credentials_exists(ssh_dir_path=self.test_ssh_dir, key_name=key_name)
        )

    def test_ed25519_key_memory_authentication(self):
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
        ssh_credentials = load_rsa_key_pair(
            ssh_dir_path=self.test_ssh_dir, key_name=key_name
        )
        self.assertIsNotNone(ssh_credentials)
        # Start dummy mount container where the public key is an
        # authorized key
        random_ssh_port = random.randint(2200, 2299)
        ssh_dummy_cont = {
            'image': IMAGE,
            'detach': True,
            'ports': {22: random_ssh_port},
            'volumes': {
                ssh_credentials.public_key_file: {
                    'bind': '/home/mountuser/.ssh/authorized_keys',
                    'mode': 'rw',
                }
            },
        }
        container = make_container(ssh_dummy_cont)
        self.assertNotEqual(container, False)
        self.assertEqual(container.status, "running")
        self.assertTrue(wait_for_container_output(container.id, "Running the OpenSSH Server"))

        datastore = SFTPStore(
            host="127.0.0.1",
            port=f"{random_ssh_port}",
            authenticator=SSHAuthenticator(
                username=self.username,
                private_key=ssh_credentials.private_key,
                public_key=ssh_credentials.public_key,
            ),
        )
        self.assertTrue(datastore.is_connected())
        datastore.disconnect()
        self.assertFalse(datastore.is_connected())
        self.assertTrue(
            remove_ssh_credentials(ssh_dir_path=self.test_ssh_dir, key_name=key_name)
        )
        self.assertFalse(
            ssh_credentials_exists(ssh_dir_path=self.test_ssh_dir, key_name=key_name)
        )


class SFTPStoreTestAuthentication(AuthenticationTestCases, unittest.TestCase):
    def setUp(self):
        self.seed = str(random.random())[2:10]
        tmp_test_dir = os.path.join(os.getcwd(), "tests", "tmp")
        self.test_ssh_dir = os.path.join(tmp_test_dir, "ssh-{}".format(self.seed))
        if not exists(self.test_ssh_dir):
            self.assertTrue(makedirs(self.test_ssh_dir))

        self.username = "mountuser"
        self.password = "Passw0rd!"
        # TODO, launch the test docker container
        # Until ssh2-python supports libssh2 1.11.0,
        # RSA keys are not hashed with SHA256 but with the
        # deprecated and unsecure SHA1
        # https://github.com/ParallelSSH/ssh2-python/issues/183
        # https://github.com/libssh2/libssh2/releases/tag/libssh2-1.11.0
        # For now, use ED25519 keys

    def tearDown(self):
        # Remove every file from test_ssh_dir
        if exists(self.test_ssh_dir):
            self.assertTrue(removedirs(self.test_ssh_dir, recursive=True))
        self.share = None
