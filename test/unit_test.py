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

    def test_str(self):
        self.assertEqual('20.0:microliter', str(Unit(20, 'microliter')))

    def test_fromstring(self):
        self.assertEqual(Unit.fromstring("20:microliter"), Unit(20,'microliter'))
        self.assertEqual(Unit.fromstring("20:microliter"), Unit("20:microliter"))
