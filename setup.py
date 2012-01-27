#!/usr/bin/python

from distutils.core import setup

setup(
    name="rpdb",
    version="0.1.2",
    description="Remote debugger based on pdb",
    author="Bertrand Janin",
    author_email="tamentis@neopulsar.org",
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
