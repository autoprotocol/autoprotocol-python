#!/usr/bin/env python3
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand

# Load version
exec(open('autoprotocol/version.py').read())  # pylint: disable=exec-used

# Test Runner (reference: https://docs.pytest.org/en/latest/goodpractices.html)
class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = "--cov=autoprotocol --cov-report=term"

    def run_tests(self):
        import shlex

         # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)

# Test and Documentation dependencies
test_deps = [
    'coverage>=4.5, <5',
    'pylint>=1.9, <2',
    'pytest>=4, <5',
    'pytest-cov>=2, !=2.8.1',
    'tox>=3.7, <4'
]

doc_deps = [
    'releases>=1.5, <2',
    'Sphinx>=1.7, <1.8',
    'sphinx_rtd_theme>=0.4, <1',
    'semantic-version==2.6.0'
]


setup(
    name='autoprotocol',
    url='https://github.com/autoprotocol/autoprotocol-python',
    maintainer='The Autoprotocol Development Team',
    description='Python library for generating Autoprotocol',
    license='BSD',
    maintainer_email="autoprotocol-curators@transcriptic.com",
    version=__version__,  # pylint: disable=undefined-variable
    install_requires=[
        'Pint==0.8.1'
    ],
    python_requires='>=3.5',
    tests_require=test_deps,
    extras_require={
        'docs': doc_deps,
        'test': test_deps
    },
    cmdclass={'pytest': PyTest},
    packages=[
        'autoprotocol',
        'autoprotocol.liquid_handle'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ]
)
