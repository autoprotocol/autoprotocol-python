
import unittest

from autoprotocol.protocol import Protocol, Ref
from autoprotocol.instruction import Instruction, Thermocycle, Incubate, Pipette, Spin
from autoprotocol.container_type import ContainerType
from autoprotocol.container import Container, WellGroup, Well


class ProtocolMultipleExistTestCase(unittest.TestCase):
    def runTest(self):
        p1 = Protocol()
        p2 = Protocol()

        p1.spin("dummy_ref", "2000:rpm", "560:second")
        self.assertEqual(
            len(p2.instructions), 0,
            "incorrect number of instructions in empty protocol",
        )


class ProtocolContainerTypeTestCase(unittest.TestCase):
    def test_container_type(self):
        p = Protocol()
        names = [
            "384-flat",
            "384-pcr",
            "96-flat",
            "96-pcr",
            "96-deep",
            "micro-2.0",
            "micro-1.5",
        ]
        for name in names:
            self.assertIsInstance(
                p.container_type(name),
                ContainerType,
            )

        container = p.container_type("384-flat")
        self.assertIsInstance(
            p.container_type(container),
            ContainerType,
        )

        with self.assertRaises(ValueError):
            p.container_type("111-unknown")


class ProtocolBasicTestCase(unittest.TestCase):
    def runTest(self):
        protocol = Protocol()
        resource = protocol.ref("resource", None, "96-flat", discard=True)
        pcr = protocol.ref("pcr", None, "96-flat", discard=True)
        bacteria = protocol.ref("bacteria", None, "96-flat", discard=True)
        self.assertEqual(len(protocol.as_dict()['refs']), 3, 'incorrect number of refs')
        self.assertEqual(protocol.as_dict()['refs']['resource'], {"new": "96-flat",
                        "discard": True})

        bacteria_wells = WellGroup([bacteria.well("B1"), bacteria.well("C5"),
                                    bacteria.well("A5"), bacteria.well("A1")])

        protocol.distribute(resource.well("A1").set_volume("40:microliter"),
                            pcr.wells_from('A1',5), "5:microliter")
        protocol.distribute(resource.well("A1").set_volume("40:microliter"),
                            bacteria_wells, "5:microliter")

        self.assertEqual(len(protocol.instructions), 1)
        self.assertEqual(protocol.instructions[0].op, "pipette")
        self.assertEqual(len(protocol.instructions[0].groups), 2)

        protocol.incubate(bacteria, "warm_37", "30:minute")

        self.assertEqual(len(protocol.instructions), 2)
        self.assertEqual(protocol.instructions[1].op, "incubate")
        self.assertEqual(protocol.instructions[1].duration, "30:minute")


class ProtocolAppendTestCase(unittest.TestCase):
    def runTest(self):
        p = Protocol()
        self.assertEqual(
            len(p.instructions), 0,
            "should not be any instructions before appending to empty protocol",
        )

        p.append(Spin("dummy_ref", "100:meter/second^2", "60:second"))
        self.assertEqual(
            len(p.instructions), 1,
            "incorrect number of instructions after single instruction append",
        )
        self.assertEqual(
            p.instructions[0].op, "spin",
            "incorrect instruction appended",
        )

        p.append([
                    Incubate("dummy_ref", "ambient", "30:second"),
                    Spin("dummy_ref", "2000:rpm", "120:second")
                ])
        self.assertEqual(
            len(p.instructions), 3,
            "incorrect number of instructions after appending instruction list",
        )
        self.assertEqual(
            p.instructions[1].op, "incubate",
            "incorrect instruction order after list append",
        )
        self.assertEqual(
            p.instructions[2].op, "spin",
            "incorrect instruction at end after list append.",
        )


class RefTestCase(unittest.TestCase):
    def test_assign_init(self):
        ref = Ref("test", None, "96-flat")
        p = Protocol(
            refs=[ref],
        )
        self.assertEqual(
            p.refs,
            {"test": ref},
        )


    def test_slashes_not_allowed(self):
        p = Protocol()
        with self.assertRaises(AssertionError):
            p.ref("test/bar", None, "96-flat", discard=True)
        self.assertEqual(0, len(p.refs))


    def test_duplicates_not_allowed(self):
        p = Protocol()
        p.ref("test", None, "96-flat", discard=True)
        with self.assertRaises(AssertionError):
            p.ref("test", None, "96-flat", storage="cold_20")
        self.assertTrue(p.refs["test"].opts["discard"])
        self.assertFalse("where" in p.refs["test"].opts)


