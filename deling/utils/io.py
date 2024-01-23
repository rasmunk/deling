import os
import fcntl
import yaml
import shutil


def makedirs(path):
    try:
        os.makedirs(path)
        return True
    except Exception as err:
        print("Failed to create directory path: {} - {}".format(path, err))
    return False


def acquire_lock(path, mode=fcntl.LOCK_EX):
    lock = open(path, "w+")
    try:
        fcntl.flock(lock.fileno(), mode)
    except IOError as ioerr:
        print("Failed to acquire lock: {} - {}".format(path, ioerr))
        # Clean up
        try:
            lock.close()
        except Exception as err:
            print("Failed to close lock after failling to acquire it: {}".format(err))
    return lock


def release_lock(lock, close=True):
    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    if close:
        try:
            lock.close()
        except Exception as err:
            print("Failed to close file during lock release: {} - {}".format(lock, err))


def write(path, content, mode="w", mkdirs=False, opener=None):
    if not opener:
        opener = open

    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path) and mkdirs:
        if not makedirs(dir_path):
            return False
    try:
        with opener(path, mode) as fh:
            fh.write(content)
        return True
    except Exception as err:
        print("Failed to save file: {} - {}".format(path, err))
    return False


def copy(src, dst):
    try:
        shutil.copy(src, dst)
        return True
    except Exception as err:
        print("Failed to copy file: {} - {}".format(src, err))
    return False


def load(path, mode="r", readlines=False, opener=None):
    if not opener:
        opener = open

    try:
        with opener(path, mode) as fh:
            if readlines:
                return fh.readlines()
            return fh.read()
    except Exception as err:
        print("Failed to load file: {} - {}".format(path, err))
    return False


def remove(path):
    try:
        if os.path.exists(path):
            os.remove(path)
            return True
    except Exception as err:
        print("Failed to remove file: {} - {}".format(path, err))
    return False


def removedirs(path, recursive=False):
    try:
        if os.path.exists(path):
            os.removedirs(path)
            return True
    except Exception as err:
        print("Failed to remove directory: {} - {}".format(path, err))
    return False


def remove_content_from_file(path, content, opener=None):
    if not os.path.exists(path):
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
    except Exception as err:
        print("Failed to set permissions: {} on: {} - {}".format(mode, path, err))
        return False
    return True


def parse_yaml(data):
    try:
        parsed = yaml.safe_load(data)
        return parsed
    except yaml.reader.ReaderError as err:
        print("Failed to parse yaml: {}".format(err))
    return False


def dump_yaml(path, data, opener=None):
    if not opener:
        opener = open

    try:
        with opener(path, "w") as fh:
            yaml.dump(data, fh)
        return True
    except IOError as err:
        print("Failed to dump yaml: {} - {}".format(path, err))
    return False


def load_yaml(path, opener=None):
    if not opener:
        opener = open
    try:
        with opener(path, "r") as fh:
            return yaml.safe_load(fh)
    except IOError as err:
        print("Failed to load yaml: {} - {}".format(path, err))
    return False


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
