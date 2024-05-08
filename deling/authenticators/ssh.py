import os
import socket
import base64
from ssh2.session import Session
from ssh2.session import (
    LIBSSH2_HOSTKEY_TYPE_RSA,
    LIBSSH2_HOSTKEY_TYPE_ECDSA_256,
    LIBSSH2_HOSTKEY_TYPE_ECDSA_384,
    LIBSSH2_HOSTKEY_TYPE_ECDSA_521,
    LIBSSH2_HOSTKEY_TYPE_ED25519,
)
from ssh2.knownhost import (
    LIBSSH2_KNOWNHOST_KEY_SSHRSA,
    LIBSSH2_KNOWNHOST_KEY_ECDSA_256,
    LIBSSH2_KNOWNHOST_KEY_ECDSA_384,
    LIBSSH2_KNOWNHOST_KEY_ECDSA_521,
    LIBSSH2_KNOWNHOST_KEY_ED25519,
    LIBSSH2_KNOWNHOST_TYPE_PLAIN,
    LIBSSH2_KNOWNHOST_TYPE_SHA1,
    LIBSSH2_KNOWNHOST_KEYENC_BASE64,
    LIBSSH2_KNOWNHOST_KEYENC_RAW,
)
from deling.utils.io import (
    acquire_lock,
    release_lock,
    write,
    remove_content_from_file,
    load,
    chmod,
    remove,
    exists,
)
from deling.utils.run import run

default_ssh_path = os.path.join(os.path.expanduser("~"), ".ssh")


class SSHKnownHost:
    host = None
    key_type = None
    key = None

    def __init__(self, host, key_type, key):
        self.host = host
        self.key_type = key_type
        self.key = key

    def __str__(self):
        return f"{self.host} {self.key_type} {self.key}"