class ThermocycleTestCase(unittest.TestCase):
    def test_thermocycle_append(self):
        t = Thermocycle("plate", [
            { "cycles": 1, "steps": [
                { "temperature": "95:celsius", "duration": "60:second" },
            ] },
            { "cycles": 30, "steps": [
                { "temperature": "95:celsius", "duration": "15:second" },
                { "temperature": "55:celsius", "duration": "15:second" },
                { "temperature": "72:celsius", "duration": "10:second" },
            ] },
            { "cycles": 1, "steps": [
                { "temperature": "72:celsius", "duration": "600:second" },
                { "temperature": "12:celsius", "duration": "120:second" },
            ] },
        ], "20:microliter")
        self.assertEqual(len(t.groups), 3, 'incorrect number of groups')
        self.assertEqual(t.volume, "20:microliter")


    def test_thermocycle_dyes_and_datarefs(self):
        self.assertRaises(ValueError,
                    Thermocycle,
                    "plate",
                    [{"cycles": 1,
                      "steps": [{
                          "temperature": "50: celsius",
                          "duration": "20:minute"
                      }]
                      }],
                    dyes={"FAM": ["A1"]})
        self.assertRaises(ValueError,
                    Thermocycle,
                    "plate",
                    [{"cycles": 1,
                      "steps": [{
                          "temperature": "50: celsius",
                          "duration": "20:minute"
                      }]
                      }],
                    dataref="test_dataref")
        self.assertRaises(ValueError,
                    Thermocycle,
                    "plate",
                    [{"cycles": 1,
                      "steps": [{
                          "temperature": "50: celsius",
                          "duration": "20:minute"
                      }]
                      }],
                    dyes={"ThisDyeIsInvalid": ["A1"]})

    def test_thermocycle_melting(self):
        self.assertRaises(ValueError,
                    Thermocycle,
                    "plate",
                    [{"cycles": 1,
                      "steps": [{
                          "temperature": "50: celsius",
                          "duration": "20:minute"
                      }]
                      }],
                    melting_start = "50:celsius")
        self.assertRaises(ValueError,
                    Thermocycle,
                    "plate",
                    [{"cycles": 1,
                      "steps": [{
                          "temperature": "50: celsius",
                          "duration": "20:minute"
                      }]
                      }],
                    melting_start = "50:celsius",
                    melting_end = "60:celsius",
                    melting_increment = "1:celsius",
                    melting_rate = "2:minute")


class DistributeTestCase(unittest.TestCase):
    def test_distribute_one_well(self):
        p = Protocol()
        c = p.ref("test", None, "96-flat", discard=True)
        p.distribute(c.well(0).set_volume("20:microliter"),
                     c.well(1),
                     "5:microliter")
        self.assertEqual(1, len(p.instructions))
        self.assertEqual("distribute",
                         list(p.as_dict()["instructions"][0]["groups"][0].keys())[0])
        self.assertTrue(5, c.well(1).volume.value)
        self.assertTrue(15, c.well(0).volume.value)


    def test_distribute_multiple_wells(self):
        p = Protocol()
        c = p.ref("test", None, "96-flat", discard=True)
        p.distribute(c.well(0).set_volume("20:microliter"),
                     c.wells_from(1,3),
                     "5:microliter")
        self.assertEqual(1, len(p.instructions))
        self.assertEqual("distribute",
                         list(p.as_dict()["instructions"][0]["groups"][0].keys())[0])
        for w in c.wells_from(1,3):
            self.assertTrue(5, w.volume.value)
        self.assertTrue(5, c.well(0).volume.value)


    def test_fill_wells(self):
        p = Protocol()
        c = p.ref("test", None, "96-flat", discard=True)
        srcs = c.wells_from(1,2).set_volume("100:microliter")
        dests = c.wells_from(7,4)
        p.distribute(srcs, dests, "30:microliter", allow_carryover=True)
        self.assertEqual(2, len(p.instructions[0].groups))

        #track source vols
        self.assertEqual(10, c.well(1).volume.value)
        self.assertEqual(70, c.well(2).volume.value)

        # track dest vols
        self.assertEqual(30, c.well(7).volume.value)
        self.assertIs(None, c.well(6).volume)

        #test distribute from Well to Well
        p.distribute(c.well("A1").set_volume("20:microliter"), c.well("A2"), "5:microliter")
        self.assertTrue("distribute" in p.instructions[-1].groups[-1])


class RefifyTestCase(unittest.TestCase):
    def test_refifying_various(self):
        p = Protocol()
        # refify container
        refs = {"plate": p.ref("test", None, "96-flat", "cold_20")}
        self.assertEqual(p._refify(refs["plate"]), "test")
        # refify dict
        self.assertEqual(p._refify(refs), {"plate": "test"})

        # refify Well
        well = refs["plate"].well("A1")
        self.assertEqual(p._refify(well), "test/0")

        # refify WellGroup
        wellgroup = refs["plate"].wells_from("A2", 3)
        self.assertEqual(p._refify(wellgroup), ["test/1", "test/2", "test/3"])

        # refify other
        s = "randomstring"
        i = 24
        self.assertEqual("randomstring", p._refify(s))
        self.assertEqual(24, p._refify(i))
