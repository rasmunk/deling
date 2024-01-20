import os
import paramiko
from deling.utils.io import acquire_lock, release_lock, write, remove_content_from_file

default_ssh_path = os.path.join("~", ".ssh")

default_host_key_order = [
    "ssh-ed25519-cert-v01@openssh.com",
    "ssh-rsa-cert-v01@openssh.com",
    "ssh-ed25519",
    "ssh-rsa",
    "ecdsa-sha2-nistp521-cert-v01@openssh.com",
    "ecdsa-sha2-nistp384-cert-v01@openssh.com",
    "ecdsa-sha2-nistp256-cert-v01@openssh.com",
    "ecdsa-sha2-nistp521",
    "ecdsa-sha2-nistp384",
    "ecdsa-sha2-nistp256",
]


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

    def get_host_key(
        self,
        endpoint,
        port=22,
        default_host_key_algos=default_host_key_order,
    ):
        transport = paramiko.transport.Transport("{}:{}".format(endpoint, port))
        transport.start_client()
        # Ensure that we use the same HostKeyAlgorithm order across
        # SSH implementations
        transport.get_security_options().key_types = tuple(default_host_key_algos)
        host_key = transport.get_remote_server_key()
        return host_key

    def prepare(self, endpoint):
        # Get the host key of the target endpoint
        host_key = self.get_host_key(endpoint)
        if self.add_to_known_hosts(endpoint, host_key):
            self._is_prepared = True
        return self.is_prepared

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
        content = [key.replace("\n", "") for key in fileload(path, readlines=True)]
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

    def add_to_known_hosts(self, endpoint, host_key):
        path = os.path.join(os.path.expanduser("~"), ".ssh", "known_hosts")
        lock_path = f"{path}_lock"
        known_host_str = "{endpoint} {key_type} {host_key}\n".format(
            endpoint=endpoint,
            key_type=host_key.get_name(),
            host_key=host_key.get_base64(),
        )
        try:
            known_hosts_lock = acquire_lock(lock_path)
            if write(path, known_host_str, mode="+a"):
                return True
        except Exception as err:
            print("Failed to add to known_hosts: {}".format(err))
        finally:
            release_lock(known_hosts_lock)
        return False

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
            self.private_key = fileload(self.private_key_file)
        if self.public_key_file:
            self.public_key = fileload(self.public_key_file)
        if self.certificate_file:
            self.certificate_file = fileload(self.certificate_file)

    def remove(self):
        if self.private_key_file and os.path.exists(self.private_key_file):
            if not fileremove(self.private_key_file):
                return False
        if self.public_key_file and os.path.exists(self.public_key_file):
            if not fileremove(self.public_key_file):
                return False
        if self.certificate_file and os.path.exists(self.certificate_file):
            if not fileremove(self.certificate_file):
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


def load_ssh_credentials(
    ssh_dir_path=default_ssh_path,
    key_name="id_rsa",
    check_certificate=False,
    size=2048,
    **kwargs,
):
    if not ssh_credentials_exists(
        ssh_dir_path=ssh_dir_path,
        key_name=key_name,
        check_certificate=check_certificate,
        **kwargs,
    ):
        return None

    private_key, public_key = load_rsa_key_pair(
        ssh_dir_path=ssh_dir_path, key_name=key_name
    )
    private_key_file = os.path.join(ssh_dir_path, key_name)
    public_key_file = os.path.join(ssh_dir_path, "{}.pub".format(key_name))

    credential_kwargs = dict(
        private_key=private_key,
        private_key_file=private_key_file,
        public_key=public_key,
        public_key_file=public_key_file,
    )

    if check_certificate:
        certificate_file = os.path.join(ssh_dir_path, "{}-cert.pub".format(key_name))
        certificate = load_certificate(certificate_file)
        if certificate:
            credential_kwargs.update(
                {"certificate_file": certificate_file, "certificate": certificate}
            )

    return SSHCredentials(**credential_kwargs)


def gen_ssh_credentials(
    ssh_dir_path=default_ssh_path,
    key_name="id_rsa",
    size=2048,
    create_certificate=False,
    certificate_kwargs=None,
    **kwargs,
):
    if not certificate_kwargs:
        certificate_kwargs = {}

    private_key, public_key = gen_rsa_ssh_key_pair(size=size)
    private_key_file = os.path.join(ssh_dir_path, key_name)
    public_key_file = os.path.join(ssh_dir_path, "{}.pub".format(key_name))

    credential_kwargs = dict(
        private_key=private_key,
        private_key_file=private_key_file,
        public_key=public_key,
        public_key_file=public_key_file,
    )

    credentials = SSHCredentials(**credential_kwargs)

    # For now the make_certificate function requires that the credentials exists
    # in the FS
    if create_certificate:
        credentials.store()
        if "identity" not in certificate_kwargs:
            certificate_kwargs["identity"] = "UserIdentity"
        certificate_file = os.path.join(ssh_dir_path, "{}-cert.pub".format(key_name))
        if make_certificate(
            certificate_kwargs["identity"], private_key_file, public_key_file
        ):
            credential_kwargs["certificate_file"] = certificate_file
            credential_kwargs["certificate"] = fileload(certificate_file)
            credentials.certificate = credential_kwargs["certificate"]
            credentials.certificate_file = credential_kwargs["certificate_file"]
        else:
            print("Failed to create certificate file: {}".format(certificate_file))
    return credentials


def gen_ssh_credentials(
    ssh_dir_path=default_ssh_path,
    key_name="id_rsa",
    size=2048,
    create_certificate=False,
    certificate_kwargs=None,
    **kwargs,
):
    if not certificate_kwargs:
        certificate_kwargs = {}

    private_key, public_key = gen_rsa_ssh_key_pair(size=size)
    private_key_file = os.path.join(ssh_dir_path, key_name)
    public_key_file = os.path.join(ssh_dir_path, "{}.pub".format(key_name))

    credential_kwargs = dict(
        private_key=private_key,
        private_key_file=private_key_file,
        public_key=public_key,
        public_key_file=public_key_file,
    )

    credentials = SSHCredentials(**credential_kwargs)

    # For now the make_certificate function requires that the credentials exists
    # in the FS
    if create_certificate:
        credentials.store()
        if "identity" not in certificate_kwargs:
            certificate_kwargs["identity"] = "UserIdentity"
        certificate_file = os.path.join(ssh_dir_path, "{}-cert.pub".format(key_name))
        if make_certificate(
            certificate_kwargs["identity"], private_key_file, public_key_file
        ):
            credential_kwargs["certificate_file"] = certificate_file
            credential_kwargs["certificate"] = fileload(certificate_file)
            credentials.certificate = credential_kwargs["certificate"]
            credentials.certificate_file = credential_kwargs["certificate_file"]
        else:
            print("Failed to create certificate file: {}".format(certificate_file))
    return credentials
