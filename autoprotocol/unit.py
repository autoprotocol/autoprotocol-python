from __future__ import division, print_function
from pint import UnitRegistry
from pint.quantity import _Quantity
import sys

if sys.version_info[0] >= 3:
    string_type = str
else:
    string_type = basestring

'''
    :copyright: 2016 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''

# Preload UnitRegistry (Use default)
ureg = UnitRegistry()


class Unit(_Quantity):
    """
        A representation of a measure of physical quantities such as length,
        mass, time and volume.
        Uses Pint's Quantity as a base class for implementing units and
        inherits functionalities such as conversions and proper unit
        arithmetic.
        Note that the magnitude is stored as a double-precision float, so
        there are inherent issues when dealing with extremely large/small
        numbers as well as numerical rounding for non-base 2 numbers.

        Usage Examples
            .. code-block:: python

                vol_1 = Unit(10, 'microliter')
                vol_2 = Unit(10, 'liter')
                print(vol_1 + vol_2)

                time_1 = Unit(1, 'second')
                speed_1 = vol_1/time_1
                print (speed_1)
                print (speed_1.to('liter/hour'))

        Output
            .. code-block:: json
                10000010.0:microliter
                10.0:microliter / second
                0.036:liter / hour

    """
    def __new__(cls, value, units=None):
        cls._REGISTRY = ureg
        cls.force_ndarray = False

        # Automatically parse String if no units provided
        if not units and isinstance(value, string_type):
            try:
                value, units = value.split(":")
            except:
                raise ValueError("Incorrect Unit format. When passing a "
                                 "string argument, Unit has to be in "
                                 "\'1:meter\' format.")

        return super(Unit, cls).__new__(cls, float(value), units)

    def __init__(self, value, units=None):
        super(Unit, self).__init__()
        self.unit = self.units.__str__()

    @staticmethod
    def fromstring(s):
        """
        Convert a string representation of a unit into a Unit object.

        Example
        -------

        .. code-block:: python

            Unit.fromstring("10:microliter")

        becomes

        .. code-block:: python

            Unit(10, "microliter")

        Parameters
        ----------
        s : str
            String in the format of "value:unit"

        """
        if isinstance(s, Unit):
            return s
        else:
            return Unit(s)

    def __str__(self):
        return ":".join([str(self._magnitude), self.unit])

    def __repr__(self):
        return "Unit({0}, '{1}')".format(self._magnitude, self._units)
