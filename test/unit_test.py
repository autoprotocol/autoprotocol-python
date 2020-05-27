import pytest
from autoprotocol.unit import Unit, UnitValueError
from decimal import Decimal


class TestUnitType(object):
    def test_input_types(self):
        u1 = Unit("20.1:microliter")
        u2 = Unit(20.1, "microliter")
        u3 = Unit(Decimal("20.1"), "microliter")
        assert u1 == u2 == u3
        assert isinstance(u1.magnitude, Decimal)
        with pytest.raises(UnitValueError):
            Unit(1j, "microliter")


class TestUnitMath(object):
    def test_arithmetic(self):
        u1 = Unit(20, "microliter")
        u2 = Unit(30, "microliter")
        assert Unit(50, "microliter") == u1 + u2
        assert Unit(50, "microliter") == u2 + u1
        assert Unit(-10, "microliter") == u1 - u2
        assert Unit(10, "microliter") == u2 - u1
        assert Unit(600, "microliter") == u2 * u1.magnitude
        assert Unit(600, "microliter") == u2.magnitude * u1
        assert Unit(1.5, "microliter") == u2 / u1.magnitude
        assert Unit(1, "dimensionless") == u2 // u1

    def test_dimensional_arithmetic(self):
        u1 = Unit(200, "microliter")
        u2 = Unit(3, "milliliter")
        assert Unit(3200, "microliter") == u1 + u2
        assert Unit(3.2, "milliliter") == u2 + u1
        assert Unit(-2800, "microliter") == u1 - u2
        assert Unit(2.8, "milliliter") == u2 - u1
        assert Unit(0.6, "milliliter**2") == u2 * u1
        assert Unit(600000, "microliter**2") == u1 * u2
        assert Unit(15, "dimensionless") == u2 / u1
        assert Unit(0.066666667, "dimensionless") == (u1 / u2).round(9)

    def test_comparison(self):
        u1 = Unit(20, "microliter")
        u2 = Unit(30, "microliter")
        u3 = Unit(1, "milliliter")
        assert u1 != u2
        assert u1 == Unit(20, "microliter")
        assert u1 != u2
        assert u1 < u2
        assert u1 <= u2
        assert u1 <= u2
        assert u2 > u1
        assert u1 < u2
        assert u2 >= u1
        assert u3 > u1
        assert u2 < u3

    # pragma pylint: disable=expression-not-assigned
    def test_units_match(self):
        with pytest.raises(ValueError):
            Unit(20, "microliter") + Unit(30, "second")

        with pytest.raises(ValueError):
            Unit(20, "microliter") - Unit(30, "second")

        with pytest.raises(ValueError):
            Unit(20, "microliter") < Unit(30, "second")

    # pragma pylint: enable=expression-not-assigned

    def test_string_repr(self):
        assert "20:microliter" == str(Unit(20, "microliter"))

    def test_fromstring(self):
        assert Unit("20:microliter") == Unit(20, "microliter")
        assert Unit("20:microliter") == Unit("20:microliter")

    def test_string_parsing(self):
        # Test Unit string parsing
        assert Unit(20, "ul") == Unit(20, "microliter")
        assert Unit(20, "microliters") == Unit(20, "microliter")
        assert Unit(20, "uliter") == Unit(20, "microliter")
        assert Unit(20, "microl") == Unit(20, "microliter")
        # Test return of calling Unit on an Unit instance
        assert Unit(Unit(20, "microliter")) == Unit(20, "microliter")

    def test_compound_units(self):
        u1 = Unit(20, "microliter/second")
        u2 = Unit(30, "microliter/second")
        assert u1 < u2
        assert u2 > u1
        assert u1 + u2 == Unit(50, "microliter/second")
        assert u1 - u2 == Unit(-10, "microliter/second")

    def test_conversion(self):
        assert Unit(200, "centimeter").to("meter") == Unit(2, "meter")
        assert Unit(20, "microliter/second").to("liter/hour") == Unit(
            0.072, "liter / hour"
        )
        assert Unit(1000, "microliter").to("milliliter") == Unit(1, "milliliter")

    def test_autoprotocol_format(self):
        # Ensure that string representation follows Autoprotocol specification
        assert str(Unit(4.2, "millisecond")) == "4.2:millisecond"
        assert str(Unit(4.2, "second")) == "4.2:second"
        assert str(Unit(4.2, "minute")) == "4.2:minute"
        assert str(Unit(4.2, "hour")) == "4.2:hour"
        assert str(Unit(4.2, "nanoliter")) == "4.2:nanoliter"
        assert str(Unit(4.2, "microliter")) == "4.2:microliter"
        assert str(Unit(4.2, "milliliter")) == "4.2:milliliter"
        assert str(Unit(4.2, "rpm")) == "4.2:rpm"
        assert str(Unit(4.2, "nanometer")) == "4.2:nanometer"
        assert str(Unit(4.2, "millimeter")) == "4.2:millimeter"
        assert str(Unit(4.2, "celsius")) == "4.2:celsius"
        assert str(Unit(4.2, "nanomole")) == "4.2:nanomole"
        assert str(Unit(4.2, "micromole")) == "4.2:micromole"
        assert str(Unit(4.2, "hertz")) == "4.2:hertz"
        # Ensure powers match same format
        assert str(Unit(2, "millimeter") * Unit(2, "millimeter")) == "4:millimeter^2"

    def test_string_rounding(self):
        # Ensure that string representation is rounded
        assert (
            str(Unit(0.1, "microliter") + Unit(0.2, "microliter")) == "0.3:microliter"
        )
        # Currently we round to 12 decimal places by default
        assert str(Unit(0.1234567890123, "microliter")) == "0.123456789012:microliter"
        assert str(Unit(0.1234567890126, "microliter")) == "0.123456789013:microliter"

    def test_prefixes(self):
        # Test SI prefixes (yotta to yocto)
        assert Unit(2 * 10 ** 15, "femtosecond") == Unit(2, "second")
        assert Unit(2 * 10 ** 12, "picosecond") == Unit(2, "second")
        assert Unit(2 * 10 ** 9, "nanosecond") == Unit(2, "second")
        assert Unit(2 * 10 ** 6, "microsecond") == Unit(2, "second")
        assert Unit(2 * 10 ** 3, "millisecond") == Unit(2, "second")
        assert Unit(2 * 10 ** 2, "centisecond") == Unit(2, "second")
        assert Unit(2 * 10 ** 1, "decisecond") == Unit(2, "second")
        assert Unit(2, "decasecond") == Unit(2 * 10 ** 1, "second")
        assert Unit(2, "hectosecond") == Unit(2 * 10 ** 2, "second")
        assert Unit(2, "kilosecond") == Unit(2 * 10 ** 3, "second")
        assert Unit(2, "megasecond") == Unit(2 * 10 ** 6, "second")
        assert Unit(2, "gigasecond") == Unit(2 * 10 ** 9, "second")
        assert Unit(2, "terasecond") == Unit(2 * 10 ** 12, "second")
        assert Unit(2, "petasecond") == Unit(2 * 10 ** 15, "second")
        assert Unit(2, "exasecond").to("second") == Unit(2 * 10 ** 18, "second")
        assert Unit(2, "zettasecond").to("second") == Unit(2 * 10 ** 21, "second")
        assert Unit(2, "yottasecond").to("second") == Unit(2 * 10 ** 24, "second")
        assert Unit(2 * 10 ** 24, "yoctosecond").to("second") == Unit(2, "second")
        assert Unit(2 * 10 ** 21, "zeptosecond").to("second") == Unit(2, "second")
        assert Unit(2 * 10 ** 18, "attosecond").to("second") == Unit(2, "second")
