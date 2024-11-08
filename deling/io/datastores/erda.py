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

from deling.authenticators.ssh import SSHAuthenticator
from deling.io.datastores.core import SFTPStore


class ERDA:
    url = "io.erda.dk"


class ERDASFTPShare(SFTPStore):
    def __init__(self, username=None, password=None, port="22"):
        super(ERDASFTPShare, self).__init__(
            ERDA.url,
            port,
            SSHAuthenticator(username=username, password=password),
        )


class ERDAShare(ERDASFTPShare):
    def __init__(self, share_link, port="22"):
        """
        :param share_link:
        This is the sharelink ID that is used to access the datastore,
        an overview over your sharelinks can be found at
        https://erda.dk/wsgi-bin/sharelink.py.
        """
        super(ERDAShare, self).__init__(
            username=share_link, password=share_link, port=port
        )


# class ErdaHome(DataStore):
#     _target = ERDA.url

#     # TODO -> switch over to checking the OPENID session instead of username/password
#     def __init__(self, username, password):
#         """
#         :param username:
#         The username to the users ERDA home directory,
#         as can be found at https://erda.dk/wsgi-bin/settings.py?topic=sftp
#         :param password:
#         Same as user but the speficied password instead
#         """
#         client = SSHFS(ErdaHome._target, user=username, passwd=password)
#         super(ErdaHome, self).__init__(client=client)
