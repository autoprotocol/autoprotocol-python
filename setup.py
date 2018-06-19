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
        'Pint==0.8.1'
    ],
    tests_require=[
        'coverage>=4,<5',
        'pylint>=1,<2',
        'pytest>=3,<4',
        'tox>=3,<4'
    ],
    extras_require={
        "docs": [
            "Sphinx>=1.7,<2",
            "sphinx-rtd-theme",
            "releases"
        ]
    },
    packages=[
        'autoprotocol'
    ]
)
