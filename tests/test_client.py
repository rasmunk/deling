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
import random
from ssh2.sftp import SFTP
from deling.clients.ssh import (
    SSHClient,
    CHANNEL_TYPE_SFTP,
    SSHClientResultCode,
    read_channel_exit_status,
)
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
        cls.random_ssh_port = random.randint(2200, 2500)
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

    def tearDown(self):
        # Ensure that we disconnect after a test
        self.client.disconnect()

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

    def test_client_exec_command(self):
        input_data = "Hello World"
        command = f"echo {input_data}"
        self.assertTrue(self.client.connect())
        self.assertTrue(self.client.open_channel())
        channel = self.client.get_channel()
        self.assertIsNotNone(channel)

        success, response = self.client.exec_command(command, channel=channel)
        self.assertIsInstance(success, SSHClientResultCode)
        self.assertEqual(success, SSHClientResultCode.SUCCESS)

        self.assertIsInstance(response, dict)
        self.assertGreater(len(response), 0)
        self.assertIn("exit_code", response)
        self.assertIn("output", response)
        self.assertIsInstance(response["exit_code"], int)
        self.assertIsInstance(response["output"], str)
        self.assertDictEqual(response, {"exit_code": 0, "output": f"{input_data}\n"})

        self.client.close_channel()
        self.assertIsNone(self.client.channel)
        self.client.disconnect()

    def test_client_run_single_command(self):
        input_data = "Hdk1902dm10d9m1d"
        command = f"echo {input_data}"
        success, response = self.client.run_single_command(command)
        self.assertIsInstance(success, SSHClientResultCode)
        self.assertEqual(success, SSHClientResultCode.SUCCESS)

        self.assertIsInstance(response, dict)
        self.assertGreater(len(response), 0)
        self.assertIn("exit_code", response)
        self.assertIn("output", response)
        self.assertIsInstance(response["exit_code"], int)
        self.assertIsInstance(response["output"], str)
        self.assertDictEqual(response, {"exit_code": 0, "output": f"{input_data}\n"})

        self.assertFalse(self.client.is_session_connected())
        self.assertFalse(self.client.is_socket_connected())

    def test_client_run_single_command_return_stderr(self):
        input_data = "Hello World"
        incorrect_command = f"42 {input_data}"
        success, response = self.client.run_single_command(incorrect_command)
        self.assertIsInstance(success, SSHClientResultCode)
        self.assertEqual(success, SSHClientResultCode.STDERR_RESPONSE)

        self.assertIsInstance(response, dict)
        self.assertGreater(len(response), 0)
        self.assertIsInstance(response["exit_code"], int)
        self.assertIsInstance(response["output"], str)

        # 127 == invalid command
        self.assertEqual(response["exit_code"], 127)
        self.assertGreater(len(response["output"]), 0)
        self.assertIn("command not found", response["output"])

        self.assertFalse(self.client.is_session_connected())
        self.assertFalse(self.client.is_socket_connected())

    def test_client_multiple_commands(self):
        commands = [
            "echo Hello",
            "echo World",
            "echo Test",
        ]
        responses = self.client.run_multiple_commands(commands)
        self.assertEqual(len(responses), len(commands))
        for rsp in responses:
            success, response = rsp[0], rsp[1]
            self.assertIsInstance(success, SSHClientResultCode)
            self.assertEqual(success, SSHClientResultCode.SUCCESS)
            self.assertIsInstance(response, dict)
            self.assertGreater(len(response), 0)
            self.assertIsInstance(response["exit_code"], int)
            self.assertIsInstance(response["output"], str)
        response_msgs = [rsp[1]["output"] for rsp in responses]
        self.assertIn("Hello\n", response_msgs)
        self.assertIn("World\n", response_msgs)
        self.assertIn("Test\n", response_msgs)
        response_exit_codes = [rsp[1]["exit_code"] for rsp in responses]
        self.assertListEqual(response_exit_codes, [0, 0, 0])

        self.assertFalse(self.client.is_session_connected())
        self.assertFalse(self.client.is_socket_connected())

    def test_client_multiple_commands_return_stderr(self):
        commands = [
            "cat --asdasdad",
            "41 World",
            "1231 Test",
        ]
        responses = self.client.run_multiple_commands(commands)
        self.assertEqual(len(responses), len(commands))
        for rsp in responses:
            success, response = rsp[0], rsp[1]
            self.assertIsInstance(success, SSHClientResultCode)
            self.assertEqual(success, SSHClientResultCode.STDERR_RESPONSE)
            self.assertIsInstance(response, dict)
            self.assertGreater(len(response), 0)
            self.assertIsInstance(response["exit_code"], int)
            self.assertIsInstance(response["output"], str)
        response_msgs = [rsp[1]["output"] for rsp in responses]
        self.assertIn("unrecognized option", response_msgs[0])
        self.assertIn("command not found", response_msgs[1])
        self.assertIn("command not found", response_msgs[2])
        response_exit_codes = [rsp[1]["exit_code"] for rsp in responses]
        # 1 == unrecognized option
        # 127 == invalid command
        self.assertListEqual(response_exit_codes, [1, 127, 127])
