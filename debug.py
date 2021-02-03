import os
from mig.io import ERDAShare, IDMCShare


def share_links_example():

    # Sharelinks lib Tutorial

    # ERDA Sharelink example
    print("ERDA")
    # Open connection to a sharelink
    erda_share = ERDAShare("SHARELINKID")
    # List files/dirs in share
    print(erda_share.list())

    with erda_share.open("tmp", "w") as tmp:
        tmp.write("sdfsfsf")

    # Get a _io.SFTPFileHandle object with automatic close
    with erda_share.open("tmp", "r") as tmp:
        print(tmp.read())

    # Get a default _io.SFTPFileHandle object with manual lifetime
    file = erda_share.open("tmp", "r")
    print(file.read())
    file.close()

    # remove file
    erda_share.remove("tmp")

    print("\n")

    # IDMC Sharelink example
    print("IDMC")
    # Open connection to a sharelink
    idmc_share = IDMCShare("SHARELINKID")
    # List files/dirs in share
    print(idmc_share.list())

    # write binary string
    with idmc_share.open("example_write", "wb") as b_tmp:
        b_tmp.write(b"Hello World")

    # Get a _io.SFTPFileHandle object with automatic close
    with idmc_share.open("b_tmp", "rb") as tmp:
        print(tmp.read())

    # Get a default _io.TextIOWrapper object with manual lifetime
    file = idmc_share.open("b_tmp", "rb")
    print(file.read())
    file.close()

    # remove file
    idmc_share.remove("b_tmp")


def download_foam():
    idmc_share = IDMCShare("SHARELINKID")

    data = b"Hello World"

    # List files/dirs in share
    print(idmc_share.list())

    # Write binary string
    with idmc_share.open("example_write", "wb") as _file:
        _file.write(data)

    read_data = None
    # Read the binary string
    with idmc_share.open("example_write", "rb") as _file:
        read_data = _file.read()

    with idmc_share.open("example_write", "ab") as _file:
        _file.write(b"more data\n")

    with idmc_share.open("example_write", "ab") as _file:
        _file.write(b"more data\n")

    with idmc_share.open("example_write", "ab") as _file:
        _file.write(b"Helasdiopmasidon\n")

    timing_dir = "timings"
    output_dir = "initial_porosity_check_bench.csv"

    if not idmc_share.exists(timing_dir):
        idmc_share.mkdir(timing_dir)

    with idmc_share.open(os.path.join(timing_dir, output_dir), "a") as _file:
        _file.write("1610140989.03146,1610141017.2718203,28.240360260009766\n")

    with idmc_share.open(os.path.join(timing_dir, output_dir), "a") as _file:
        _file.write("1610140989.03146,1610141017.2718203,28.240360260009766\n")

    assert data == read_data
    print(idmc_share.list())


if __name__ == "__main__":
    # share_links_example()
    download_foam()
