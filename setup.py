#!/usr/bin/env python
from setuptools import setup

setup(
    name='autoprotocol',
    url='http://github.com/autoprotocol/autoprotocol-python',
    author='Vanessa Biggers',
    description='Python library for generating Autoprotocol',
    author_email="vanessa@transcriptic.com",
    version='4.0.0',
    test_suite='test',
    install_requires=[
        'Pint>=0.8.0'
    ],
    tests_require=[
        'pytest>=3.0.0,<4.0',
        'coverage>=4.0.3',
        'tox>=2.3.1'
    ],
    packages=['autoprotocol']
)
