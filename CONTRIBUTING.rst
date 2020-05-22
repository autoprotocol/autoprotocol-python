==============
 Contributing
==============

Licensing
---------
Autoprotocol-Python is BSD licensed (see LICENSE_).

Features and Bugs
-----------------
The easiest way to contribute is to fork this repository and submit a pull request.
You can also submit an issue or write an email to us at support@strateos.com if you want to discuss ideas or bugs.

Dev Env Setup
-------------

Installation:
    Minimum Python version supported for development is :code:`v3.6`.

Python Virtual Environment (Optional):
    Use of virtual environment to isolate development environment is
    highly recommended. There are several tools available such as
    conda_ and pyenv_.

Dependencies:
    We recommend first activating your desired virtualenv, then
    installing the dependencies using the snippet below.

.. code-block:: sh

   pip install -e '.[test, docs]'
   pre-commit install

Testing:
    We use tox_ as a runner for managing test environments and
    running our entire suite of tests, including linting and
    documentation, for all supported Python versions.

    However, you may choose to execute tests piecemeal while
    iterating on code development. For that, we use pytest_
    as our test framework for python tests.

.. code-block:: sh

    tox  # Execute the full suite of tests, usually not required
    python setup.py test  # Executing just python tests

Linting and Formatting:
    We use pre-commit_ as our linting and auto-formatting framework.
    Lint is checked with pylint_ and auto-formatting is done with
    black_.
    This is automatically executed as part of the `git commit` and
    `git push` workflows. You may also execute it manually by using
    the snippet below.

.. code-block:: sh

   pre-commit run

Documentation:
    We use sphinx_ for generating documentation.

.. code-block:: bash

   cd docs  # Assuming you're in the root cloned directory
   sphinx-build -W -b html -d tmp/doctrees . tmp/html

Package Structure
-----------------

Protocol_
^^^^^^^^^

- Primary user interface for Autoprotocol Python
- Represent high level abstractions around instructions, refs, and constraints
- Have more situational checks than those in :code:`Builders` or :code:`Instruction`
- Have simple arguments that are as flat as possible, ideally with no nesting
- Don't necessarily have a 1:1 mapping to an :code:`Instruction`
    - a single call may generate multiple :code:`Instruction` instances
    - a complicated, modal :code:`Instruction` may have multiple corresponding :code:`Protocol` methods
    - significantly complex instructions (e.g. :code:`LiquidHandle`) may require parametrization with user-configurable class instances to avoid overloading the :code:`Protocol` method with too many arguments

Builders_
^^^^^^^^^

- Constructors for nested :code:`Instruction` parameters
- Assigned to the :code:`builders` attribute of their corresponding :code:`Instruction`
- Only contain checks that are valid for all instances of their corresponding :code:`Instruction`
- Check the relationship between parameters
    - a modal :code:`Instruction` generally has :code:`mode_params` that depend on the specified mode (e.g. :code:`LiquidHandle` and :code:`Spectrophotometry.groups`)
    - parameters like :code:`shape` are very interdependent, and only certain combinations of :code:`rows`, :code:`columns`, and :code:`format` are physically possible

Instruction_
^^^^^^^^^^^^

- Code analogue of an Autoprotocol Instruction; constructs Instruction JSON
- :code:`__init___` parameters mirror structure of Autoprotocol Instruction
- Only validate the type, structure, and extent of their inputs

.. _LICENSE: http://autoprotocol-python.readthedocs.io/en/latest/LICENSE.html
.. _AUTHORS: http://autoprotocol-python.readthedocs.io/en/latest/AUTHORS.html
.. _Protocol: http://autoprotocol-python.readthedocs.io/en/latest/protocol.html
.. _Builders: http://autoprotocol-python.readthedocs.io/en/latest/builders.html
.. _Instruction: http://autoprotocol-python.readthedocs.io/en/latest/instruction.html
.. _pyenv: https://github.com/pyenv/pyenv#installation
.. _conda: https://docs.conda.io/projects/conda/en/latest/user-guide/install/
.. _tox: https://tox.readthedocs.io/en/latest/
.. _pytest: https://docs.pytest.org/en/latest/
.. _pre-commit: https://pre-commit.com/
.. _pylint: https://www.pylint.org/
.. _black: https://black.readthedocs.io/en/stable/
.. _sphinx: https://www.sphinx-doc.org/en/master/
