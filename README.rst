======
deling
======

.. image:: https://readthedocs.org/projects/deling/badge/?version=latest
    :target: https://deling.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://badge.fury.io/py/deling.svg
    :target: https://badge.fury.io/py/deling

deling is a set of utilities for accessing and writing data across remote data storages.

Installation
------------

Installation from pypi

.. code-block:: sh

    pip install deling

Installation from source

.. code-block:: sh

    git clone https://github.com/rasmunk/deling.git
    cd deling
    make install

Datastores
----------

This package contains a set of datastores for accessing and conducting IO operations against remote data storage systems.
Currently the package supports datastores that can be accessed through the following protocols:

- `SFTP <https://en.wikipedia.org/wiki/SSH_File_Transfer_Protocol>`_
- `SSHFS <https://en.wikipedia.org/wiki/SSHFS>`_

Helper Datastores
-----------------

To ease the use of the datastores, a set of helper datastores are provided. These datastores are wrappers around the basic datastore that have been implemented.
The helper datastores are:

- ERDAShare/ERDASFTPShare which connects to pre-created `ERDA <https://erda.dk>`_ sharelinks.


Additional documentation can be found at `ReadTheDocs <https://deling.readthedocs.io/en/latest/>`_
