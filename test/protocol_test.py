import unittest
from autoprotocol.protocol import Protocol, Ref
from autoprotocol.instruction import Instruction, Thermocycle, Incubate, Pipette, Spin
from autoprotocol.container_type import ContainerType
from autoprotocol.container import Container, WellGroup, Well
from autoprotocol.unit import Unit
from autoprotocol.pipette_tools import *
import json


class ProtocolMultipleExistTestCase(unittest.TestCase):
    def runTest(self):
        p1 = Protocol()
        p2 = Protocol()

        p1.spin("dummy_ref", "2000:rpm", "560:second")
        self.assertEqual(len(p2.instructions), 0,
            "incorrect number of instructions in empty protocol")


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
        self.assertEqual(len(p.instructions), 0,
            "should not be any instructions before appending to empty protocol")

        p.append(Spin("dummy_ref", "100:meter/second^2", "60:second"))
        self.assertEqual(len(p.instructions), 1,
            "incorrect number of instructions after single instruction append")
        self.assertEqual(p.instructions[0].op, "spin",
            "incorrect instruction appended")

        p.append([
                    Incubate("dummy_ref", "ambient", "30:second"),
                    Spin("dummy_ref", "2000:rpm", "120:second")
                ])
        self.assertEqual(len(p.instructions), 3,
            "incorrect number of instructions after appending instruction list")
        self.assertEqual(p.instructions[1].op, "incubate",
            "incorrect instruction order after list append")
        self.assertEqual(p.instructions[2].op, "spin",
            "incorrect instruction at end after list append.")


class RefTestCase(unittest.TestCase):
    def test_duplicates_not_allowed(self):
        p = Protocol()
        p.ref("test", None, "96-flat", discard=True)
        with self.assertRaises(RuntimeError):
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
                     c.wells_from(1, 3),
                     "5:microliter")
        self.assertEqual(1, len(p.instructions))
        self.assertEqual("distribute",
                         list(p.as_dict()["instructions"][0]["groups"][0].keys())[0])
        for w in c.wells_from(1, 3):
            self.assertTrue(5, w.volume.value)
        self.assertTrue(5, c.well(0).volume.value)

    def test_fill_wells(self):
        p = Protocol()
        c = p.ref("test", None, "96-flat", discard=True)
        srcs = c.wells_from(1, 2).set_volume("100:microliter")
        dests = c.wells_from(7, 4)
        p.distribute(srcs, dests, "30:microliter", allow_carryover=True)
        self.assertEqual(2, len(p.instructions[0].groups))

        # track source vols
        self.assertEqual(10, c.well(1).volume.value)
        self.assertEqual(70, c.well(2).volume.value)

        # track dest vols
        self.assertEqual(30, c.well(7).volume.value)
        self.assertIs(None, c.well(6).volume)

        # test distribute from Well to Well
        p.distribute(c.well("A1").set_volume("20:microliter"), c.well("A2"), "5:microliter")
        self.assertTrue("distribute" in p.instructions[-1].groups[-1])

    def test_unit_conversion(self):
        p = Protocol()
        c = p.ref("test", None, "96-flat", discard=True)
        with self.assertRaises(RuntimeError):
            with self.assertRaises(ValueError):
                p.distribute(c.well(0).set_volume("100:microliter"), c.well(1), ".0001:liter")
        p.distribute(c.well(0).set_volume("100:microliter"), c.well(1), "200:nanoliter")
        self.assertTrue(str(p.instructions[0].groups[0]["distribute"]["to"][0]["volume"]) == "0.2:microliter")
        p.distribute(c.well(2).set_volume("100:microliter"), c.well(3), ".1:milliliter", new_group=True)
        self.assertTrue(str(p.instructions[-1].groups[0]["distribute"]["to"][0]["volume"]) == "100.0:microliter")


