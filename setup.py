#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

import codecs
import re
import os

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

lightweight_requirements = [
    'numpy>=1.13',
    'msgpack>=0.6.0',
    'lz4>=2.1.6',
    'aioredis>=1.2.0'
]

setup_requirements = []

test_requirements = ['pytest==4.0.1']

setup(
    author="Jelle Prins",
    author_email='jelle.prins@nelen-schuurmans.nl',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering',
    ],
    description="Asyncio RPC client/server with redis/msgpack/dataclasses",
    entry_points={
    },
    install_requires=lightweight_requirements,
    license="BSD license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='asyncio rpc',
    name='asyncio_rpc',
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests",
                 "__pycache__", "*.__pycache__.*"]),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    extras_require={
    },
    url='https://github.com/nens/asyncio_rpc',
    version=find_version("asyncio_rpc", "__init__.py"),
    zip_safe=False,
)