class SSHAuthenticator:
    def __init__(self, **kwargs):
        self._credentials = SSHCredentials(**kwargs)
        self._is_prepared = False

    @property
    def credentials(self):
        return self._credentials

    @property
    def is_prepared(self):
        return self._is_prepared

    def get_known_host(self, host, port=22, knownhost_salt=None):
        # Inspired by https://github.dev/ParallelSSH/ssh2-python/blob/692bbbf0d8f4be6256a8c3fb0c7d20a99c6fd095/examples/example_host_key_verification.py#L17
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if isinstance(port, str):
            port = int(port)
        sock.connect((host, port))
        known_host = None
        try:
            session = Session()
            session.handshake(sock)
            # Retrieve the host key
            host_key, key_type = session.hostkey()
            server_type_type = None
            if key_type == LIBSSH2_HOSTKEY_TYPE_RSA:
                server_type_type = LIBSSH2_KNOWNHOST_KEY_SSHRSA
            if key_type == LIBSSH2_HOSTKEY_TYPE_ECDSA_256:
                server_type_type = LIBSSH2_KNOWNHOST_KEY_ECDSA_256
            if key_type == LIBSSH2_HOSTKEY_TYPE_ECDSA_384:
                server_type_type = LIBSSH2_KNOWNHOST_KEY_ECDSA_384
            if key_type == LIBSSH2_HOSTKEY_TYPE_ECDSA_521:
                server_type_type = LIBSSH2_KNOWNHOST_KEY_ECDSA_521
            if key_type == LIBSSH2_HOSTKEY_TYPE_ED25519:
                server_type_type = LIBSSH2_KNOWNHOST_KEY_ED25519

            if knownhost_salt:
                host_format = LIBSSH2_KNOWNHOST_TYPE_SHA1
                key_format = LIBSSH2_KNOWNHOST_KEYENC_BASE64
            else:
                host_format = LIBSSH2_KNOWNHOST_TYPE_PLAIN
                key_format = LIBSSH2_KNOWNHOST_KEYENC_RAW

            type_mask = key_format | host_format | server_type_type
            # encoded_hostkey = b64encode(host_key)
            known_host = session.knownhost_init()
        except Exception as err:
            print("Failed to get known host: {}".format(err))
        finally:
            sock.close()
        if not known_host:
            return None

        # https://www.ibm.com/docs/en/zos/2.4.0?topic=daemon-ssh-known-hosts-file-format
        if str(port) != "22":
            known_hostname = bytes("[{}]:{}".format(host, port), encoding="utf-8")
        else:
            known_hostname = bytes(host, encoding="utf-8")

        salt = None
        if host_format == LIBSSH2_KNOWNHOST_TYPE_SHA1:
            known_hostname = base64.b64encode(known_hostname)
            # Salt must also be base64 encoded
            salt = base64.b64encode(bytes(knownhost_salt, encoding="utf-8"))

        if key_format == LIBSSH2_KNOWNHOST_KEYENC_BASE64:
            if not isinstance(host_key, bytes):
                host_key = bytes(host_key, encoding="utf-8")
            host_key = base64.b64encode(host_key)

        entry = known_host.addc(known_hostname, host_key, type_mask, salt=salt)
        # https://github.com/ParallelSSH/ssh2-python/blob/692bbbf0d8f4be6256a8c3fb0c7d20a99c6fd095/libssh2/libssh2/src/knownhost.c#L997-L998
        # The only place where I could find where the bitwise & is used to resolve/write-out the host key type
        # Comes in the format b'ip algorithm key\n'
        known_host_write_line = known_host.writeline(entry).decode("utf-8")
        return SSHKnownHost(*known_host_write_line.split(" "))

    def prepare(self, endpoint, port=22, knownhost_salt=None):
        # Get the host key of the target endpoint
        ssh_known_host = self.get_known_host(
            endpoint, port=port, knownhost_salt=knownhost_salt
        )
        if not ssh_known_host:
            return False
        if str(ssh_known_host) not in self.get_known_hosts():
            if self.add_to_known_hosts(ssh_known_host):
                self._is_prepared = True
        else:
            self._is_prepared = True
        return self.is_prepared

    def authenticate(self, session):
        # Ensure that libssh2 receives the correct types
        if not self._credentials.password:
            passphrase = ""
        else:
            if not isinstance(self._credentials.password, str):
                passphrase = str(self._credentials.password)
            else:
                passphrase = self._credentials.password
        # Use private key authentication if a private key is provided
        if self._credentials.private_key:
            if self._credentials.public_key:
                if isinstance(self._credentials.public_key, str):
                    publickeyfiledata = bytes(
                        self._credentials.public_key, encoding="utf-8"
                    )
                elif isinstance(self._credentials.public_key, bytes):
                    publickeyfiledata = self._credentials.public_key
                else:
                    raise TypeError("public_key must be a string or bytes")
            else:
                publickeyfiledata = None
            session.userauth_publickey_frommemory(
                self._credentials.username,
                bytes(self._credentials.private_key, encoding="utf-8"),
                passphrase=passphrase,
                publickeyfiledata=publickeyfiledata,
            )
        elif self._credentials.private_key_file:
            session.userauth_publickey_fromfile(
                self._credentials.username,
                self._credentials.private_key_file,
                passphrase=passphrase,
                publickey=self._credentials.public_key_file,
            )
        elif self._credentials.password and passphrase:
            session.userauth_password(self._credentials.username, passphrase)
        else:
            raise ValueError("No valid authentication method found")
        return True

    def cleanup(self, endpoint):
        credentials_removed = self.remove_credentials()
        known_host_removed = self.remove_from_known_hosts(endpoint)

        if credentials_removed and known_host_removed:
            self._credentials = None
            self._is_prepared = False
            return True
        return False

    def add_to_authorized(self, path=None):
        if not path:
            path = os.path.join(os.path.expanduser("~"), ".ssh", "authorized_keys")
        authorized_str = "{public_key}\n".format(public_key=self.credentials.public_key)
        lock_path = f"{path}_lock"
        try:
            authorized_lock = acquire_lock(lock_path)
            if write(path, authorized_str, mode="a"):
                return True
        except Exception as err:
            print("Failed to add to authorized_keys: {}".format(err))
        finally:
            release_lock(authorized_lock)
        return False

    def get_authorized(self, path=None):
        if not path:
            path = os.path.join(os.path.expanduser("~", ".ssh", "authorized_keys"))
        content = [key.replace("\n", "") for key in load(path, readlines=True)]
        return content

    def remove_from_authorized(self, path=None):
        if not path:
            path = os.path.join(os.path.expanduser("~"), ".ssh", "authorized_keys")
        lock_path = f"{path}_lock"
        try:
            authorized_lock = acquire_lock(lock_path)
            if not remove_content_from_file(path, self.credentials.public_key):
                return False
        except Exception as err:
            print("Failed to remove from authorized_keys: {}".format(err))
        finally:
            release_lock(authorized_lock)
        return True

    def add_to_known_hosts(self, ssh_known_host):
        path = os.path.join(os.path.expanduser("~"), ".ssh", "known_hosts")
        lock_path = f"{path}_lock"
        known_host_str = f"{ssh_known_host}"
        try:
            known_hosts_lock = acquire_lock(lock_path)
            if write(path, known_host_str, mode="+a"):
                return True
        except Exception as err:
            print("Failed to add to known_hosts: {}".format(err))
        finally:
            release_lock(known_hosts_lock)
        return False

    def get_known_hosts(self, path=None):
        if not path:
            path = os.path.join(os.path.expanduser("~"), ".ssh", "known_hosts")
        return load(path, readlines=True)

    def remove_from_known_hosts(self, endpoint):
        path = os.path.join(os.path.expanduser("~"), ".ssh", "known_hosts")
        lock_path = "{}_lock".format(path)
        try:
            known_hosts_lock = acquire_lock(lock_path)
            if not remove_content_from_file(path, endpoint):
                return False
        except Exception as err:
            print("Failed to remove from known_hosts: {}".format(err))
        finally:
            release_lock(known_hosts_lock)
        return True

    def store_credentials(self):
        return self.credentials.store()

    def remove_credentials(self):
        return self.credentials.remove()

    @staticmethod
    def existing_credentials(**kwargs):
        return SSHCredentials.exists(**kwargs)


