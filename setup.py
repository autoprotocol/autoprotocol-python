#!/usr/bin/env python
from setuptools import setup
exec(open('autoprotocol/version.py').read())  # pylint: disable=exec-used

setup(
    name='autoprotocol',
    url='http://github.com/autoprotocol/autoprotocol-python',
    maintainer='The Autoprotocol Development Team',
    description='Python library for generating Autoprotocol',
    license='BSD',
    maintainer_email="autoprotocol-curators@transcriptic.com",
    version=__version__,  # pylint: disable=undefined-variable
    test_suite='test',
    install_requires=[
        'Pint==0.8.1',
        'future==0.16.0'
    ],
    tests_require=[
        'coverage==4.*',
        'pylint==1.*',
        'pytest==4.*',
        'tox==3.*'
    ],
    extras_require={
        "docs": [
            "Sphinx==1.*",
            "sphinx-rtd-theme",
            "releases"
        ]
    },
    packages=[
        'autoprotocol',
        'autoprotocol.liquid_handle'
    ]
)
