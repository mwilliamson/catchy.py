#!/usr/bin/env python

import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='catchy',
    version='0.2.0',
    description='Library for caching',
    long_description=read("README"),
    author='Michael Williamson',
    url='http://github.com/mwilliamson/catchy.py',
    packages=['catchy'],
    install_requires=[
        "locket>=0.1.1,<0.2",
    ],
)
