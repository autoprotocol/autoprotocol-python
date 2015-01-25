from __future__ import division
import operator

'''
    :copyright: 2015 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''

class Unit(object):
    def __init__(self, value, unit):
        self.value = float(value)
        self.unit = unit

    @staticmethod
    def fromstring(s):
        if isinstance(s, Unit):
            return s
        else:
            value, unit = s.split(":")
            return Unit(float(value), unit)

    def __str__(self):
        return ":".join([str(self.value), self.unit])

    def __add__(self, other):
        if not isinstance(other, Unit):
            raise ValueError("Both operands must be of type Unit")
        elif self.unit != other.unit:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))
        else:
            return Unit(self.value + other.value, self.unit)
    def __sub__(self, other):
        if not isinstance(other, Unit):
            raise ValueError("Both operands must be of type Unit")
        elif self.unit != other.unit:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))
        else:
            return Unit(self.value - other.value, self.unit)

    def __cmp__(self, other):
        if not isinstance(other, Unit):
            raise ValueError("Both operands must be of type Unit")
        elif self.unit != other.unit:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))
        return cmp(self.value, other.value)

    def __mul__(self, other):
        if not isinstance(other, Unit):
            raise ValueError("Both operands must be of type Unit")
        elif self.unit != other.unit:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))
        else:
            return Unit(self.value * other.value, self.unit)

    def __div__(self, other):
        if not isinstance(other, Unit):
            raise ValueError("Both operands must be of type Unit")
        elif self.unit != other.unit:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))
        else:
            return Unit(self.value / other.value, self.unit)

    def __floordiv__(self, other):
        if not isinstance(other, Unit):
            raise ValueError("Both operands must be of type Unit")
        elif self.unit != other.unit:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))
        else:
            return Unit(self.value // other.value, self.unit)

    def __iadd__(self,other):
        if not isinstance(other, Unit):
            raise ValueError("Both operands must be of type Unit")
        elif self.unit != other.unit:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))
        else:
            return Unit(operator.iadd(self.value,other.value), self.unit)

    def __isub__(self,other):
        if not isinstance(other, Unit):
            raise ValueError("Both operands must be of type Unit")
        elif self.unit != other.unit:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))
        else:
            return Unit(operator.isub(self.value,other.value), self.unit)
