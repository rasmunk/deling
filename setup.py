import os
from setuptools import setup, find_packages

here = os.path.dirname(__file__)


def read(path):
    with open(path, "r") as _file:
        return _file.read()


def read_req(name):
    path = os.path.join(here, name)
    return [req.strip() for req in read(path).splitlines() if req.strip()]


version_ns = {}
with open(os.path.join(here, "version.py")) as f:
    exec(f.read(), {}, version_ns)

long_description = open("README.rst").read()

setup(
    name="deling",
    version=version_ns["__version__"],
    description="A library for accessing and storing data in remote storage systems",
    long_description=long_description,
    author="Rasmus Munk",
    author_email="munk1@live.dk",
    license="MIT",
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
        "Intended Audience :: Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
