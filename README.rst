=========
mig_utils
=========

.. image:: https://travis-ci.org/rasmunk/mig_utils.svg?branch=master
    :target: https://travis-ci.org/rasmunk/mig_utils


A Minimum Intrusion Grid(MiG) utilities python library:
It includes the mig.io module that provides access to MiG Sharelinks through
python by wrapping around (https://github.com/althonos/fs.sshfs) for sshfs
connections and (https://github.com/ParallelSSH/ssh2-python.git) for sftp
which is the default and recommended connection


Installation
------------

Installation from pypi

.. code-block:: sh

    pip install mig-utils


Installation from a local git repository

.. code-block:: sh

    cd mig-utils
    pip install .


IO Example
----------

ERDA (https://erda.dk) sharelink access with python3 example.
A likewise sharelink class (IdmcShare) exists for IDMC (https://idmc.dk)

.. code-block:: python

  # First import the class that gives you access to the share in question*
  from mig.io import ERDAShare, IDMCShare

    # ERDA Sharelink example
    print("ERDA")
    # Open connection to a sharelink
    erda_share = ERDAShare('SHARELINKID')
    # List files/dirs in share
    print(erda_share.list())

    with erda_share.open('tmp', 'w') as tmp:
        tmp.write("sdfsfsf")

    # Get a _io.SFTPFileHandle object with automatic close
    with erda_share.open('tmp', 'r') as tmp:
        print(tmp.read())

    # Get a default _io.SFTPFileHandle object with manual lifetime
    file = erda_share.open('tmp', 'r')
    print(file.read())
    file.close()

    # remove file
    erda_share.remove('tmp')

    print("\n")

    # IDMC Sharelink example
    print("IDMC")
    # Open connection to a sharelink
    idmc_share = IDMCShare('SHARELINKID')
    # List files/dirs in share
    print(idmc_share.list())

    # write binary string
    with idmc_share.open('b_tmp', 'wb') as b_tmp:
        b_tmp.write(b'sadasdasd')

    # Get a _io.SFTPFileHandle object with automatic close
    with idmc_share.open('b_tmp', 'rb') as tmp:
        print(tmp.read())

    # Get a default _io.TextIOWrapper object with manual lifetime
    file = idmc_share.open('b_tmp', 'rb')
    print(file.read())
    file.close()

