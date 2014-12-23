from __future__ import division

class Unit(object):
    def __init__(self, value, unit):
        self.value = value
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
        if isinstance(other, Unit) and self.unit == other.unit:
            return Unit(self.value + other.value, self.unit)
        else:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))
    def __sub__(self, other):
        if not isinstance(other, Unit):
            raise ValueError("Both operands must be of type Unit")
        if isinstance(other, Unit) and self.unit == other.unit:
            return Unit(self.value - other.value, self.unit)
        else:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))

    def __cmp__(self, other):
        if not isinstance(other, Unit):
            raise ValueError("Both operands must be of type Unit")
        if not self.unit == other.unit:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))
        return cmp(self.value, other.value)

    def __mul__(self, other):
        if not isinstance(other, Unit):
            raise ValueError("Both operands must be of type Unit")
        if isinstance(other, Unit) and self.unit == other.unit:
            return Unit(self.value * other.value, self.unit)
        else:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))

    def __div__(self, other):
        if not isinstance(other, Unit):
            raise ValueError("Both operands must be of type Unit")
        if isinstance(other, Unit) and self.unit == other.unit:
            return Unit(self.value / other.value, self.unit)
        else:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))

    def __floordiv__(self, other):
        if not isinstance(other, Unit):
            raise ValueError("Both operands must be of type Unit")
        if isinstance(other, Unit) and self.unit == other.unit:
            return Unit(self.value // other.value, self.unit)
        else:
            raise ValueError("unit %s is not %s" % (self.unit, other.unit))
