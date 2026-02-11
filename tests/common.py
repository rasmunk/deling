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

import os
import random
from deling.utils.io import hashsum, makedirs, exists

from utils import gen_random_file


class CommonDataStoreTests:
    def setUp(self):
        self.seed = str(random.random())[2:10]

    def test_open_write(self):
        content = "sddsfeqwfiopqiodnqodniasd"
        write_file = "write_file_{}".format(self.seed)
        with self.share.open(write_file, "w") as w_file:
            w_file.write(content)

        with self.share.open(write_file, "r") as r_file:
            read_content = r_file.read()
            self.assertIsInstance(read_content, str)
            self.assertEqual(read_content, content)

        self.assertTrue(self.share.remove(write_file))
        self.assertNotIn(write_file, self.share.listdir())

    def test_open_write_bytes(self):
        content = b"sddsfeqwfiopqiodnqodniasd"
        write_file = "write_file_bytes_{}".format(self.seed)
        with self.share.open(write_file, "wb") as w_file:
            w_file.write(content)

        with self.share.open(write_file, "rb") as r_file:
            read_content = r_file.read()
            self.assertIsInstance(read_content, bytes)
            self.assertEqual(read_content, content)

        self.assertTrue(self.share.remove(write_file))
        self.assertNotIn(write_file, self.share.listdir())

    def test_open_write_bytearray(self):
        content = bytearray("sddsfeqwfiopqiodnqodniasd", "utf-8")
        write_file = "write_file_bytearray_{}".format(self.seed)
        with self.share.open(write_file, "wb") as w_file:
            w_file.write(content)

        with self.share.open(write_file, "rb") as r_file:
            read_content = r_file.read()
            self.assertIsInstance(read_content, bytes)
            self.assertEqual(bytearray(read_content), content)

        self.assertTrue(self.share.remove(write_file))
        self.assertNotIn(write_file, self.share.listdir())

    def test_open_write_int(self):
        content = 42342342
        write_file = "write_file_int_{}".format(self.seed)
        with self.share.open(write_file, "w") as w_file:
            w_file.write(str(content))

        with self.share.open(write_file, "r") as r_file:
            read_content = r_file.read()
            self.assertIsInstance(read_content, str)
            self.assertEqual(int(read_content), content)

        self.assertTrue(self.share.remove(write_file))
        self.assertNotIn(write_file, self.share.listdir())

    def test_open_write_float(self):
        content = 4234.234324
        write_file = "write_file_float_{}".format(self.seed)
        with self.share.open(write_file, "w") as w_file:
            w_file.write(str(content))

        with self.share.open(write_file, "r") as r_file:
            read_content = r_file.read()
            self.assertIsInstance(read_content, str)
            self.assertEqual(float(read_content), content)

        self.assertTrue(self.share.remove(write_file))
        self.assertNotIn(write_file, self.share.listdir())

    def test_directory(self):
        make_directory = "directory_{}".format(self.seed)
        self.assertTrue(self.share.mkdir(make_directory))
        self.assertIn(make_directory, self.share.listdir())
        self.assertTrue(self.share.rmdir(make_directory))
        self.assertNotIn(make_directory, self.share.listdir())

    def test_make_nested_directory(self):
        nested_directory_name = "nested"
        make_nested_directory = "nested_directory_{}".format(self.seed)
        nested_directory = os.path.join(make_nested_directory, nested_directory_name)
        self.assertTrue(self.share.mkdir(nested_directory, recursive=True))
        self.assertIn(make_nested_directory, self.share.listdir())
        self.assertIn(
            nested_directory_name, self.share.listdir(path=make_nested_directory)
        )
        self.assertTrue(self.share.rmdir(nested_directory))
        self.assertNotIn(
            nested_directory_name, self.share.listdir(path=make_nested_directory)
        )
        self.assertTrue(self.share.rmdir(make_nested_directory))
        self.assertNotIn(make_nested_directory, self.share.listdir())

    def test_make_absolute_nested_directory(self):
        first_directory_name = "nested_directory_{}".format(self.seed)
        second_directory_name = "nested"
        absolute_top_dir_path = os.path.join(os.sep, "tmp", "tests")
        make_first_directory = os.path.join(absolute_top_dir_path, first_directory_name)
        make_second_directory = os.path.join(
            make_first_directory, second_directory_name
        )

        self.assertTrue(self.share.mkdir(make_second_directory, recursive=True))
        self.assertIn(first_directory_name, self.share.listdir(absolute_top_dir_path))
        self.assertIn(second_directory_name, self.share.listdir(make_first_directory))
        self.assertTrue(self.share.rmdir(make_second_directory))
        self.assertNotIn(
            second_directory_name, self.share.listdir(make_first_directory)
        )
        self.assertTrue(self.share.rmdir(make_first_directory))
        self.assertNotIn(
            first_directory_name, self.share.listdir(absolute_top_dir_path)
        )

    def test_remove_recursive_directory(self):
        first_directory_name = "remove_nested_directory_{}".format(self.seed)
        second_directory_name = "nested"
        make_directory_path = os.path.join(first_directory_name, second_directory_name)
        self.assertTrue(self.share.mkdir(make_directory_path, recursive=True))
        self.assertIn(first_directory_name, self.share.listdir())
        self.assertIn(second_directory_name, self.share.listdir(first_directory_name))
        self.assertTrue(self.share.rmdir(make_directory_path, recursive=True))
        self.assertNotIn(first_directory_name, self.share.listdir())

    def test_directory_exists(self):
        make_directory = "make_directory_exists_{}".format(self.seed)
        self.assertTrue(self.share.mkdir(make_directory))
        self.assertTrue(self.share.exists(make_directory))
        self.assertTrue(self.share.rmdir(make_directory))
        self.assertFalse(self.share.exists(make_directory))

    def test_touch_file(self):
        touch_file = "touch_file_{}".format(self.seed)
        self.share.touch(touch_file)
        self.assertIn(touch_file, self.share.listdir())
        self.assertEqual(self.share.read(touch_file), "")
        self.assertTrue(self.share.remove(touch_file))
        self.assertNotIn(touch_file, self.share.listdir())

    def test_touch_file_exists(self):
        touch_file_existing = "touch_file_exists_{}".format(self.seed)
        self.assertFalse(self.share.exists(touch_file_existing))
        self.share.touch(touch_file_existing)
        self.assertTrue(self.share.exists(touch_file_existing))
        self.assertIn(touch_file_existing, self.share.listdir())

        self.assertTrue(self.share.remove(touch_file_existing))
        self.assertNotIn(touch_file_existing, self.share.listdir())
        self.assertFalse(self.share.exists(touch_file_existing))

    def test_touch_existing_file(self):
        touch_file_existing = "touch_file_existing_{}".format(self.seed)
        self.share.touch(touch_file_existing)
        self.assertIn(touch_file_existing, self.share.listdir())
        self.assertEqual(self.share.read(touch_file_existing), "")
        # TODO, get the timestamp for the file and compare it
        # after a new touch

        self.share.touch(touch_file_existing)
        self.assertIn(touch_file_existing, self.share.listdir())
        self.assertEqual(self.share.read(touch_file_existing), "")
        self.assertTrue(self.share.remove(touch_file_existing))
        self.assertNotIn(touch_file_existing, self.share.listdir())

    def test_make_file_with_content(self):
        content_file = "content_file_{}".format(self.seed)
        self.assertTrue(self.share.write(content_file, "sddsfsf"))
        self.assertIn(content_file, self.share.listdir())
        self.assertEqual(self.share.read(content_file), "sddsfsf")
        self.assertTrue(self.share.remove(content_file))
        self.assertNotIn(content_file, self.share.listdir())

    def test_overwrite_file(self):
        overwrite_file = "overwrite_file_{}".format(self.seed)
        self.assertTrue(self.share.write(overwrite_file, "sddsfsf"))
        self.assertIn(overwrite_file, self.share.listdir())
        self.assertEqual(self.share.read(overwrite_file), "sddsfsf")
        self.assertTrue(self.share.write(overwrite_file, "sddsfsf"))
        self.assertEqual(self.share.read(overwrite_file), "sddsfsf")
        self.assertTrue(self.share.remove(overwrite_file))
        self.assertNotIn(overwrite_file, self.share.listdir())

    def test_append_file(self):
        append_file = "append_file_{}".format(self.seed)
        self.assertTrue(self.share.write(append_file, "sddsfsf"))
        self.assertIn(append_file, self.share.listdir())
        self.assertEqual(self.share.read(append_file), "sddsfsf")
        self.assertTrue(self.share.append(append_file, "sddsfsf"))
        self.assertEqual(self.share.read(append_file), "sddsfsfsddsfsf")
        self.assertTrue(self.share.remove(append_file))
        self.assertNotIn(append_file, self.share.listdir())

    def test_write_string(self):
        content = "Hello There"
        write_file_string = "write_string_{}".format(self.seed)
        self.assertTrue(self.share.write(write_file_string, content))
        self.assertIn(write_file_string, self.share.listdir())
        self.assertEqual(self.share.read(write_file_string), content)
        self.assertTrue(self.share.remove(write_file_string))
        self.assertNotIn(write_file_string, self.share.listdir())

    def test_write_bytes(self):
        write_bytes_file = "write_bytes_{}".format(self.seed)
        content = b"Hello There"
        self.assertTrue(self.share.write(write_bytes_file, content))
        self.assertIn(write_bytes_file, self.share.listdir())
        self.assertEqual(self.share.read(write_bytes_file, datatype=bytes), content)
        self.assertTrue(self.share.remove(write_bytes_file))
        self.assertNotIn(write_bytes_file, self.share.listdir())

    def test_test_bytearray(self):
        write_bytearray_file = "write_bytearray_{}".format(self.seed)
        content = bytearray("Hello There", "utf-8")
        self.assertTrue(self.share.write(write_bytearray_file, content))
        self.assertIn(write_bytearray_file, self.share.listdir())
        self.assertEqual(
            self.share.read(write_bytearray_file, datatype=bytearray), content
        )
        self.assertTrue(self.share.remove(write_bytearray_file))
        self.assertNotIn(write_bytearray_file, self.share.listdir())

    def test_write_int(self):
        write_int_file = "write_int_{}".format(self.seed)
        content = 42342342
        self.assertTrue(self.share.write(write_int_file, content))
        self.assertIn(write_int_file, self.share.listdir())
        self.assertEqual(int(self.share.read(write_int_file)), content)
        self.assertTrue(self.share.remove(write_int_file))
        self.assertNotIn(write_int_file, self.share.listdir())

    def test_write_float(self):
        write_float_file = "write_float_{}".format(self.seed)
        content = 4234.234324
        self.assertTrue(self.share.write(write_float_file, content))
        self.assertIn(write_float_file, self.share.listdir())
        self.assertEqual(float(self.share.read(write_float_file)), content)
        self.assertTrue(self.share.remove(write_float_file))
        self.assertNotIn(write_float_file, self.share.listdir())

    def test_upload_download_file(self):
        filename = "test_file_{}".format(self.seed)
        tmp_test_dir = os.path.join(os.getcwd(), "tests", "tmp")
        if not exists(tmp_test_dir):
            self.assertTrue(makedirs(tmp_test_dir))
        upload_file = os.path.join(tmp_test_dir, filename)
        # 100 MB
        size = 1024 * 1024 * 100
        self.assertTrue(gen_random_file(upload_file, size=size))
        self.assertTrue(os.path.exists(upload_file))
        upload_hash = hashsum(upload_file)

        self.assertTrue(self.share.upload(upload_file, filename))
        self.assertIn(filename, self.share.listdir())

        download_name = "downloaded_{}".format(filename)
        download_path = os.path.join(tmp_test_dir, download_name)
        self.assertTrue(self.share.download(filename, download_path))
        self.assertTrue(os.path.exists(download_path))
        self.assertEqual(upload_hash, hashsum(download_path))

        self.assertTrue(self.share.remove(filename))
        self.assertNotIn(filename, self.share.listdir())

    def test_remote_copy(self):
        filename = "test_file_{}".format(self.seed)
        tmp_test_dir = os.path.join(os.getcwd(), "tests", "tmp")
        if not exists(tmp_test_dir):
            self.assertTrue(makedirs(tmp_test_dir))
        upload_file = os.path.join(tmp_test_dir, filename)

        size = 1024 * 1024
        self.assertTrue(gen_random_file(upload_file, size=size))
        self.assertTrue(os.path.exists(upload_file))
        upload_hash = hashsum(upload_file)

        self.assertTrue(self.share.upload(upload_file, filename))
        self.assertIn(filename, self.share.listdir())

        self.assertTrue(self.share.copy(filename, filename + "_copy"))

        download_name = "downloaded_{}".format(filename)
        download_path = os.path.join(tmp_test_dir, download_name)
        self.assertTrue(self.share.download(filename + "_copy", download_path))
        self.assertTrue(os.path.exists(download_path))
        self.assertEqual(upload_hash, hashsum(download_path))

        # Remove the original
        self.assertTrue(self.share.remove(filename))
        self.assertNotIn(filename, self.share.listdir())

        # Remove the copy
        self.assertTrue(self.share.remove(filename + "_copy"))
        self.assertNotIn(filename + "_copy", self.share.listdir())


