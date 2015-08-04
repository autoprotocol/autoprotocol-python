from __future__ import division, print_function
import operator
import sys

'''
    :copyright: 2015 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''


class Unit(object):
    """A representation of a measure of volume, duration, temperature, or
    concentration.

    """
    def __init__(self, value, unit):
        self.value = float(value)
        self.unit = unit

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
            value, unit = s.split(":")
            return Unit(float(value), unit)

    def __str__(self):
        return ":".join([str(self.value), self.unit])

    def __repr__(self):
        return "Unit(%s, %s)" % (self.value, self.unit)

    def _check_type(self, other):
        if not isinstance(other, Unit):
            raise ValueError("Both operands must be of type Unit")
        elif self.unit != other.unit:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))

    def __add__(self, other):
        self._check_type(other)
        return Unit(self.value + other.value, self.unit)

    def __sub__(self, other):
        self._check_type(other)
        return Unit(self.value - other.value, self.unit)

    def __lt__(self, other):
        self._check_type(other)
        return self.value < other.value

    def __le__(self, other):
        self._check_type(other)
        return self.value <= other.value

    def __eq__(self, other):
        self._check_type(other)
        return self.value == other.value

    def __cmp__(self, other):
        self._check_type(other)
        return cmp(self.value, other.value)

    def __mul__(self, other):
        if isinstance(other, Unit):
            print("WARNING: Unit.__mul__ and __div__ only support scalar "
                "multiplication. Converting %s to %f" % (other, other.value),
                file=sys.stderr)
            other = other.value
        return Unit(self.value * other, self.unit)

    __rmul__ = __mul__

    def __div__(self, other):
        if isinstance(other, Unit):
            print("WARNING: Unit.__mul__ and __div__ only support scalar "
                "multiplication. Converting %s to %f" % (other, other.value),
                file=sys.stderr)
            other = other.value
        return Unit(self.value / other, self.unit)

    def __truediv__(self, other):
        return self.__div__(other)

    def __floordiv__(self, other):
        self._check_type(other)
        return Unit(self.value // other.value, self.unit)

    def __iadd__(self,other):
        self._check_type(other)
        return Unit(operator.iadd(self.value,other.value), self.unit)

    def __isub__(self,other):
        self._check_type(other)
        return Unit(operator.isub(self.value,other.value), self.unit)
