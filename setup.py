#!/usr/bin/env python3
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


# Load version
exec(open("autoprotocol/version.py").read())  # pylint: disable=exec-used

# Test Runner (reference: https://docs.pytest.org/en/latest/goodpractices.html)
class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = "--cov=autoprotocol --cov-report=term"  # pylint: disable=attribute-defined-outside-init

    def run_tests(self):
        import shlex

        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


# Test and Documentation dependencies
test_deps = [
    "coverage>=4.5, <5",
    "pre-commit>=2.4, <3",
    "pylint==2.5.2",  # should be consistent with .pre-commit-config.yaml
    "pytest>=5.4, <6",
    "pytest-cov>=2, !=2.8.1",
    "tox>=3.15, <4",
]

doc_deps = [
    "releases>=1.6.3, <2",
    "Sphinx>=2.4, <3",
    "sphinx_rtd_theme>=0.4.3, <1",
    "semantic-version==2.6.0",
    "six>=1.15.0, <2",
]


setup(
    name="autoprotocol",
    url="https://github.com/autoprotocol/autoprotocol-python",
    maintainer="The Autoprotocol Development Team",
    description="Python library for generating Autoprotocol",
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    license="BSD",
    maintainer_email="support@strateos.com",
    version=__version__,  # pylint: disable=undefined-variable
    install_requires=["Pint==0.9"],
    python_requires=">=3.6",
    tests_require=test_deps,
    extras_require={"docs": doc_deps, "test": test_deps},
    cmdclass={"pytest": PyTest},
    packages=["autoprotocol", "autoprotocol.liquid_handle"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
