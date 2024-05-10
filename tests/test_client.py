import unittest
import os
import random
from ssh2.sftp import SFTP
from deling.clients.ssh import SSHClient, CHANNEL_TYPE_SFTP
from deling.authenticators.ssh import SSHAuthenticator
from deling.utils.io import exists, makedirs, removedirs
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


class CommonClientTestCases:
    def test_client_connection(self):
        self.assertTrue(self.client.connect())
        self.assertTrue(self.client.is_socket_connected())
        self.client.disconnect()


class SSHClientTestAuthentication(CommonClientTestCases, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed = str(random.random())[2:10]
        tmp_test_dir = os.path.join(os.getcwd(), "tests", "tmp")
        cls.test_ssh_dir = os.path.join(tmp_test_dir, "ssh-{}".format(cls.seed))
        if not exists(cls.test_ssh_dir):
            assert makedirs(cls.test_ssh_dir)

        cls.host = "127.0.0.1"
        username = "mountuser"
        password = "Passw0rd!"

        # Start dummy mount container where the public key is an
        # authorized key.
        # Expose a random SSH port on the host that can be used for SSH
        # testing againt the container
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
            authenticator = SSHAuthenticator(username=username, password=password)
            cls.client = SSHClient(cls.host, authenticator, port=cls.random_ssh_port)
        except AssertionError:
            assert remove_container(cls.container.id)

    @classmethod
    def tearDownClass(cls):
        # Remove every file from test_ssh_dir
        if exists(cls.test_ssh_dir):
            assert removedirs(cls.test_ssh_dir, recursive=True)
        # Remove container
        assert remove_container(cls.container.id)
        cls.share = None

    def test_socket_connection(self):
        self.assertTrue(self.client._init_socket())
        self.assertTrue(self.client._connect_socket())
        self.assertTrue(self.client.is_socket_connected())
        self.client._close_socket()
        self.assertFalse(self.client.is_socket_connected())

    def test_client_session_connection(self):
        self.assertTrue(self.client._init_socket())
        self.assertTrue(self.client._connect_socket())
        self.assertTrue(self.client.is_socket_connected())

        self.assertTrue(self.client._init_session())
        self.assertTrue(self.client._connect_session())
        self.client._close_session()
        self.client._close_socket()
        self.assertFalse(self.client.is_socket_connected())

    def test_client_authentication(self):
        self.assertFalse(self.client.is_socket_connected())
        self.assertTrue(self.client._init_socket())
        self.assertTrue(self.client._connect_socket())
        self.assertTrue(self.client.is_socket_connected())
        self.assertTrue(self.client._connect_session())
        self.assertTrue(self.client._authenticate())
        self.client.disconnect()
        self.assertFalse(self.client.is_socket_connected())

    def test_client_connect(self):
        self.assertFalse(self.client.is_socket_connected())
        self.assertTrue(self.client.connect())
        self.assertTrue(self.client.is_socket_connected())
        self.client.disconnect()
        self.assertFalse(self.client.is_socket_connected())

    def test_client_session_channel(self):
        self.assertTrue(self.client.connect())
        self.assertTrue(self.client.open_channel())
        self.assertIsNotNone(self.client.channel)
        self.client.close_channel()
        self.assertIsNone(self.client.channel)
        self.client.disconnect()

    def test_client_sftp_channel(self):
        self.assertTrue(self.client.connect())
        self.assertTrue(self.client.open_channel(channel_type=CHANNEL_TYPE_SFTP))
        sftp_channel = self.client.get_channel(channel_type=CHANNEL_TYPE_SFTP)
        self.assertIsInstance(sftp_channel, SFTP)
        self.assertEqual(sftp_channel, self.client.sftp_channel)
        self.client.close_channel(channel_type=CHANNEL_TYPE_SFTP)
        self.assertIsNone(self.client.sftp_channel)
        self.client.disconnect()
