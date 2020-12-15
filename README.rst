=============================
 Autoprotocol Python Library
=============================

.. image:: https://img.shields.io/pypi/v/autoprotocol.svg?maxAge=86400
   :target: https://pypi.python.org/pypi/autoprotocol
   :alt: PyPI Version

.. image:: https://github.com/autoprotocol/autoprotocol-python/workflows/CI/badge.svg?branch=master
   :target: https://github.com/autoprotocol/autoprotocol-python/actions?query=workflow%3ACI+branch%3Amaster
   :alt: Build Status

.. image:: https://codecov.io/gh/autoprotocol/autoprotocol-python/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/autoprotocol/autoprotocol-python
   :alt: Code Coverage

.. image:: https://img.shields.io/pypi/dm/autoprotocol?logo=pypi
   :target: https://autoprotocol-python.readthedocs.io
   :alt: PyPI - Downloads

.. image:: https://badges.gitter.im/autoprotocol/autoprotocol-python.svg
   :target: https://gitter.im/autoprotocol/autoprotocol-python?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
   :alt: Gitter Chat


Autoprotocol_ is the standard way to express experiments in life science. This repository contains a python library for generating Autoprotocol.

Installation
------------

To work from the latest stable release:

.. code-block:: bash

    pip install autoprotocol

check the the releases_ for more information about the changes that will be downloaded.

Alternatively to get more up-to-date features:

.. code-block:: bash

    git clone https://github.com/autoprotocol/autoprotocol-python
    cd autoprotocol-python
    python setup.py install

check the changelog_ for information about features included on `master` but not yet released.

Building a Protocol
-------------------

A basic protocol is written by declaring :code:`Protocol.ref` objects and acting on them with :code:`Protocol.instruction` methods.

.. code-block:: python

    import json
    from autoprotocol.protocol import Protocol

    # instantiate a protocol object
    p = Protocol()

    # generate a ref
    # specify where it comes from and how it should be handled when the Protocol is done
    plate = p.ref("test pcr plate", id=None, cont_type="96-pcr", discard=True)

    # generate seal and spin instructions that act on the ref
    # some parameters are explicitly specified and others are left to vendor defaults
    p.seal(
        ref=plate,
        type="foil",
        mode="thermal",
        temperature="165:celsius",
        duration="1.5:seconds"
    )
    p.spin(
        ref=plate,
        acceleration="1000:g",
        duration="1:minute"
    )

    # serialize the protocol as Autoprotocol JSON
    print(json.dumps(p.as_dict(), indent=2))

which prints

.. code-block:: json

    {
      "instructions": [
        {
          "op": "seal",
          "object": "test pcr plate",
          "type": "foil",
          "mode": "thermal",
          "mode_params": {
            "temperature": "165:celsius",
            "duration": "1.5:second"
          }
        },
        {
          "op": "spin",
          "object": "test pcr plate",
          "acceleration": "1000:g",
          "duration": "1:minute"
        }
      ],
      "refs": {
        "test pcr plate": {
          "new": "96-pcr",
          "discard": true
        }
      }
    }

Extras
------

Select SublimeText snippets are included with this repository.
To use them copy the :code:`autoprotocol-python SublimeText Snippet` folder to your local Sublime :code:`/Packages/User` directory.

Documentation
-------------

For more information, see the documentation_.

Contributing
------------

For more information, see CONTRIBUTING_.

.. _Autoprotocol: http://www.autoprotocol.org
.. _releases: http://github.com/autoprotocol/autoprotocol-python/releases
.. _changelog: http://autoprotocol-python.readthedocs.io/en/latest/changelog.html
.. _CONTRIBUTING: http://autoprotocol-python.readthedocs.io/en/latest/CONTRIBUTING.html
.. _documentation: http://autoprotocol-python.readthedocs.org/en/latest/
