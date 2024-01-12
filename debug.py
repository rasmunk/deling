from mig.io import ERDAShare


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


if __name__ == "__main__":
    share_links_example()
