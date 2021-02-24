"""
Module containing a Units library

    :copyright: 2021 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""

from collections import defaultdict
from decimal import Decimal, InvalidOperation
from math import ceil, floor
from numbers import Number

from pint import UnitRegistry
from pint.errors import UndefinedUnitError
from pint.quantity import _Quantity
from pint.util import UnitsContainer


def to_decimal(number):
    """
    Casts a number to a Decimal safely.

    Parameters
    ----------
    number: Number
        number to be cast to a decimal

    Returns
    -------
    Decimal
        decimal representation of the input number

    Raises
    ------
    ValueError
        Number is not of a type that's castable to decimal
    """
    if isinstance(number, Decimal):
        decimal = number
    elif isinstance(number, Number):
        decimal = Decimal(str(number))
    else:
        raise ValueError(
            f"Tried to cast {number} to decimal but it was of non-numeric type "
            f"{type(number)}."
        )
    return decimal


# pragma pylint: disable=protected-access
class DecimalUnitRegistry(UnitRegistry):
    """
    Redefines builtin UnitRegistry methods for doing conversions to use Decimals
    instead of floats to eliminate floating point imprecision, particularly
    converting .to("new_unit").
    """

    def _get_root_units(self, input_units, check_nonmult=True):
        if not input_units:
            return Decimal("1"), UnitsContainer()

        # The cache is only done for check_nonmult=True
        if check_nonmult and input_units in self._root_units_cache:
            return self._root_units_cache[input_units]

        accumulators = [Decimal("1"), defaultdict(Decimal)]
        self._get_root_units_recurse(input_units, Decimal("1"), accumulators)

        factor = accumulators[0]
        units = UnitsContainer(
            dict((k, v) for k, v in accumulators[1].items() if v != Decimal("0"))
        )

        if check_nonmult:
            for unit in units.keys():
                if not self._units[unit].converter.is_multiplicative:
                    return None, units

        if check_nonmult:
            self._root_units_cache[input_units] = factor, units

        return factor, units

    def _get_root_units_recurse(self, ref, exp, accumulators):
        for key in sorted(ref):
            exp2 = to_decimal(exp) * to_decimal(ref[key])
            key = self.get_name(key)
            reg = self._units[key]
            if reg.is_base:
                accumulators[1][key] += exp2
            else:
                accumulators[0] *= to_decimal(reg._converter.scale) ** exp2
                if reg.reference is not None:
                    self._get_root_units_recurse(reg.reference, exp2, accumulators)


# Preload UnitRegistry (Use default Pints definition file as a base)
_UnitRegistry = DecimalUnitRegistry()

"""Map string representation of Pint units over to Autoprotocol format"""
# Map Temperature Unit names
_UnitRegistry._units["degC"]._name = "celsius"
_UnitRegistry._units["celsius"]._name = "celsius"
_UnitRegistry._units["degF"]._name = "fahrenheit"
_UnitRegistry._units["fahrenheit"]._name = "fahrenheit"
_UnitRegistry._units["degR"]._name = "rankine"
_UnitRegistry._units["rankine"]._name = "rankine"
# Map Speed Unit names
_UnitRegistry._units["revolutions_per_minute"]._name = "rpm"

"""Add support for Molarity Unit"""
_UnitRegistry.define("molar = mole/liter = M")
# pragma pylint: enable=protected-access


class UnitError(Exception):
    """
    Exceptions from creating new Unit instances with bad inputs.
    """

    message_text = "Unit error for %s"

    def __init__(self, value):
        super(UnitError, self).__init__(self.message_text % value)
        self.value = value


class UnitStringError(UnitError):
    message_text = (
        "Invalid format '%s'; when building a Unit from a string "
        "it must be formatted as '1:meter'."
    )


class UnitValueError(UnitError):
    message_text = "Invalid value '%s'; when building a Unit the value must be numeric."


class UnitUnitsError(UnitError):
    message_text = (
        "Invalid value '%s'; when building a Unit "
        "the units must be in the UnitRegistry."
    )


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

    Example
    -------

        .. code-block:: python

            vol_1 = Unit(10, 'microliter')
            vol_2 = Unit(10, 'liter')
            print(vol_1 + vol_2)

            time_1 = Unit(1, 'second')
            speed_1 = vol_1/time_1
            print (speed_1)
            print (speed_1.to('liter/hour'))

    Returns
    -------
    Unit
        unit object

        .. code-block:: none

            10000010.0:microliter
            10.0:microliter / second
            0.036:liter / hour

    """

    def __new__(cls, value, units=None):
        cls._REGISTRY = _UnitRegistry
        cls.force_ndarray = False

        # Automatically return Unit if Unit is provided
        if isinstance(value, Unit):
            return value

        # Automatically parse String if no units provided
        if not units and isinstance(value, str):
            try:
                value, units = value.split(":")
            except ValueError:
                raise UnitStringError(value)
        try:
            return super(Unit, cls).__new__(cls, Decimal(str(value)), units)
        except (ValueError, InvalidOperation):
            raise UnitValueError(value)
        except UndefinedUnitError:
            raise UnitUnitsError(units)

    def __init__(self, value, units=None):  # pylint: disable=unused-argument
        super(Unit, self).__init__()
        self.unit = self.units.__str__()

    def __str__(self, ndigits=12):
        """
        Parameters
        ----------
        ndigits: int, optional
            Number of decimal places to round to, useful for numerical
            precision reasons

        Returns
        -------
        str
            This rounds the string presentation to 12 decimal places by default
            to account for the majority of numerical precision issues
        """
        rounded_magnitude = round(self.magnitude, ndigits)
        normalized_magnitude = to_decimal(rounded_magnitude).normalize()
        unit_repr = self.unit.replace("**", "^").replace(" ", "")
        return f"{normalized_magnitude:f}:{unit_repr:s}"

    def __repr__(self):
        return f"Unit({self.magnitude:f}, '{self.units:s}')"

    def __ceil__(self):
        return self.__class__(ceil(self.magnitude), self.units)

    def __floor__(self):
        return self.__class__(floor(self.magnitude), self.units)

    def _mul_div(self, other, magnitude_op, units_op=None):
        """
        Extends Pint's base _Quantity multiplication/division
        implementation by checking for dimensionality and
        casting Numbers to Decimals
        """
        if isinstance(other, Unit):
            if self.dimensionality == other.dimensionality:
                other = other.to(self.units)
        else:
            other = to_decimal(other)

        return super(Unit, self)._mul_div(other, magnitude_op, units_op)

    def _imul_div(self, other, magnitude_op, units_op=None):
        """
        Extends Pint's base _Quantity multiplication/division
        implementation by checking for dimensionality and
        casting Numbers to Decimals
        """
        if isinstance(other, Unit):
            if self.dimensionality == other.dimensionality:
                other = other.to(self.units)
        else:
            other = to_decimal(other)

        return super(Unit, self)._imul_div(other, magnitude_op, units_op)

    @property
    def magnitude(self):
        return self._magnitude

    @magnitude.setter
    def magnitude(self, magnitude):
        try:
            self._magnitude = to_decimal(magnitude)
        except ValueError:
            raise RuntimeError(
                f"Tried to set Unit's magnitude {magnitude} but it was of type "
                f"{type(magnitude)}. Magnitudes must be numeric."
            )

    @staticmethod
    def fromstring(s):
        return Unit(s)

    def ceil(self):
        """
        Equivalent of math.ceil(Unit) for python 2 compatibility

        Returns
        -------
        Unit
            ceil of Unit
        """
        return self.__ceil__()

    def floor(self):
        """
        Equivalent of math.floor(Unit) for python 2 compatibility

        Returns
        -------
        Unit
            floor of Unit
        """
        return self.__floor__()

    def round(self, ndigits):
        """
        Equivalent of round(Unit) for python 2 compatibility

        Parameters
        ----------
        ndigits: int
            number of decimal places to be rounded to

        Returns
        -------
        Unit
            rounded unit
        """
        return self.__round__(ndigits)
