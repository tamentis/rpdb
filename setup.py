#!/usr/bin/python3

import os
from distutils.core import setup
from io import open


here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst'), encoding='utf8').read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except IOError:
    README = CHANGES = ''


setup(
    name="rpdb",
    version="0.1.6",
    description="pdb wrapper with remote access via tcp socket",
    long_description=README + "\n\n" + CHANGES,
    author="Bertrand Janin",
    author_email="b@janin.com",
    url="http://tamentis.com/projects/rpdb",
    packages=["rpdb"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
        "Topic :: Software Development :: Debuggers",
    ]
)