class SSHCredentials:
    def __init__(
        self,
        username=None,
        password=None,
        private_key=None,
        private_key_file=None,
        public_key=None,
        public_key_file=None,
        certificate=None,
        certificate_file=None,
        store_credentials=False,
    ):
        self._username = username
        self._password = password
        self._private_key = private_key
        self._private_key_file = private_key_file
        self._public_key = public_key
        self._public_key_file = public_key_file
        self._certificate = certificate
        self._certificate_file = certificate_file
        if store_credentials:
            self.store()

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, username):
        self._username = username

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = password

    @property
    def private_key(self):
        return self._private_key

    @private_key.setter
    def private_key(self, private_key):
        self._private_key = private_key

    @property
    def private_key_file(self):
        return self._private_key_file

    @private_key_file.setter
    def private_key_file(self, private_key_file):
        self._private_key_file = private_key_file

    @property
    def public_key(self):
        return self._public_key

    @public_key.setter
    def public_key(self, public_key):
        self._public_key = public_key

    @property
    def public_key_file(self):
        return self._public_key_file

    @public_key_file.setter
    def public_key_file(self, public_key_file):
        self._public_key_file = public_key_file

    @property
    def certificate(self):
        return self._certificate

    @certificate.setter
    def certificate(self, certificate):
        self._certificate = certificate

    @property
    def certificate_file(self):
        return self._certificate_file

    @certificate_file.setter
    def certificate_file(self, certificate_file):
        self._certificate_file = certificate_file

    def store(self):
        if self.private_key_file and self.private_key:
            if not write(
                self.private_key_file, self.private_key, mkdirs=True
            ) or not chmod(self.private_key_file, 0o600):
                return False

        if self.public_key_file and self.public_key:
            if not write(
                self.public_key_file, self.public_key, mkdirs=True
            ) or not chmod(self.public_key_file, 0o644):
                return False

        if self.certificate_file and self.certificate:
            if not write(
                self.certificate_file, self.certificate, mkdirs=True
            ) or not chmod(self.certificate_file, 0o644):
                return False
        return True

    def load(self):
        if self.private_key_file:
            self.private_key = load(self.private_key_file)
        if self.public_key_file:
            self.public_key = load(self.public_key_file)
        if self.certificate_file:
            self.certificate_file = load(self.certificate_file)

    def remove(self):
        if self.private_key_file and os.path.exists(self.private_key_file):
            if not remove(self.private_key_file):
                return False
        if self.public_key_file and os.path.exists(self.public_key_file):
            if not remove(self.public_key_file):
                return False
        if self.certificate_file and os.path.exists(self.certificate_file):
            if not remove(self.certificate_file):
                return False
        return True

    @staticmethod
    def exists(
        ssh_dir_path=default_ssh_path,
        key_name="id_rsa",
        check_certificate=False,
        **kwargs,
    ):
        return ssh_credentials_exists(
            ssh_dir_path=ssh_dir_path,
            key_name=key_name,
            check_certificate=check_certificate,
        )