class TransferTestCase(unittest.TestCase):
    def test_single_transfer(self):
        p = Protocol()
        c = p.ref("test", None, "96-flat", discard=True)
        p.transfer(c.well(0), c.well(1), "20:microliter")
        self.assertEqual(Unit(20, "microliter"), c.well(1).volume)
        self.assertEqual(None, c.well(0).volume)
        self.assertTrue("transfer" in p.instructions[-1].groups[-1])

    def test_gt_750uL_transfer(self):
        p = Protocol()
        c = p.ref("test", None, "96-deep", discard=True)
        p.transfer(
            c.well(0),
            c.well(1),
            "1800:microliter"
            )
        self.assertEqual(3, len(p.instructions[0].groups))
        self.assertEqual(
            Unit(750, 'microliter'),
            p.instructions[0].groups[0]['transfer'][0]['volume']
            )
        self.assertEqual(
            Unit(750, 'microliter'),
            p.instructions[0].groups[1]['transfer'][0]['volume']
            )
        self.assertEqual(
            Unit(300, 'microliter'),
            p.instructions[0].groups[2]['transfer'][0]['volume']
            )

    def test_gt_750uL_wellgroup_transfer(self):
        p = Protocol()
        c = p.ref("test", None, "96-deep", discard=True)
        p.transfer(
            c.wells_from(0, 8, columnwise=True),
            c.wells_from(1, 8, columnwise=True),
            '1800:microliter'
            )
        self.assertEqual(
            24,
            len(p.instructions[0].groups)
            )

    def test_transfer_option_propagation(self):
        p = Protocol()
        c = p.ref("test", None, "96-deep", discard=True)
        p.transfer(
            c.well(0),
            c.well(1),
            "1800:microliter",
            aspirate_source=aspirate_source(
                depth("ll_bottom", distance=".004:meter")
                )
            )
        self.assertEqual(
            len(p.instructions[0].groups[0]['transfer'][0]),
            len(p.instructions[0].groups[1]['transfer'][0])
            )
        self.assertEqual(
            len(p.instructions[0].groups[0]['transfer'][0]),
            len(p.instructions[0].groups[2]['transfer'][0])
            )

    def test_max_transfer(self):
        p = Protocol()
        c = p.ref("test", None, "micro-2.0", storage="cold_4")
        p.transfer(c.well(0), c.well(0), "3050:microliter")

    def test_multiple_transfers(self):
        p = Protocol()
        c = p.ref("test", None, "96-flat", discard=True)
        p.transfer(c.wells_from(0, 2), c.wells_from(2, 2), "20:microliter")
        self.assertEqual(c.well(2).volume, c.well(3).volume)
        self.assertEqual(2, len(p.instructions[0].groups))

    def test_one_tip(self):
        p = Protocol()
        c = p.ref("test", None, "96-flat", discard=True)
        p.transfer(c.wells_from(0, 2), c.wells_from(2, 2), "20:microliter",
            one_tip=True)
        self.assertEqual(c.well(2).volume, c.well(3).volume)
        self.assertEqual(1, len(p.instructions[0].groups))

    def test_one_source(self):
        p = Protocol()
        c = p.ref("test", None, "96-flat", discard=True)
        with self.assertRaises(RuntimeError):
            p.transfer(c.wells_from(0, 2),
                   c.wells_from(2, 2), "40:microliter", one_source=True)
        with self.assertRaises(RuntimeError):
            p.transfer(c.wells_from(0, 2).set_volume("1:microliter"),
                       c.wells_from(1, 5), "10:microliter", one_source=True)
        p.transfer(c.wells_from(0, 2).set_volume("50:microliter"),
                   c.wells_from(2, 2), "40:microliter", one_source=True)
        self.assertEqual(2, len(p.instructions[0].groups))
        self.assertFalse(p.instructions[0].groups[0]["transfer"][0]["from"] == p.instructions[0].groups[1]["transfer"][0]["from"])

    def test_unit_conversion(self):
        p = Protocol()
        c = p.ref("test", None, "96-flat", discard=True)
        with self.assertRaises(ValueError):
            p.transfer(c.well(0), c.well(1), "1:liter")
        p.transfer(c.well(0), c.well(1), "200:nanoliter")
        self.assertTrue(str(p.instructions[0].groups[0]['transfer'][0]['volume']) == "0.2:microliter")
        p.transfer(c.well(1), c.well(2), ".5:milliliter", new_group=True)
        self.assertTrue(str(p.instructions[-1].groups[0]['transfer'][0]['volume']) == "500.0:microliter")

class ConsolidateTestCase(unittest.TestCase):
    def test_multiple_sources(self):
        p = Protocol()
        c = p.ref("test", None, "96-flat", discard=True)
        with self.assertRaises(TypeError):
            p.consolidate(c.wells_from(0, 3), c.wells_from(2, 3), "10:microliter")
        with self.assertRaises(ValueError):
            p.consolidate(c.wells_from(0, 3), c.well(4), ["10:microliter"])
        p.consolidate(c.wells_from(0, 3), c.well(4), "10:microliter")
        self.assertEqual(Unit(30, "microliter"), c.well(4).volume)
        self.assertEqual(3, len(p.instructions[0].groups[0]["consolidate"]["from"]))

    def test_one_source(self):
        p = Protocol()
        c = p.ref("test", None, "96-flat", discard=True)
        p.consolidate(c.well(0), c.well(4), "30:microliter")
        self.assertEqual(Unit(30, "microliter"), c.well(4).volume)


class StampTestCase(unittest.TestCase):
    def test_single_transfers(self):
        p = Protocol()
        plate_96_list = []
        for plate_num in range(5):
            plate_name = ("test_96_"+str(plate_num))
            plate_96_list.append(p.ref(plate_name, None, "96-flat", discard=True))
        plate_384_list = []
        for plate_num in range(3):
            plate_name = ("test_384_"+str(plate_num))
            plate_384_list.append(p.ref(plate_name, None, "384-flat", discard=True))
        with self.assertRaises(RuntimeError):
            # Transfer 4 plates
            for pl, q in zip(plate_96_list, [0, 1, 24, 26]):
                p.stamp(pl, plate_384_list[0], "10:microliter", to_quad = q)


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

class OutsTestCase(unittest.TestCase):
    def test_outs(self):
        p = Protocol()
        self.assertFalse('outs' in p.as_dict())
        plate = p.ref("plate", None, "96-pcr", discard=True)
        plate.well(0).set_name("test_well")
        self.assertTrue(plate.well(0).name == "test_well")
        self.assertTrue(list(p.as_dict()['outs'].keys()) == ['plate'])
        self.assertTrue(list(list(p.as_dict()['outs'].values())[0].keys()) == ['0'])
        self.assertTrue(list(p.as_dict()['outs'].values())[0]['0'] == {'name': 'test_well'})
