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
from setuptools import setup, find_packages

cur_dir = os.path.abspath(os.path.dirname(__file__))


def read(path):
    with open(path, "r") as _file:
        return _file.read()


def read_req(name):
    path = os.path.join(cur_dir, name)
    return [req.strip() for req in read(path).splitlines() if req.strip()]


# Get the current package version.
version_ns = {}
version_path = os.path.join(cur_dir, "deling", "_version.py")
version_content = read(version_path)
exec(version_content, {}, version_ns)

long_description = open("README.rst").read()

setup(
    name="deling",
    version=version_ns["__version__"],
    description="A library for accessing and storing data in remote storage systems",
    long_description=long_description,
    author="Rasmus Munk",
    author_email="munk1@live.dk",
    license="GNU General Public License v2 (GPLv2)",
    keywords="Data IO, Staging data, Data transfer, Data storage, Data management",
    url="https://github.com/rasmunk/deling",
    packages=find_packages(),
    install_requires=read_req("requirements.txt"),
    extras_require={
        "test": read_req("tests/requirements.txt"),
        "dev": read_req("requirements-dev.txt"),
    },
    project_urls={"Source Code": "https://github.com/rasmunk/deling"},
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
