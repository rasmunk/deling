=========
mig_utils
=========

.. image:: https://travis-ci.org/rasmunk/mig_utils.svg?branch=master
    :target: https://travis-ci.org/rasmunk/mig_utils


A Minimum Intrusion Grid(MiG) utilities python library:
It includes the mig.io module that provides access to MiG Sharelinks through
python by wrapping around (https://github.com/althonos/fs.sshfs) for sshfs
connections.


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
  from mig.io import ErdaShare
  
  # Initialize sharelink
  share = ErdaShare('SHARELINKID')
  
  # List files/dirs in share
  print(share.list())
  
  # Read file directly as string
  print(share.read('tmp'))
  
  # Read file directly as binary
  print(str(share.read_binary('tmp')))
  
  # Get a _io.TextIOWrapper object with automatic close
  with share.open('tmp', 'r') as tmp:
      print(tmp.read())

  # Get a default _io.TextIOWrapper object with manual lifetime
  file = share.open('tmp', 'r')
  print(file.read())
  file.close()

  # Writing strings to a file
  test_string = "Hello There"
  test_num = 42342342
  test_float = 3434.231

  with share.open('write_test', 'w') as w_file:
      w_file.write(test_string)
      w_file.write(str(test_num))
      w_file.write(str(test_float))

  # Writing bytes to a file
  test_binary = b'Hello again'
  test_b_num = (255).to_bytes(1, byteorder=sys.byteorder)
  with share.open('binary_test', 'wb') as b_file:
      b_file.write(test_binary)
      b_file.write(test_b_num)

  # Removing files, likewise for dirs by using share.removedir(path)
  share.remove('writes_test')
  share.remove('binary_test')