class CommonDataStoreFileHandleTests:
    def setUp(self):
        self.seed = str(random.random())[2:10]
        self.seek_file = "".join(["seek_file", self.seed])
        self.data = "Hello World"
        self.data_bytes = bytes(self.data, "utf-8")
        self.space_offset = 6
        with self.share.open(self.seek_file, "w") as _file:
            _file.write(self.data)

        self.files = [self.seek_file]

    def tearDown(self):
        for f in self.files:
            if self.share.exists(f):
                self.share.remove(f)

        share_content = self.share.listdir()
        for f in self.files:
            self.assertNotIn(f, share_content)
        self.share = None

    def test_seek_offset_whence_0(self):
        # Seek to the absolute position
        # Characters
        whence = 0
        with self.share.open(self.seek_file, "r") as _file:
            content = _file.read()
            self.assertEqual(content, self.data)

            # offset to the middle space
            _file.seek(self.space_offset, whence)
            offset_content = _file.read()
            self.assertEqual(offset_content, "World")

        # binary
        with self.share.open(self.seek_file, "rb") as _file:
            content = _file.read()
            self.assertEqual(content, self.data_bytes)

            # offset to the middle space
            _file.seek(self.space_offset, whence)
            offset_content = _file.read()
            self.assertEqual(offset_content, b"World")

    def test_seek_offset_whence_1(self):
        # Seek relative to the current position
        whence = 1
        # https://docs.python.org/3.2/tutorial/inputoutput.html#methods-of-file-objects
        # Relative seeks from other than the beginning or the end
        # is only allowed in binary mode
        with self.share.open(self.seek_file, "rb") as _file:
            content = _file.read()
            self.assertEqual(content, self.data_bytes)
            # Go to the middle
            _file.seek(self.space_offset)
            # Move forward 3 offsets
            _file.seek(3, whence)

            # Reading the file moves the offset to the end
            end_content = _file.read()
            self.assertEqual(end_content, b"ld")

            # Move back 8 chars from the end
            _file.seek(-8, whence)
            rewind_content = _file.read()
            self.assertEqual(rewind_content, b"lo World")

    def test_seek_offset_whence_2(self):
        # Seek relative to the file end
        whence = 2
        with self.share.open(self.seek_file, "r") as _file:
            content = _file.read()
            self.assertEqual(content, self.data)
            # offset to the end
            # only zero offset of the end is allowed in non-binary modes
            _file.seek(0, whence)
            offset_content = _file.read()
            self.assertEqual(offset_content, "")

        # binary
        with self.share.open(self.seek_file, "rb") as _file:
            content = _file.read()
            self.assertEqual(content, self.data_bytes)
            # offset to the end
            _file.seek(0, whence)
            offset_content = _file.read()
            # Should be empty
            self.assertEqual(offset_content, b"")

            # Binary mode supports non-zero offset relative to the end
            _file.seek(-6, whence)
            end_content = _file.read()
            self.assertEqual(end_content, b" World")
