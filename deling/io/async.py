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

# from ._io import SFTPStore, SFTPFileHandle
#
#
# class AsyncSFTPFileHandle(SFTPFileHandle):
#
#     def __init__(self, fh, name, flag):
#         super().__init__(fh, name, flag)
#
#     def __iter__(self):
#         return super().__iter__()
#
#     def __next__(self):
#         return super().__next__()
#
#     def __enter__(self):
#         return super().__enter__()
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         super().__exit__(exc_type, exc_val, exc_tb)
#
#     async def close(self):
#         await super().close()
#
#     async def read(self, n: int = -1):
#         return await super().read(n)
#
#     async def write(self, data):
#         await super().write(data)
#
#     async def seek(self, offset):
#         await super().seek(offset)
#
#     async def read_binary(self, n: int = -1):
#         return await super().read_binary(n)
#
#     async def tell(self):
#         return await super().tell()
#
#
# class AsyncSFTPStore(SFTPStore):
#
#     def __init__(self, host=None, username=None, password=None):
#         super().__init__(host, username, password)
#
#     def __enter__(self):
#         return super().__enter__()
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         super().__exit__(exc_type, exc_val, exc_tb)
#
#     async def open(self, path, flag='r'):
#         return await super().open(path, flag)
#
#     async def list(self, path='.'):
#         return await super().list(path)
#
#     async def remove(self, path):
#         await super().remove(path)
#
#     async def close(self):
#         await super().close()
