import unittest
from autoprotocol.protocol import Protocol
from autoprotocol.harness import seal_on_store


class CoverSealTestCase(unittest.TestCase):
    def test_sequence_cover_instructions(self):
        p = Protocol()
        cont1 = p.ref("c1", None, "384-pcr", storage="cold_4")
        cont2 = p.ref("c2", None, "384-pcr", storage="cold_4")
        cont3 = p.ref("c3", None, "96-deep", storage="cold_4")
        cont4 = p.ref("c4", None, "micro-1.5", storage="cold_4")
        therm_groups = [
            {
                "cycles": 1,
                "steps": [
                    {
                        "temperature": "37:celsius",
                        "duration": "60:minute"
                    },
                ]
            }
        ]
        p.incubate(cont1, "ambient", duration="1:minute")
        self.assertEqual(p.instructions[0].op, "incubate")
        self.assertEqual(cont1.cover, None)
        p.spin(cont1, acceleration="1000:g", duration="2:minute")
        self.assertEqual(cont1.cover, "universal")
        self.assertEqual(cont2.cover, None)
        p.thermocycle(cont2, groups=therm_groups)

        self.assertEqual(cont2.cover, "ultra-clear")
        p.transfer(cont2.well(0), cont1.well(1), volume="1:microliter")
        self.assertEqual(cont1.cover, None)
        self.assertEqual(cont2.cover, None)
        p.cover(cont2)
        with self.assertRaises(RuntimeError):
            p.thermocycle(cont2, groups=therm_groups)
        p.thermocycle(cont1, groups=therm_groups)
        self.assertEqual(cont1.cover, "ultra-clear")
        p.spin(cont1, acceleration="1000:g", duration="2:minute")
        p.spin(cont2, acceleration="1000:g", duration="2:minute")
        self.assertEqual(cont1.cover, "ultra-clear")
        self.assertEqual(cont2.cover, "universal")
        p.unseal(cont1)
        p.transfer(cont4.well(0), cont3.well(0), "1:microliter")
        p.spin(cont4, acceleration="1000:g", duration="2:minute")
        self.assertEqual(cont4.cover, None)
        with self.assertRaises(TypeError):
            p.thermocycle(cont4, groups=therm_groups)
        seal_on_store(p)
        self.assertEqual(cont1.cover, "ultra-clear")
        self.assertEqual(cont2.cover, "universal")
        self.assertEqual(cont3.cover, "standard")
        self.assertEqual(cont4.cover, None)
