import os


def gen_random_file(path, size=1024):
    try:
        with open(path, "wb") as fh:
            fh.write(os.urandom(size))
    except Exception as err:
        print("Failed to generate random file: {} - {}".format(path, err))
        return False
    return True
