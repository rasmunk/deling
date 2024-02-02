import unittest
import os
from random import random
from deling.clients.ssh import SSHClient
from deling.authenticators.ssh import SSHAuthenticator
from deling.utils.io import exists, makedirs, removedirs

# Set the test salt to use for hashing the known_hosts entry hostname
knownhost_salt = "testsalt"


class CommonClientTestCases:
    def test_client_connection(self):
        self.assertTrue(self.client.connect())
        self.assertTrue(self.client.is_socket_connected())
        self.client.disconnect()


class SSHClientTestAuthentication(CommonClientTestCases, unittest.TestCase):
    def setUp(self):
        self.seed = str(random())[2:10]
        tmp_test_dir = os.path.join(os.getcwd(), "tests", "tmp")
        self.test_ssh_dir = os.path.join(tmp_test_dir, "ssh-{}".format(self.seed))
        if not exists(self.test_ssh_dir):
            self.assertTrue(makedirs(self.test_ssh_dir))

        host = "127.0.0.1"
        port = "2222"
        username = "mountuser"
        password = "Passw0rd!"

        authenticator = SSHAuthenticator(username=username, password=password)
        self.client = SSHClient(host, authenticator, port=port)

    def tearDown(self):
        # Remove every file from test_ssh_dir
        if exists(self.test_ssh_dir):
            self.assertTrue(removedirs(self.test_ssh_dir, recursive=True))
        self.share = None

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

    def test_client_channel(self):
        self.assertTrue(self.client.connect())
        self.assertTrue(self.client.open_channel())
        self.assertTrue(self.client.channel)
        self.client.close_channel()
        self.assertIsNone(self.client.channel)
        self.client.disconnect()