def ssh_credentials_exists(
    ssh_dir_path=default_ssh_path, key_name="id_rsa", check_certificate=False, **kwargs
):
    if not os.path.exists(ssh_dir_path):
        return False

    private_key_file = os.path.join(ssh_dir_path, key_name)
    if not os.path.exists(private_key_file):
        return False

    public_key_file = os.path.join(ssh_dir_path, "{}.pub".format(key_name))
    if not os.path.exists(public_key_file):
        return False

    if check_certificate:
        certificate_file = os.path.join(ssh_dir_path, "{}-cert.pub".format(key_name))
        if not os.path.exists(certificate_file):
            return False
    return True


def gen_ssh_key_pair(
    key_type="ed25519",
    size=4096,
    ssh_dir_path=default_ssh_path,
    key_name="id_ed25519",
    format_output_str=False,
    password="",
):
    generate_key_path = os.path.join(ssh_dir_path, key_name)
    generate_command = [
        "ssh-keygen",
        "-t",
        key_type,
        "-b",
        str(size),
        "-f",
        generate_key_path,
        "-N",
        password,
    ]

    result = run(
        generate_command,
        format_output_str=format_output_str,
    )
    if result["returncode"] == 0:
        return True
    return False


def load_rsa_key_pair(ssh_dir_path=default_ssh_path, key_name="id_rsa"):
    private_key_file = os.path.join(ssh_dir_path, key_name)
    if not os.path.exists(private_key_file):
        return None
    private_key = load(private_key_file)

    public_key_file = os.path.join(ssh_dir_path, "{}.pub".format(key_name))
    if not os.path.exists(public_key_file):
        return None
    public_key = load(public_key_file)
    credential_kwargs = dict(
        private_key=private_key,
        private_key_file=private_key_file,
        public_key=public_key,
        public_key_file=public_key_file,
    )
    return SSHCredentials(**credential_kwargs)


def remove_ssh_credentials(ssh_dir_path=default_ssh_path, key_name="id_rsa"):
    private_key_file = os.path.join(ssh_dir_path, key_name)
    if exists(private_key_file):
        if not remove(private_key_file):
            return False

    public_key_file = os.path.join(ssh_dir_path, "{}.pub".format(key_name))
    if exists(public_key_file):
        if not remove(public_key_file):
            return False
    return True
