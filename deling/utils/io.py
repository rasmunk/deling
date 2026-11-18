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
import stat
import fcntl
import yaml
import shutil
import logging


def makedirs(path, **kwargs) -> tuple[bool, str | None]:
    try:
        os.makedirs(path, **kwargs)
        return True, None
    except Exception as err:
        return False, "failed to create directory path: {} - {}".format(
            path, err
        )


def acquire_lock(path, mode=fcntl.LOCK_EX):
    with open(path, "w+") as lock:
        try:
            fcntl.flock(lock.fileno(), mode)
            return True, lock
        except OSError as ioerr:
            return_msg = "failed to acquire lock: {} - {}".format(path, ioerr)
    return_msg = (
        "failed to acquire lock: {} - an unknown error occurred".format(path)
    )
    return False, return_msg


def release_lock(lock, close=True):
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        if close:
            lock.close()
        return True, None
    except Exception as err:
        return (
            False,
            "failed to close file during lock release: {} - {}".format(
                lock, err
            ),
        )


def write(path, content, mode="w", opener=None):
    if opener is None:
        opener = open

    try:
        with opener(path, mode) as fh:
            fh.write(content)
        return True, None
    except Exception as err:
        return False, "failed to save file: {} - {}".format(path, err)


def copy(src, dst):
    try:
        shutil.copy(src, dst)
        return True, None
    except Exception as err:
        return False, "failed to copy file: {} - {}".format(src, err)


def load(path, mode="r", readlines=False, opener=None):
    if opener is None:
        opener = open

    try:
        with opener(path, mode) as fh:
            if readlines:
                return fh.readlines(), None
            return fh.read(), None
    except Exception as err:
        return False, "failed to load file: {} - {}".format(path, err)


def remove(path):
    try:
        if exists(path):
            os.remove(path)
            return True, None
    except Exception as err:
        return False, "failed to remove file: {} - {}".format(path, err)
    return True, "file does not exist: {}".format(path)


def removedirs(path, recursive=False):
    try:
        if exists(path):
            if recursive:
                shutil.rmtree(path)
            else:
                os.removedirs(path)
            return True, None
    except Exception as err:
        return False, "failed to remove directory: {} - {}".format(path, err)
    return False, "directory does not exist: {}".format(path)


def remove_content_from_file(path, content, opener=None):
    if not exists(path):
        return False

    if not content:
        return False

    if not opener:
        opener = open

    lines = []
    with opener(path, "r") as rh:
        lines = rh.readlines()

    with opener(path, "w") as wh:
        for current_line in lines:
            if content not in current_line:
                wh.write(current_line)


def exists(path):
    return os.path.exists(path)


def join(path, *paths):
    return os.path.join(path, *paths)


def chmod(path, mode, **kwargs):
    try:
        os.chmod(path, mode, **kwargs)
        return True, None
    except Exception as err:
        return False, "failed to set permissions: {} on: {} - {}".format(
            mode, path, err
        )


def parse_yaml(fh_or_data) -> [bool, dict | str]:
    try:
        parsed_yaml = yaml.safe_load(fh_or_data)
        return True, parsed_yaml
    except (yaml.reader.ReaderError, yaml.parser.ParserError) as err:
        return False, f"parsing yaml failed - err: {err}"
    return False, "unkown error occured while parsing a yaml filehandle or data"


def dump_yaml(path, data, opener=None) -> [bool, str | None]:
    if opener is None:
        opener = open

    try:
        with opener(path, "w") as fh:
            yaml.dump(data, fh)
        return True, None
    except OSError as err:
        return False, "failed to dump yaml: {} - {}".format(path, err)
    except Exception as err:
        return (
            False,
            f"an error occurred while dumping yaml: {path} - err: {err}",
        )
    return False, f"unknown error occurred while dumping yaml: {path}"


def load_yaml(path, opener=None):
    if opener is None:
        opener = open
    try:
        with opener(path, "r") as fh:
            return parse_yaml(fh)
    except OSError as err:
        return False, f"failed to load yaml path: {path} - err: {err}"
    return False, "unknown error occured while loading a yaml file"


# Read chunks of a file, default to 64KB
def hashsum(path, algorithm="sha1", buffer_size=65536):
    try:
        import hashlib

        hash_algorithm = hashlib.new(algorithm)
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(buffer_size), b""):
                hash_algorithm.update(chunk)
        return hash_algorithm.hexdigest()
    except Exception as err:
        print("Failed to calculate hashsum: {} - {}".format(path, err))
    return False


def touch(path, times=None, opener=None):
    if not opener:
        opener = open

    try:
        with opener(path, "a"):
            os.utime(path, times)
    except Exception as err:
        print("Failed to touch file: {} - {}".format(path, err))
        return False
    return True


def get_path_permissions(path):
    return oct(stat.S_IMODE(os.stat(path).st_mode))
