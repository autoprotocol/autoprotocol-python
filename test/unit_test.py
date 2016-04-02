import unittest
from autoprotocol.unit import Unit


class UnitMathTestCase(unittest.TestCase):
    def test_arithmetic(self):
        u1 = Unit(20, 'microliter')
        u2 = Unit(30, 'microliter')
        self.assertEqual(Unit(50, 'microliter'), u1 + u2)
        self.assertEqual(Unit(50, 'microliter'), u2 + u1)
        self.assertEqual(Unit(-10, 'microliter'), u1 - u2)
        self.assertEqual(Unit(10, 'microliter'), u2 - u1)
        self.assertEqual(Unit(600, 'microliter'), u2 * u1._magnitude)
        self.assertEqual(Unit(600, 'microliter'), u2._magnitude * u1)
        self.assertEqual(Unit(1.5, 'microliter'), u2 / u1._magnitude)
        self.assertEqual(Unit(1, 'dimensionless'), u2//u1)

    def test_dimensional_arithmetic(self):
        u1 = Unit(200, 'microliter')
        u2 = Unit(3, 'milliliter')
        # Due to floating point imprecision, use AlmostEqual as the test
        # condition
        eps = Unit(10**-12, 'microliter')
        self.assertAlmostEqual(Unit(3200, 'microliter'), u1 + u2,
                               delta=eps)
        self.assertAlmostEqual(Unit(3.2, 'milliliter'), u2 + u1,
                               delta=eps)
        self.assertAlmostEqual(Unit(-2800, 'microliter'), u1 - u2,
                               delta=eps)
        self.assertAlmostEqual(Unit(2.8, 'milliliter'), u2 - u1,
                               delta=eps)
        self.assertAlmostEqual(Unit(0.6, 'milliliter**2'), u2 * u1,
                               delta=Unit(10**-12, 'milliliter**2'))
        self.assertAlmostEqual(Unit(600000, 'microliter**2'), u1 * u2,
                               delta=Unit(10**-5, 'microliter**2'))
        self.assertAlmostEqual(Unit(15, 'dimensionless'), u2 / u1)
        self.assertAlmostEqual(Unit(0.066666667, 'dimensionless'), u1 / u2)

    def test_comparison(self):
        u1 = Unit(20, 'microliter')
        u2 = Unit(30, 'microliter')
        u3 = Unit(1, 'milliliter')
        self.assertFalse(u1 == u2)
        self.assertTrue(u1 == Unit(20, 'microliter'))
        self.assertTrue(u1 != u2)
        self.assertTrue(u1 < u2)
        self.assertTrue(u1 <= u2)
        self.assertFalse(u1 > u2)
        self.assertTrue(u2 > u1)
        self.assertFalse(u1 >= u2)
        self.assertTrue(u2 >= u1)
        self.assertTrue(u3 > u1)
        self.assertTrue(u2 < u3)

    def test_units_match(self):
        with self.assertRaises(ValueError):
            Unit(20, 'microliter') + Unit(30, 'second')

        with self.assertRaises(ValueError):
            Unit(20, 'microliter') - Unit(30, 'second')

        with self.assertRaises(ValueError):
            Unit(20, 'microliter') < Unit(30, 'second')

    def test_string_repr(self):
        self.assertEqual('20.0:microliter', str(Unit(20, 'microliter')))

    def test_fromstring(self):
        self.assertEqual(Unit.fromstring("20:microliter"),
                         Unit(20, 'microliter'))
        self.assertEqual(Unit.fromstring("20:microliter"),
                         Unit("20:microliter"))

    def test_string_parsing(self):
        # Test Unit string parsing
        self.assertEqual(Unit(20, 'ul'), Unit(20, 'microliter'))
        self.assertEqual(Unit(20, 'microliters'), Unit(20, 'microliter'))
        self.assertEqual(Unit(20, 'uliter'), Unit(20, 'microliter'))
        self.assertEqual(Unit(20, 'microl'), Unit(20, 'microliter'))
        # Test return of calling Unit on an Unit instance
        self.assertEqual(Unit(Unit(20, 'microliter')), Unit(20, 'microliter'))

    def test_compound_units(self):
        u1 = Unit(20, 'microliter/second')
        u2 = Unit(30, 'microliter/second')
        self.assertTrue(u1 < u2)
        self.assertTrue(u2 > u1)
        self.assertEqual(u1+u2, Unit(50, 'microliter/second'))
        self.assertEqual(u1-u2, Unit(-10, 'microliter/second'))

    def test_conversion(self):
        self.assertTrue(Unit(200, 'centimeter').to('meter'),
                        Unit(2, 'meter'))
        self.assertTrue(Unit(20, 'microliter/second').to('liter/hour'),
                        Unit(0.072, 'liter / hour'))
        # Due to floating point imprecision, use AlmostEqual as the test
        # condition
        self.assertAlmostEqual(Unit(1000, 'microliter').to('milliliter'),
                               Unit(1, 'milliliter'),
                               delta=Unit(10**-12, 'milliliter'))

    def test_autoprotocol_format(self):
        # Ensure that string representation follows Autoprotocol specification
        self.assertEqual(str(Unit(4.2, 'millisecond')), '4.2:millisecond')
        self.assertEqual(str(Unit(4.2, 'second')), '4.2:second')
        self.assertEqual(str(Unit(4.2, 'minute')), '4.2:minute')
        self.assertEqual(str(Unit(4.2, 'hour')), '4.2:hour')
        self.assertEqual(str(Unit(4.2, 'nanoliter')), '4.2:nanoliter')
        self.assertEqual(str(Unit(4.2, 'microliter')), '4.2:microliter')
        self.assertEqual(str(Unit(4.2, 'milliliter')), '4.2:milliliter')
        self.assertEqual(str(Unit(4.2, 'rpm')), '4.2:rpm')
        self.assertEqual(str(Unit(4.2, 'nanometer')), '4.2:nanometer')
        self.assertEqual(str(Unit(4.2, 'millimeter')), '4.2:millimeter')
        self.assertEqual(str(Unit(4.2, 'celsius')), '4.2:celsius')
        self.assertEqual(str(Unit(4.2, 'nanomole')), '4.2:nanomole')
        self.assertEqual(str(Unit(4.2, 'micromole')), '4.2:micromole')
        self.assertEqual(str(Unit(4.2, 'hertz')), '4.2:hertz')

    def test_prefixes(self):
        # Test SI prefixes (yotta to yocto)
        self.assertEqual(Unit(2*10**15, 'femtosecond'),
                         Unit(2, 'second'))
        self.assertEqual(Unit(2*10**12, 'picosecond'),
                         Unit(2, 'second'))
        self.assertEqual(Unit(2*10**9, 'nanosecond'),
                         Unit(2, 'second'))
        self.assertEqual(Unit(2*10**6, 'microsecond'),
                         Unit(2, 'second'))
        self.assertEqual(Unit(2*10**3, 'millisecond'),
                         Unit(2, 'second'))
        self.assertEqual(Unit(2*10**2, 'centisecond'),
                         Unit(2, 'second'))
        self.assertEqual(Unit(2*10**1, 'decisecond'),
                         Unit(2, 'second'))
        self.assertEqual(Unit(2, 'decasecond'),
                         Unit(2*10**1, 'second'))
        self.assertEqual(Unit(2, 'hectosecond'),
                         Unit(2*10**2, 'second'))
        self.assertEqual(Unit(2, 'kilosecond'),
                         Unit(2*10**3, 'second'))
        self.assertEqual(Unit(2, 'megasecond'),
                         Unit(2*10**6, 'second'))
        self.assertEqual(Unit(2, 'gigasecond'),
                         Unit(2*10**9, 'second'))
        self.assertEqual(Unit(2, 'terasecond'),
                         Unit(2*10**12, 'second'))
        self.assertEqual(Unit(2, 'petasecond'),
                         Unit(2*10**15, 'second'))
        # Due to float imprecision, direct comparisons for really large/small
        # numbers are not possible, use assertAlmostEqual
        eps = Unit(10**-12, 'second')
        self.assertAlmostEqual(Unit(2, 'exasecond').to('second'),
                               Unit(2*10**18, 'second'), delta=eps)
        self.assertAlmostEqual(Unit(2, 'zettasecond').to('second'),
                               Unit(2*10**21, 'second'), delta=eps)
        self.assertAlmostEqual(Unit(2, 'yottasecond').to('second'),
                               Unit(2*10**24, 'second'), delta=eps)
        self.assertAlmostEqual(Unit(2*10**24, 'yoctosecond').to('second'),
                               Unit(2, 'second'), delta=eps)
        self.assertAlmostEqual(Unit(2*10**21, 'zeptosecond').to('second'),
                               Unit(2, 'second'), delta=eps)
        self.assertAlmostEqual(Unit(2*10**18, 'attosecond').to('second'),
                               Unit(2, 'second'), delta=eps)
