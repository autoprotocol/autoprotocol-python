==============
 Contributing
==============

Licensing
---------
Autoprotocol-Python is BSD licensed (see LICENSE_).
Before we can accept your pull request, we require that you sign a CLA (Contributor License Agreement) allowing us to distribute your work under the BSD license.
Email one of the AUTHORS_ or support@transcriptic.com for more details.

Features and Bugs
-----------------
The easiest way to contribute is to fork this repository and submit a pull request.
You can also submit an issue or write an email to us at support@transcriptic.com if you want to discuss ideas or bugs.

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

