import pytest
from autoprotocol.container import Container, WellGroup
from autoprotocol.instruction import Thermocycle, Incubate, Spin
from autoprotocol.pipette_tools import *  # NOQA
from autoprotocol.protocol import Protocol, Ref
from autoprotocol.unit import Unit, UnitError
from autoprotocol.harness import _add_dye_to_preview_refs, \
    _convert_provision_instructions, _convert_dispense_instructions


class TestProtocolMultipleExist():

    def test_multiple_exist(self, dummy_protocol, dummy_96):
        p1 = dummy_protocol
        p2 = Protocol()

        p1.cover(dummy_96)
        p1.incubate(dummy_96, "warm_37", "560:second")
        assert (len(p2.instructions) == 0)
        assert (len(p1.instructions) == 2)


class TestProtocolBasic():

    def test_basic_protocol(self, dummy_protocol):
        protocol = dummy_protocol
        resource = protocol.ref("resource", None, "96-flat", discard=True)
        pcr = protocol.ref("pcr", None, "96-flat", discard=True)
        bacteria = protocol.ref("bacteria", None, "96-flat", discard=True)
        # Test for correct number of refs
        assert (len(protocol.as_dict()['refs']) == 3)
        assert (protocol.as_dict()['refs']['resource'] ==
                {"new": "96-flat", "discard": True})

        bacteria_wells = WellGroup([bacteria.well("B1"), bacteria.well("C5"),
                                    bacteria.well("A5"), bacteria.well("A1")])

        protocol.distribute(resource.well("A1").set_volume("40:microliter"),
                            pcr.wells_from('A1', 5), "5:microliter")
        protocol.distribute(resource.well("A1").set_volume("40:microliter"),
                            bacteria_wells, "5:microliter")

        assert (len(protocol.instructions) == 1)
        assert (protocol.instructions[0].op == "pipette")
        assert (len(protocol.instructions[0].groups) == 2)

        protocol.incubate(bacteria, "warm_37", "30:minute")

        assert (len(protocol.instructions) == 3)
        assert (protocol.instructions[1].op == "cover")
        assert (protocol.instructions[2].op == "incubate")
        assert (protocol.instructions[2].duration == "30:minute")


class TestProtocolAppend:

    def test_protocol_append(self, dummy_protocol):
        p = dummy_protocol
        # assert empty list of instructions
        assert (len(p.instructions) == 0)

        p.append(Spin("dummy_ref", "100:meter/second^2", "60:second"))
        assert (len(p.instructions) == 1)
        assert(p.instructions[0].op == "spin")

        p.append([
            Incubate("dummy_ref", "ambient", "30:second"),
            Spin("dummy_ref", "2000:rpm", "120:second")
        ])
        assert (len(p.instructions) == 3)
        assert (p.instructions[1].op == "incubate")
        assert (p.instructions[2].op == "spin")


class TestRef:

    def test_duplicates_not_allowed(self, dummy_protocol):
        p = dummy_protocol
        p.ref("test", None, "96-flat", discard=True)
        with pytest.raises(RuntimeError):
            p.ref("test", None, "96-flat", storage="cold_20")
        assert (p.refs["test"].opts["discard"])
        assert ("where" not in p.refs["test"].opts)

    def test_storage_condition_change(self, dummy_protocol):
        p = dummy_protocol
        c1 = p.ref("discard_test", None, "micro-2.0", storage="cold_20")
        assert (
            p.refs["discard_test"].opts["store"]["where"] == "cold_20")
        with pytest.raises(KeyError):
            p.as_dict()["refs"]["discard_test"]["discard"]
        c1.discard()
        assert (p.as_dict()["refs"]["discard_test"]["discard"])
        with pytest.raises(KeyError):
            p.as_dict()["refs"]["discard_test"]["store"]
        c1.set_storage("cold_4")
        assert (
            p.as_dict()["refs"]["discard_test"]["store"]["where"] == "cold_4")


class TestThermocycle:

    def test_thermocycle_append(self):
        t = Thermocycle("plate", [
            {"cycles": 1, "steps": [
                {"temperature": "95:celsius", "duration": "60:second"},
            ]},
            {"cycles": 30, "steps": [
                {"temperature": "95:celsius", "duration": "15:second"},
                {"temperature": "55:celsius", "duration": "15:second"},
                {"temperature": "72:celsius", "duration": "10:second"},
            ]},
            {"cycles": 1, "steps": [
                {"temperature": "72:celsius", "duration": "600:second"},
                {"temperature": "12:celsius", "duration": "120:second"},
            ]},
        ], "20:microliter")
        # Test for correct number of groups
        assert (len(t.groups) == 3)
        assert (t.volume == "20:microliter")

    def test_thermocycle_dyes_and_datarefs(self):
        pytest.raises(ValueError,
                      Thermocycle,
                      "plate",
                      [{"cycles": 1,
                        "steps": [{
                            "temperature": "50: celsius",
                            "duration": "20:minute"
                        }]
                        }],
                      dyes={"FAM": ["A1"]})
        pytest.raises(ValueError,
                      Thermocycle,
                      "plate",
                      [{"cycles": 1,
                        "steps": [{
                            "temperature": "50: celsius",
                            "duration": "20:minute"
                        }]
                        }],
                      dataref="test_dataref")
        pytest.raises(ValueError,
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
        pytest.raises(ValueError,
                      Thermocycle,
                      "plate",
                      [{"cycles": 1,
                        "steps": [{
                            "temperature": "50: celsius",
                            "duration": "20:minute"
                        }]
                        }],
                      melting_start="50:celsius")
        pytest.raises(ValueError,
                      Thermocycle,
                      "plate",
                      [{"cycles": 1,
                        "steps": [{
                            "temperature": "50: celsius",
                            "duration": "20:minute"
                        }]
                        }],
                      melting_start="50:celsius",
                      melting_end="60:celsius",
                      melting_increment="1:celsius",
                      melting_rate="2:minute")


class TestDistribute():

    def test_distribute_one_well(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        p.distribute(c.well(0).set_volume("20:microliter"),
                     c.well(1),
                     "5:microliter")
        assert (1 == len(p.instructions))
        assert (
            "distribute" ==
            list(p.as_dict()["instructions"][0]["groups"][0].keys())[0])
        assert (Unit(5, 'microliter') == c.well(1).volume)
        assert (Unit(15, 'microliter') == c.well(0).volume)

    def test_uncover_before_distribute(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        p.cover(c)
        p.distribute(c.well(0).set_volume("20:microliter"),
                     c.well(1),
                     "5:microliter")
        assert (3 == len(p.instructions))
        assert ("distribute" ==
                list(p.as_dict()["instructions"][-1]["groups"][0].keys())[0])
        assert (Unit(5, "microliter") == c.well(1).volume)
        assert (Unit(15, "microliter") == c.well(0).volume)
        assert (p.instructions[-2].op == "uncover")
        assert (not c.cover)

    def test_distribute_multiple_wells(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        p.distribute(c.well(0).set_volume("20:microliter"),
                     c.wells_from(1, 3),
                     "5:microliter")
        assert (1 == len(p.instructions))
        assert (
            "distribute" ==
            list(p.as_dict()["instructions"][0]["groups"][0].keys())[0])
        for w in c.wells_from(1, 3):
            assert (Unit(5, 'microliter') == w.volume)
        assert (Unit(5, 'microliter') == c.well(0).volume)

    def test_fill_wells(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        srcs = c.wells_from(1, 2).set_volume("100:microliter")
        dests = c.wells_from(7, 4)
        p.distribute(srcs, dests, "30:microliter", allow_carryover=True)
        assert (2 == len(p.instructions[0].groups))

        # track source vols
        assert (Unit(10, 'microliter') == c.well(1).volume)
        assert (Unit(70, 'microliter') == c.well(2).volume)

        # track dest vols
        assert (Unit(30, 'microliter') == c.well(7).volume)
        assert (c.well(6).volume is None)

        # test distribute from Well to Well
        p.distribute(c.well("A1").set_volume(
            "20:microliter"), c.well("A2"), "5:microliter")
        assert ("distribute" in p.instructions[-1].groups[-1])

    def test_unit_conversion(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        p.distribute(
            c.well(0).set_volume("100:microliter"), c.well(1), "200:nanoliter")
        assert (str(p.instructions[0].groups[0]["distribute"][
                "to"][0]["volume"]) == "0.2:microliter")
        p.distribute(c.well(2).set_volume("100:microliter"), c.well(
            3), ".1:milliliter", new_group=True)
        assert (str(
            p.instructions[-1].groups[0]["distribute"]["to"][
                0]["volume"]) == "100.0:microliter")

    def test_dispense_speed(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        p.distribute(
            c.well(0).set_volume("100:microliter"), c.well(1), "2:microliter",
            dispense_speed="150:microliter/second")
        assert ("dispense_speed" in p.instructions[-1].groups[-1]
                ["distribute"]["to"][0])
        p.distribute(
            c.well(0), c.well(1), "2:microliter",
            distribute_target={"dispense_speed": "100:microliter/second"})
        assert ("x_dispense_target" in p.instructions[-1].groups[-1]
                ["distribute"]["to"][0])


class TestTransfer():

    def test_single_transfer(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        p.transfer(c.well(0), c.well(1), "20:microliter")
        assert (Unit(20, "microliter") == c.well(1).volume)
        assert (c.well(0).volume is None)
        assert ("transfer" in p.instructions[-1].groups[-1])

    def test_uncover_before_transfer(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        p.cover(c)
        p.transfer(c.well(0), c.well(1), "20:microliter")
        assert (3 == len(p.instructions))
        assert (Unit(20, "microliter") == c.well(1).volume)
        assert (c.well(0).volume is None)
        assert ("transfer" in p.instructions[-1].groups[-1])
        assert (p.instructions[-2].op == "uncover")
        assert (not c.cover)

    def test_gt_900uL_transfer(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-deep", discard=True)
        p.transfer(
            c.well(0),
            c.well(1),
            "2000:microliter"
        )
        assert (3 == len(p.instructions[0].groups))
        assert (
            Unit(900, 'microliter') ==
            p.instructions[0].groups[0]['transfer'][0]['volume']
        )
        assert (
            Unit(900, 'microliter') ==
            p.instructions[0].groups[1]['transfer'][0]['volume']
        )
        assert (
            Unit(200, 'microliter') ==
            p.instructions[0].groups[2]['transfer'][0]['volume']
        )

    def test_gt_900uL_wellgroup_transfer(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-deep", discard=True)
        p.transfer(
            c.wells_from(0, 8, columnwise=True),
            c.wells_from(1, 8, columnwise=True),
            '2000:microliter'
        )
        assert (
            24 ==
            len(p.instructions[0].groups)
        )

    def test_transfer_option_propagation(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-deep", discard=True)
        p.transfer(
            c.well(0),
            c.well(1),
            "2000:microliter",
            aspirate_source=aspirate_source(
                depth("ll_bottom", distance=".004:meter")
            )
        )
        assert (
            len(p.instructions[0].groups[0]['transfer'][0]) ==
            len(p.instructions[0].groups[1]['transfer'][0])
        )
        assert (
            len(p.instructions[0].groups[0]['transfer'][0]) ==
            len(p.instructions[0].groups[2]['transfer'][0])
        )

    def test_max_transfer(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "micro-2.0", storage="cold_4")
        p.transfer(c.well(0), c.well(0), "3050:microliter")

    def test_multiple_transfers(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        p.transfer(c.wells_from(0, 2), c.wells_from(2, 2), "20:microliter")
        assert (c.well(2).volume == c.well(3).volume)
        assert (2 == len(p.instructions[0].groups))

    def test_one_tip(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        p.transfer(c.wells_from(0, 2), c.wells_from(2, 2), "20:microliter",
                   one_tip=True)
        assert (c.well(2).volume == c.well(3).volume)
        assert (1 == len(p.instructions[0].groups))

    def test_one_source(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        with pytest.raises(RuntimeError):
            p.transfer(c.wells_from(0, 2),
                       c.wells_from(2, 2), "40:microliter", one_source=True)
        with pytest.raises(RuntimeError):
            p.transfer(c.wells_from(0, 2).set_volume("1:microliter"),
                       c.wells_from(1, 5), "10:microliter", one_source=True)
        p.transfer(c.wells_from(0, 2).set_volume("50:microliter"),
                   c.wells_from(2, 2), "40:microliter", one_source=True)
        assert (2 == len(p.instructions[0].groups))
        assert (p.instructions[0].groups[0]["transfer"][0]
                ["from"] != p.instructions[0].groups[1]["transfer"]
                [0]["from"])
        p.transfer(c.wells_from(0, 2).set_volume("100:microliter"),
                   c.wells_from(2, 4), "40:microliter", one_source=True)
        assert (7 == len(p.instructions[0].groups))
        assert (p.instructions[0].groups[2]["transfer"][0]
                ["from"] == p.instructions[0].groups[4]["transfer"][0]["from"])
        assert (p.instructions[0].groups[4]["transfer"][0]["volume"] ==
                Unit.fromstring("20:microliter"))
        p.transfer(c.wells_from(0, 2).set_volume("100:microliter"),
                   c.wells_from(2, 4),
                   ["20:microliter", "40:microliter",
                    "60:microliter", "80:microliter"], one_source=True)
        assert (12 == len(p.instructions[0].groups))
        assert (p.instructions[0].groups[7]["transfer"][0]["from"] ==
                p.instructions[0].groups[9]["transfer"][0]["from"])
        assert (p.instructions[0].groups[9]["transfer"][0]["from"] !=
                p.instructions[0].groups[10]["transfer"][0]["from"])
        assert (Unit.fromstring("20:microliter") ==
                p.instructions[0].groups[10]["transfer"][0]["volume"])
        p.transfer(c.wells_from(0, 2).set_volume("50:microliter"),
                   c.wells(2), "100:microliter", one_source=True)
        c.well(0).set_volume("50:microliter")
        c.well(1).set_volume("200:microliter")
        p.transfer(c.wells_from(0, 2), c.well(
            1), "100:microliter", one_source=True)
        assert (p.instructions[0].groups[14]["transfer"][0]["from"] !=
                p.instructions[0].groups[15]["transfer"][0]["from"])
        c.well(0).set_volume("100:microliter")
        c.well(1).set_volume("0:microliter")
        c.well(2).set_volume("100:microliter")
        p.transfer(c.wells_from(0, 3), c.wells_from(3, 2),
                   "100:microliter", one_source=True)

    def test_one_tip_true_gt_750(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-deep", discard=True)
        p.transfer(c.well(0), c.well(1), "1000:microliter", one_tip=True)
        assert (1 == len(p.instructions[0].groups))

    def test_unit_conversion(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        p.transfer(c.well(0), c.well(1), "200:nanoliter")
        assert (
            str(p.instructions[0].groups[0]['transfer'][
                0]['volume']) == "0.2:microliter")
        p.transfer(c.well(1), c.well(2), ".5:milliliter", new_group=True)
        assert (
            str(p.instructions[-1].groups[0]['transfer'][
                0]['volume']) == "500.0:microliter")

    def test_volume_rounding(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        c.well(0).set_volume("100.0000000000005:microliter")
        c.well(1).set_volume("100:microliter")
        p.transfer(c.wells_from(0, 2), c.wells_from(
            3, 3), "50:microliter", one_source=True)
        assert (3 == len(p.instructions[0].groups))

        c.well(0).set_volume("50:microliter")
        c.well(1).set_volume("101:microliter")
        p.transfer(c.wells_from(0, 2), c.wells_from(
            3, 3), "50.0000000000005:microliter", one_source=True)
        assert (6 == len(p.instructions[0].groups))

    def test_mix_before_and_after(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        with pytest.raises(RuntimeError):
            p.transfer(
                c.well(0), c.well(1), "10:microliter", mix_vol="15:microliter")
            p.transfer(c.well(0), c.well(1), "10:microliter", repetitions_a=21)
            p.transfer(c.well(0), c.well(1), "10:microliter", repetitions=21)
            p.transfer(c.well(0), c.well(1), "10:microliter", repetitions_b=21)
            p.transfer(c.well(0), c.well(1), "10:microliter",
                       flowrate_a="200:microliter/second")
        p.transfer(c.well(0), c.well(1), "12:microliter", mix_after=True,
                   mix_vol="10:microliter", repetitions_a=20)
        assert (int(
            p.instructions[-1].groups[0]['transfer'][0]['mix_after'][
                'repetitions']) == 20)
        p.transfer(c.well(0), c.well(1), "12:microliter", mix_after=True,
                   mix_vol="10:microliter", repetitions_b=20)
        assert (int(
            p.instructions[-1].groups[-1]['transfer'][0]['mix_after'][
                'repetitions']) == 10)
        p.transfer(c.well(0), c.well(1), "12:microliter", mix_after=True)
        assert (int(
            p.instructions[-1].groups[-1]['transfer'][0]['mix_after'][
                'repetitions']) == 10)
        assert (str(
            p.instructions[-1].groups[-1]['transfer'][0]['mix_after'][
                'speed']) == "100:microliter/second")
        assert (str(
            p.instructions[-1].groups[-1]['transfer'][0]['mix_after'][
                'volume']) == "6.0:microliter")
        p.transfer(c.well(0), c.well(1), "12:microliter", mix_before=True,
                   mix_vol="10:microliter", repetitions_b=20)
        assert (int(
            p.instructions[-1].groups[-1]['transfer'][-1]['mix_before'][
                'repetitions']) == 20)
        p.transfer(c.well(0), c.well(1), "12:microliter", mix_before=True,
                   mix_vol="10:microliter", repetitions_a=20)
        assert (int(
            p.instructions[-1].groups[-1]['transfer'][-1]['mix_before'][
                'repetitions']) == 10)
        p.transfer(c.well(0), c.well(1), "12:microliter", mix_before=True)
        assert (int(
            p.instructions[-1].groups[-1]['transfer'][-1]['mix_before'][
                'repetitions']) == 10)
        assert (str(
            p.instructions[-1].groups[-1]['transfer'][-1]['mix_before'][
                'speed']) == "100:microliter/second")
        assert (str(
            p.instructions[-1].groups[-1]['transfer'][-1]['mix_before'][
                'volume']) == "6.0:microliter")

    def test_mix_false(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-deep", discard=True)
        p.transfer(c.well(0), c.well(1), "20:microliter", mix_after=False)
        assert ("mix_after" not in p.instructions[0].groups[0]["transfer"][0])
        p.transfer(c.well(0), c.well(1), "20:microliter", mix_before=False)
        assert ("mix_before" not in p.instructions[0].groups[1]["transfer"][0])
        p.transfer(c.well(0), c.well(1), "2000:microliter", mix_after=False)
        for i in range(2, 5):
            assert ("mix_after" not in
                    p.instructions[0].groups[i]["transfer"][0])
        p.transfer(c.well(0), c.well(1), "2000:microliter", mix_before=False)
        for i in range(5, 8):
            assert ("mix_before" not in
                    p.instructions[0].groups[i]["transfer"][0])


class TestConsolidate():

    def test_multiple_sources(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        with pytest.raises(TypeError):
            p.consolidate(
                c.wells_from(0, 3), c.wells_from(2, 3), "10:microliter")
        with pytest.raises(ValueError):
            p.consolidate(c.wells_from(0, 3), c.well(4), ["10:microliter"])
        p.consolidate(c.wells_from(0, 3), c.well(4), "10:microliter")
        assert (Unit(30, "microliter") == c.well(4).volume)
        assert (3 == len(p.instructions[0].groups[0]["consolidate"]["from"]))

    def test_one_source(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        p.consolidate(c.well(0), c.well(4), "30:microliter")
        assert (Unit(30, "microliter") == c.well(4).volume)


class TestStamp():

    def test_volume_tracking(self, dummy_protocol):
        p = dummy_protocol
        plate_96 = p.ref("plate_96", None, "96-pcr", discard=True)
        plate_96_2 = p.ref("plate_96_2", None, "96-pcr", discard=True)
        plate_384 = p.ref("plate_384", None, "384-pcr", discard=True)
        plate_384_2 = p.ref("plate_384_2", None, "384-pcr", discard=True)
        p.stamp(plate_96.well(0), plate_384.well(0), "5:microliter",
                {"columns": 12, "rows": 1})
        assert (plate_384.well(0).volume == Unit(5, 'microliter'))
        assert (plate_384.well(1).volume is None)
        p.stamp(plate_96.well(0), plate_96_2.well(0), "10:microliter",
                {"columns": 12, "rows": 1})
        p.stamp(plate_96.well(0), plate_96_2.well(0), "10:microliter",
                {"columns": 1, "rows": 8})
        assert (plate_96_2.well(0).volume == Unit(20, "microliter"))
        for w in plate_96_2.wells_from(1, 11):
            assert (w.volume == Unit(10, "microliter"))
        p.stamp(plate_96.well(0), plate_384_2.well(0), "5:microliter",
                {"columns": 1, "rows": 8})
        for w in plate_384_2.wells_from(0, 16, columnwise=True)[0::2]:
            assert (w.volume == Unit(5, "microliter"))
        for w in plate_384_2.wells_from(1, 16, columnwise=True)[0::2]:
            assert (w.volume is None)
        for w in plate_384_2.wells_from(1, 24)[0::2]:
            assert (w.volume is None)
        plate_384_2.all_wells().set_volume("0:microliter")
        p.stamp(plate_96.well(0), plate_384_2.well(
            0), "15:microliter", {"columns": 3, "rows": 8})
        assert (plate_384_2.well("C3").volume == Unit(15, "microliter"))
        assert (plate_384_2.well("B2").volume == Unit(0, "microliter"))

    def test_single_transfers(self, dummy_protocol):
        p = dummy_protocol
        plate_1_6 = p.ref("plate_1_6", None, "6-flat", discard=True)
        plate_1_96 = p.ref("plate_1_96", None, "96-flat", discard=True)
        plate_2_96 = p.ref("plate_2_96", None, "96-flat", discard=True)
        plate_1_384 = p.ref("plate_1_384", None, "384-flat", discard=True)
        plate_2_384 = p.ref("plate_2_384", None, "384-flat", discard=True)
        p.stamp(plate_1_96.well("G1"), plate_2_96.well("H1"),
                "10:microliter", dict(rows=1, columns=12))
        p.stamp(plate_1_96.well("A1"), plate_1_384.well("A2"),
                "10:microliter", dict(rows=8, columns=2))
        # Verify full plate to full plate transfer works for 96, 384 container
        # input
        p.stamp(plate_1_96, plate_2_96, "10:microliter")
        p.stamp(plate_1_384, plate_2_384, "10:microliter")

        with pytest.raises(ValueError):
            p.stamp(plate_1_96.well("A1"), plate_2_96.well("A2"),
                    "10:microliter", dict(rows=9, columns=1))
        with pytest.raises(ValueError):
            p.stamp(plate_1_96.well("A1"), plate_2_96.well("B1"),
                    "10:microliter", dict(rows=1, columns=13))
        with pytest.raises(ValueError):
            p.stamp(plate_1_384.well("A1"), plate_2_384.well("A2"),
                    "10:microliter", dict(rows=9, columns=1))
        with pytest.raises(ValueError):
            p.stamp(plate_1_384.well("A1"), plate_2_384.well("B1"),
                    "10:microliter", dict(rows=1, columns=13))
        with pytest.raises(ValueError):
            p.stamp(plate_1_96.well("A1"), plate_2_96.well("A2"),
                    "10:microliter", dict(rows=1, columns=12))
        with pytest.raises(ValueError):
            p.stamp(plate_1_96.well("A1"), plate_2_96.well("D1"),
                    "10:microliter", dict(rows=6, columns=12))
        with pytest.raises(ValueError):
            p.stamp(plate_1_6.well("A1"), plate_2_96.well("D1"),
                    "10:microliter", dict(rows=1, columns=2))

    def test_multiple_transfers(self):
        # Set maximum number of full plate transfers (limited by maximum
        # number of tip boxes)
        maxFullTransfers = 4

        # Test: Ensure individual transfers are appended one at a time
        p = Protocol()
        plateList = [p.ref("plate_%s_96" % str(x + 1), None, "96-flat",
                           discard=True) for x in range(2)]

        for i in range(maxFullTransfers):
            p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                    "10:microliter")
            assert (i + 1 == len(p.instructions[0].groups))

        # Ensure new stamp operation overflows into new instruction
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter")
        assert (len(p.instructions) == 2)
        assert (1 == len(p.instructions[1].groups))

        # Test: Maximum number of containers on a deck
        maxContainers = 3
        p = Protocol()
        plateList = [p.ref("plate_%s_96" % str(x + 1), None, "96-flat",
                           discard=True) for x in range(maxContainers + 1)]

        for i in range(maxContainers - 1):
            p.stamp(plateList[i], plateList[i + 1], "10:microliter")
        assert (1 == len(p.instructions))
        assert (maxContainers - 1 == len(p.instructions[0].groups))

        p.stamp(plateList[maxContainers - 1].well("A1"),
                plateList[maxContainers].well("A1"), "10:microliter")
        assert (2 == len(p.instructions))

        # Test: Ensure col/row/full plate stamps are in separate instructions
        p = Protocol()
        plateList = [p.ref("plate_%s_96" % str(x + 1), None, "96-flat",
                           discard=True) for x in range(2)]

        p.stamp(plateList[0].well("G1"), plateList[1].well("G1"),
                "10:microliter", dict(rows=1, columns=12))
        assert (len(p.instructions) == 1)
        p.stamp(plateList[0].well("G1"), plateList[1].well("G1"),
                "10:microliter", dict(rows=2, columns=12))
        assert (len(p.instructions) == 1)
        assert (len(p.instructions[0].groups) == 2)

        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=8, columns=2))
        p.stamp(plateList[0].well("A1"), plateList[1].well("A12"),
                "10:microliter", dict(rows=8, columns=1))
        assert (len(p.instructions) == 2)
        assert (len(p.instructions[1].groups) == 2)

        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=8, columns=12))
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=8, columns=12))
        assert (len(p.instructions) == 3)
        assert (len(p.instructions[2].groups) == 2)

        # Test: Check on max transfer limit - Full plate
        p = Protocol()
        plateList = [p.ref("plate_%s_96" % str(x + 1), None, "96-flat",
                           discard=True) for x in range(2)]

        for i in range(maxFullTransfers):
            p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                    "10:microliter", dict(rows=8, columns=12))
        assert (len(p.instructions) == 1)

        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=8, columns=12))
        assert (len(p.instructions) == 2)
        assert (maxFullTransfers == len(p.instructions[0].groups))
        assert (1 == len(p.instructions[1].groups))

        # Test: Check on max transfer limit - Row-wise
        p = Protocol()
        plateList = [p.ref("plate_%s_96" % str(x + 1), None, "96-flat",
                           discard=True) for x in range(2)]
        # Mixture of rows
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=3, columns=12))
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=1, columns=12))
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=2, columns=12))
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=2, columns=12))
        assert (len(p.instructions) == 1)
        # Maximum number of row transfers
        for i in range(8):
            p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                    "10:microliter", dict(rows=1, columns=12))
        assert (len(p.instructions) == 2)
        assert (len(p.instructions[0].groups) == 4)
        assert (len(p.instructions[1].groups) == 8)
        # Overflow check
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=1, columns=12))
        assert (len(p.instructions) == 3)

        # Test: Check on max transfer limit - Col-wise
        p = Protocol()
        plateList = [p.ref("plate_%s_96" % str(x + 1), None, "96-flat",
                           discard=True) for x in range(2)]
        # Mixture of columns
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=8, columns=4))
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=8, columns=6))
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=8, columns=2))
        assert (len(p.instructions) == 1)
        # Maximum number of col transfers
        for i in range(12):
            p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                    "10:microliter", dict(rows=8, columns=1))
        assert (len(p.instructions) == 2)
        assert (len(p.instructions[0].groups) == 3)
        assert (len(p.instructions[1].groups) == 12)

        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=8, columns=1))
        assert (len(p.instructions) == 3)

        # Test: Check on switching between tip volume types
        p = Protocol()
        plateList = [p.ref("plate_%s_96" % str(x + 1), None, "96-flat",
                           discard=True) for x in range(2)]
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "31:microliter")
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "31:microliter")
        assert (len(p.instructions) == 1)
        assert (2 == len(p.instructions[0].groups))

        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "90:microliter")
        assert (len(p.instructions) == 2)
        assert (2 == len(p.instructions[0].groups))
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "90:microliter")
        assert (len(p.instructions) == 2)
        assert (2 == len(p.instructions[1].groups))

        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "31:microliter")
        assert (len(p.instructions) == 3)

        # Test: Check on max transfer limit - Row-wise
        p = Protocol()
        plateList = [p.ref("plate_%s_96" % str(x + 1), None, "96-flat",
                           discard=True) for x in range(3)]
        # Mixture of columns
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=1, columns=12))
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=3, columns=12))
        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=4, columns=12))
        assert (len(p.instructions) == 1)
        # Maximum number of row transfers
        for i in range(8):
            p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                    "10:microliter", dict(rows=1, columns=12))
        assert (len(p.instructions) == 2)
        assert (len(p.instructions[0].groups) == 3)
        assert (len(p.instructions[1].groups) == 8)

        p.stamp(plateList[0].well("A1"), plateList[1].well("A1"),
                "10:microliter", dict(rows=1, columns=12))
        assert (len(p.instructions) == 3)
        p.stamp(plateList[0].well("A1"), plateList[2].well("A1"),
                "10:microliter", dict(rows=1, columns=12))
        assert (len(p.instructions) == 4)

    def test_one_tip(self, dummy_protocol):

        p = dummy_protocol
        plateCount = 2
        plateList = [p.ref("plate_%s_384" % str(x + 1),
                     None, "384-flat", discard=True) for x in range(plateCount)]
        p.stamp(plateList[0], plateList[1], "330:microliter", one_tip=True)
        assert (len(p.instructions[0].groups[0]["transfer"]) == 12)
        assert (len(p.instructions[0].groups) == 1)

    def test_one_tip_variable_volume(self, dummy_protocol):

        p = dummy_protocol
        plateCount = 2
        plateList = [p.ref("plate_%s_384" % str(x + 1),
                     None, "384-flat", discard=True) for x in range(plateCount)]
        with pytest.raises(RuntimeError):
            p.stamp(WellGroup([plateList[0].well(0),
                    plateList[0].well(1)]),
                    WellGroup([plateList[1].well(0), plateList[1].well(1)]),
                    ["20:microliter", "90:microliter"], one_tip=True)
        p.stamp(WellGroup([plateList[0].well(0), plateList[0].well(1)]),
                WellGroup([plateList[1].well(0), plateList[1].well(1)]),
                ["20:microliter", "90:microliter"], mix_after=True,
                mix_vol="40:microliter", one_tip=True)
        assert (len(p.instructions[0].groups[0]["transfer"]) == 2)
        assert (len(p.instructions[0].groups) == 1)

    def test_wellgroup(self, dummy_protocol):
        p = dummy_protocol
        plateCount = 2
        plateList = [p.ref("plate_%s_384" % str(x + 1),
                     None, "384-flat", discard=True) for x in range(plateCount)]
        p.stamp(plateList[0].wells(list(range(12))), plateList[1].wells(
            list(range(12))), "30:microliter", shape={"rows": 8, "columns": 1})
        assert (len(p.instructions[0].groups) == 12)

    def test_gt_148uL_transfer(self, dummy_protocol):
        p = dummy_protocol
        plateCount = 2
        plateList = [p.ref("plate_%s_96" % str(
            x + 1), None, "96-flat", discard=True) for x in range(plateCount)]
        p.stamp(plateList[0], plateList[1], "296:microliter")
        assert (2 == len(p.instructions[0].groups))
        assert (Unit(148, 'microliter') ==
                p.instructions[0].groups[0]['transfer'][0]['volume'])
        assert (Unit(148, 'microliter') ==
                p.instructions[0].groups[1]['transfer'][0]['volume'])

    def test_one_source(self, dummy_protocol):
        p = dummy_protocol
        plateCount = 2
        plateList = [p.ref("plate_%s_384" % str(x + 1),
                     None, "384-flat", discard=True) for x in range(plateCount)]
        with pytest.raises(RuntimeError):
            p.stamp(plateList[0].wells(list(range(4))),
                    plateList[1].wells(list(range(12))),
                    "30:microliter", shape={"rows": 8, "columns": 1},
                    one_source=True)
        plateList[0].wells_from(
            0, 64, columnwise=True).set_volume("10:microliter")
        with pytest.raises(RuntimeError):
            p.stamp(plateList[0].wells(list(range(4))),
                    plateList[1].wells(list(range(12))),
                    "30:microliter", shape={"rows": 8, "columns": 1},
                    one_source=True)
        plateList[0].wells_from(
            0, 64, columnwise=True).set_volume("15:microliter")
        p.stamp(plateList[0].wells(list(range(4))),
                plateList[1].wells(list(range(12))), "5:microliter",
                shape={"rows": 8, "columns": 1}, one_source=True)
        assert (len(p.instructions[0].groups) == 12)

    def test_implicit_uncover(self, dummy_protocol):
        p = dummy_protocol
        plateCount = 2
        plateList = [p.ref("plate_%s_384" % str(x + 1), None, "384-flat",
                           discard=True, cover="universal")
                     for x in range(plateCount)]
        for x in plateList:
            assert (x.cover)
        p.stamp(plateList[0], plateList[1], "5:microliter")
        for x in plateList:
            assert (not x.cover)
        assert (len(p.instructions) == 3)
        assert (p.instructions[0].op == "uncover")


class TestRefify():

    def test_refifying_various(self, dummy_protocol):
        p = dummy_protocol
        # refify container
        refs = {"plate": p.ref("test", None, "96-flat", "cold_20")}
        assert (p._refify(refs["plate"]) == "test")
        # refify dict
        assert (p._refify(refs) == {"plate": "test"})

        # refify Well
        well = refs["plate"].well("A1")
        assert (p._refify(well) == "test/0")

        # refify WellGroup
        wellgroup = refs["plate"].wells_from("A2", 3)
        assert (p._refify(wellgroup) == ["test/1", "test/2", "test/3"])

        # refify Unit
        a_unit = Unit("30:microliter")
        assert (p._refify(a_unit) == "30.0:microliter")

        # refify Instruction
        p.cover(refs["plate"])
        assert (p._refify(p.instructions[0]) == p._refify(
            p.instructions[0].data))

        # refify Ref
        assert (p._refify(p.refs["test"]) == p.refs["test"].opts)

        # refify other
        s = "randomstring"
        i = 24
        assert ("randomstring" == p._refify(s))
        assert (24 == p._refify(i))


class TestOuts():

    def test_outs(self, dummy_protocol):
        p = dummy_protocol
        assert ('outs' not in p.as_dict())
        plate = p.ref("plate", None, "96-pcr", discard=True)
        plate.well(0).set_name("test_well")
        plate.well(0).set_properties({"test": "foo"})
        assert (plate.well(0).name == "test_well")
        assert (list(p.as_dict()['outs'].keys()) == ['plate'])
        assert (list(list(p.as_dict()['outs'].values())[0].keys()) ==
                ['0'])
        assert (list(p.as_dict()['outs'].values())[0]['0']['name'] ==
                'test_well')
        assert (list(p.as_dict()['outs'].values())[0]['0']['properties']
                ['test'] == 'foo')


class TestInstructionIndex():

    def test_instruction_index(self, dummy_protocol):
        p = dummy_protocol
        plate = p.ref("plate", None, "96-flat", discard=True)

        with pytest.raises(ValueError):
            p.get_instruction_index()
        p.cover(plate)
        assert (p.get_instruction_index() == 0)
        p.uncover(plate)
        assert (p.get_instruction_index() == 1)


class TestTimeConstraints:

    def test_time_constraint(self, dummy_protocol):
        p = dummy_protocol

        plate_1 = p.ref("plate_1", id=None, cont_type="96-flat", discard=True)
        plate_2 = p.ref("plate_2", id=None, cont_type="96-flat", discard=True)

        p.cover(plate_1)
        time_point_1 = p.get_instruction_index()
        p.cover(plate_2)
        time_point_2 = p.get_instruction_index()

        with pytest.raises(AttributeError):
            p.time_constraints

        p.add_time_constraint({"mark": time_point_1, "state": "start"},
                              {"mark": time_point_1, "state": "end"},
                              "10:minute")
        p.add_time_constraint({"mark": time_point_1, "state": "start"},
                              {"mark": time_point_2, "state": "end"},
                              "10:minute")
        p.add_time_constraint({"mark": time_point_2, "state": "start"},
                              {"mark": time_point_1, "state": "end"},
                              "10:minute")
        p.add_time_constraint({"mark": time_point_1, "state": "start"}, {
                              "mark": plate_1, "state": "end"}, "10:minute")
        p.add_time_constraint({"mark": plate_2, "state": "start"}, {
                              "mark": plate_1, "state": "end"}, "10:minute")
        p.add_time_constraint({"mark": plate_2, "state": "start"}, {
                              "mark": plate_2, "state": "end"}, "10:minute")

        assert (len(p.time_constraints) == 6)

        p.add_time_constraint({"mark": time_point_1, "state": "end"},
                              {"mark": time_point_2, "state": "end"},
                              "10:minute", True)

        assert (len(p.time_constraints) == 8)

    def test_time_constraint_checker(self, dummy_protocol):
        p = dummy_protocol

        plate_1 = p.ref("plate_1", id=None, cont_type="96-flat", discard=True)
        plate_2 = p.ref("plate_2", id=None, cont_type="96-flat", discard=True)

        p.cover(plate_1)
        p.cover(plate_2)

        with pytest.raises(ValueError):
            p.add_time_constraint(
                {"mark": -1, "state": "start"},
                {"mark": plate_2, "state": "end"}, "10:minute")

        with pytest.raises(TypeError):
            p.add_time_constraint({"mark": "foo", "state": "start"}, {
                                  "mark": plate_2, "state": "end"}, "10:minute")

        with pytest.raises(TypeError):
            p.add_time_constraint({"mark": plate_1, "state": "foo"}, {
                                  "mark": plate_2, "state": "end"}, "10:minute")

        with pytest.raises(ValueError):
            p.add_time_constraint({"mark": plate_1, "state": "start"},
                                  {"mark": plate_2, "state": "end"},
                                  "-10:minute")

        with pytest.raises(RuntimeError):
            p.add_time_constraint({"mark": plate_1, "state": "start"},
                                  {"mark": plate_1, "state": "start"},
                                  "10:minute")

        with pytest.raises(RuntimeError):
            p.add_time_constraint({"mark": plate_1, "state": "end"},
                                  {"mark": plate_1, "state": "start"},
                                  "10:minute")

        with pytest.raises(KeyError):
            p.add_time_constraint({"mark": plate_1},
                                  {"mark": plate_1, "state": "start"},
                                  "10:minute")

        with pytest.raises(KeyError):
            p.add_time_constraint({"state": "end"},
                                  {"mark": plate_1, "state": "start"},
                                  "10:minute")

    def test_time_more_than(self, dummy_protocol):
        p = dummy_protocol

        plate_1 = p.ref("plate_1", id=None, cont_type="96-flat", discard=True)
        plate_2 = p.ref("plate_2", id=None, cont_type="96-flat", discard=True)

        p.cover(plate_1)
        p.cover(plate_2)

        # Mirror has no effect with only more_than
        p.add_time_constraint({"mark": plate_1, "state": "start"},
                              {"mark": plate_2, "state": "start"},
                              more_than="1:minute", mirror=True)

        assert (len(p.time_constraints) == 1)

        # this adds 3 more constraints
        p.add_time_constraint(
            {"mark": plate_1, "state": "start"},
            {"mark": plate_2, "state": "start"},
            less_than="10:minute",
            more_than="1:minute", mirror=True
        )

        assert (len(p.time_constraints) == 4)


class TestAbsorbance:

    def test_single_well(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.absorbance(test_plate, test_plate.well(0), "475:nanometer",
                     "test_reading")
        assert isinstance(p.instructions[0].wells, list)

    def test_bad_well(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref("test", None, "96-flat", discard=True)
        with pytest.raises(ValueError):
            p.absorbance(test_plate, "bad_well_ref",
                         wavelength="450:nanometer", dataref="bad_wells")

    def test_temperature(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.absorbance(test_plate, test_plate.well(0), "475:nanometer",
                     "test_reading", temperature="30:celsius")
        assert (p.instructions[0].temperature == "30:celsius")

    def test_incubate(self, dummy_protocol):
        from autoprotocol.util import incubate_params

        p = dummy_protocol
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.absorbance(test_plate, test_plate.well(0), "475:nanometer",
                     "test_reading",
                     incubate_before=incubate_params(
                                                     "10:second",
                                                     "3:millimeter",
                                                     True)
                     )

        assert (p.instructions[0].incubate_before["shaking"]["orbital"])
        assert (p.instructions[0].incubate_before["shaking"]["amplitude"] ==
                "3:millimeter")
        assert (p.instructions[0].incubate_before["duration"] == "10:second")

        p.absorbance(test_plate, test_plate.well(0), "475:nanometer",
                     "test_reading",
                     incubate_before=incubate_params("10:second"))

        assert ("shaking" not in p.instructions[1].incubate_before)
        assert (p.instructions[1].incubate_before["duration"] == "10:second")

        with pytest.raises(ValueError):
            p.absorbance(test_plate, test_plate.well(0),
                         "475:nanometer", "test_reading",
                         incubate_before=incubate_params("10:second",
                                                         "-3:millimeter",
                                                         True))

        with pytest.raises(ValueError):
            p.absorbance(test_plate, test_plate.well(0),
                         "475:nanometer", "test_reading",
                         incubate_before=incubate_params("10:second",
                                                         "3:millimeter",
                                                         "foo"))

        with pytest.raises(ValueError):
            p.absorbance(test_plate, test_plate.well(0),
                         "475:nanometer", "test_reading",
                         incubate_before=incubate_params("-10:second",
                                                         "3:millimeter",
                                                         True))

        with pytest.raises(RuntimeError):
            p.absorbance(test_plate, test_plate.well(
                0), "475:nanometer", "test_reading",
                incubate_before=incubate_params("10:second", "3:millimeter"))

        with pytest.raises(RuntimeError):
            p.absorbance(test_plate, test_plate.well(0),
                         "475:nanometer", "test_reading",
                         incubate_before=incubate_params("10:second",
                                                         shake_orbital=True))

        with pytest.raises(RuntimeError):
            p.absorbance(test_plate, test_plate.well(0), "475:nanometer",
                         "test_reading", incubate_before={
                         'shaking': {'amplitude': '3:mm', 'orbital': True}})

        with pytest.raises(RuntimeError):
            p.absorbance(test_plate, test_plate.well(
                0), "475:nanometer", "test_reading",
                incubate_before={'duration': '10:minute', 'shaking': {}})

        with pytest.raises(RuntimeError):
            p.absorbance(test_plate, test_plate.well(0),
                         "475:nanometer", "test_reading", incubate_before={
                         'duration': '10:minute', 'shaking': {'orbital': True}})

        with pytest.raises(RuntimeError):
            p.absorbance(test_plate, test_plate.well(0), "475:nanometer",
                         "test_reading", incubate_before={
                         'duration': '10:minute',
                         'shaking': {'amplitude': '3:mm'}})
        with pytest.raises(KeyError):
            p.absorbance(test_plate, test_plate.well(0), "475:nanometer",
                         "test_reading", incubate_before={
                         'duration': '10:minute',
                         'shake': {'amplitude': '3:mm', 'orbital': True}})


class TestFluorescence:

    def test_single_well(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.fluorescence(test_plate, test_plate.well(0),
                       excitation="587:nanometer", emission="610:nanometer",
                       dataref="test_reading")
        assert (isinstance(p.instructions[0].wells, list))

    def test_temperature(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.fluorescence(test_plate, test_plate.well(0),
                       excitation="587:nanometer",
                       emission="610:nanometer", dataref="test_reading",
                       temperature="30:celsius")
        assert (p.instructions[0].temperature == "30:celsius")

    def test_gain(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref("test", None, "96-flat", discard=True)
        for i in range(0, 10):
            p.fluorescence(test_plate, test_plate.well(0),
                           excitation="587:nanometer",
                           emission="610:nanometer",
                           dataref="test_reading_%s" % i, gain=(i * 0.1))
            assert (p.instructions[i].gain == (i * 0.1))

        with pytest.raises(ValueError):
            for i in range(-6, 10, 5):
                p.fluorescence(test_plate,
                               test_plate.well(0),
                               excitation="587:nanometer",
                               emission="610:nanometer",
                               dataref="test_reading", gain=i)

    def test_incubate(self, dummy_protocol):
        from autoprotocol.util import incubate_params

        p = dummy_protocol
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.fluorescence(test_plate, test_plate.well(0),
                       excitation="587:nanometer", emission="610:nanometer",
                       dataref="test_reading",
                       incubate_before=incubate_params("10:second",
                                                       "3:millimeter",
                                                       True))

        assert (p.instructions[0].incubate_before["shaking"]["orbital"])
        assert (p.instructions[0].incubate_before["shaking"]["amplitude"] ==
                "3:millimeter")
        assert (p.instructions[0].incubate_before["duration"] == "10:second")

        p.fluorescence(test_plate, test_plate.well(0),
                       excitation="587:nanometer", emission="610:nanometer",
                       dataref="test_reading",
                       incubate_before=incubate_params("10:second"))

        assert ("shaking" not in p.instructions[1].incubate_before)
        assert (p.instructions[1].incubate_before["duration"] == "10:second")

        with pytest.raises(ValueError):
            p.fluorescence(test_plate, test_plate.well(0),
                           excitation="587:nanometer", emission="610:nanometer",
                           dataref="test_reading",
                           incubate_before=incubate_params("10:second",
                                                           "-3:millimeter",
                                                           True))

        with pytest.raises(ValueError):
            p.fluorescence(test_plate, test_plate.well(0),
                           excitation="587:nanometer", emission="610:nanometer",
                           dataref="test_reading",
                           incubate_before=incubate_params("10:second",
                                                           "3:millimeter",
                                                           "foo"))

        with pytest.raises(ValueError):
            p.fluorescence(test_plate, test_plate.well(0),
                           excitation="587:nanometer", emission="610:nanometer",
                           dataref="test_reading",
                           incubate_before=incubate_params("-10:second",
                                                           "3:millimeter",
                                                           True))

        with pytest.raises(RuntimeError):
            p.fluorescence(test_plate, test_plate.well(0),
                           excitation="587:nanometer", emission="610:nanometer",
                           dataref="test_reading",
                           incubate_before=incubate_params("10:second",
                                                           "3:millimeter"))

        with pytest.raises(RuntimeError):
            p.fluorescence(test_plate, test_plate.well(0),
                           excitation="587:nanometer", emission="610:nanometer",
                           dataref="test_reading",
                           incubate_before=incubate_params("10:second",
                                                           shake_orbital=True))

        with pytest.raises(RuntimeError):
            p.fluorescence(test_plate, test_plate.well(0),
                           excitation="587:nanometer", emission="610:nanometer",
                           dataref="test_reading",
                           incubate_before={'shaking':
                                            {'amplitude': '3:mm',
                                             'orbital': True}})

        with pytest.raises(RuntimeError):
            p.fluorescence(test_plate, test_plate.well(0),
                           excitation="587:nanometer", emission="610:nanometer",
                           dataref="test_reading",
                           incubate_before={'duration': '10:minute',
                                            'shaking': {}})

        with pytest.raises(RuntimeError):
            p.fluorescence(test_plate, test_plate.well(0),
                           excitation="587:nanometer", emission="610:nanometer",
                           dataref="test_reading",
                           incubate_before={'duration': '10:minute',
                                            'shaking': {'orbital': True}})

        with pytest.raises(RuntimeError):
            p.fluorescence(test_plate, test_plate.well(0),
                           excitation="587:nanometer", emission="610:nanometer",
                           dataref="test_reading",
                           incubate_before={'duration': '10:minute',
                                            'shaking': {'amplitude': '3:mm'}})


class TestLuminescence:

    def test_single_well(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.luminescence(test_plate, test_plate.well(0), "test_reading")
        assert (isinstance(p.instructions[0].wells, list))

    def test_temperature(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.luminescence(test_plate, test_plate.well(
            0), "test_reading", temperature="30:celsius")
        assert (p.instructions[0].temperature == "30:celsius")

    def test_incubate(self, dummy_protocol):
        from autoprotocol.util import incubate_params

        p = dummy_protocol
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.luminescence(test_plate, test_plate.well(0), "test_reading",
                       incubate_before=incubate_params("10:second",
                                                       "3:millimeter",
                                                       True))

        assert (p.instructions[0].incubate_before["shaking"]["orbital"])
        assert (p.instructions[0].incubate_before["shaking"]["amplitude"] ==
                "3:millimeter")
        assert (p.instructions[0].incubate_before["duration"] == "10:second")

        p.luminescence(test_plate, test_plate.well(0), "test_reading",
                       incubate_before=incubate_params("10:second"))

        assert ("shaking" not in p.instructions[1].incubate_before)
        assert (p.instructions[1].incubate_before["duration"] == "10:second")

        with pytest.raises(ValueError):
            p.luminescence(test_plate, test_plate.well(0),
                           "test_reading",
                           incubate_before=incubate_params("10:second",
                                                           "-3:millimeter",
                                                           True))

        with pytest.raises(ValueError):
            p.luminescence(test_plate, test_plate.well(0),
                           "test_reading",
                           incubate_before=incubate_params("10:second",
                                                           "3:millimeter",
                                                           "foo"))

        with pytest.raises(ValueError):
            p.luminescence(test_plate, test_plate.well(0),
                           "test_reading",
                           incubate_before=incubate_params("-10:second",
                                                           "3:millimeter",
                                                           True))

        with pytest.raises(RuntimeError):
            p.luminescence(test_plate, test_plate.well(0),
                           "test_reading",
                           incubate_before=incubate_params("10:second",
                                                           "3:millimeter"))

        with pytest.raises(RuntimeError):
            p.luminescence(test_plate, test_plate.well(0),
                           "test_reading",
                           incubate_before=incubate_params("10:second",
                                                           shake_orbital=True))

        with pytest.raises(RuntimeError):
            p.luminescence(test_plate, test_plate.well(0), "test_reading",
                           incubate_before={
                           'shaking': {'amplitude': '3:mm', 'orbital': True}})

        with pytest.raises(RuntimeError):
            p.luminescence(test_plate, test_plate.well(0),
                           "test_reading",
                           incubate_before={
                           'duration': '10:minute', 'shaking': {}})

        with pytest.raises(RuntimeError):
            p.luminescence(test_plate, test_plate.well(0), "test_reading",
                           incubate_before={
                           'duration': '10:minute', 'shaking':
                           {'orbital': True}})

        with pytest.raises(RuntimeError):
            p.luminescence(test_plate, test_plate.well(0), "test_reading",
                           incubate_before={
                           'duration': '10:minute', 'shaking':
                           {'amplitude': '3:mm'}})


class TestAcousticTransfer:

    def test_append(self, dummy_protocol):
        p = dummy_protocol
        echo = p.ref("echo", None, "384-echo", discard=True)
        dest = p.ref("dest", None, "384-flat", discard=True)
        dest2 = p.ref("dest2", None, "384-flat", discard=True)
        p.acoustic_transfer(echo.well(0), dest.wells(1, 3, 5), "25:microliter")
        assert (len(p.instructions) == 1)
        p.acoustic_transfer(echo.well(0), dest.wells(0, 2, 4), "25:microliter")
        assert (len(p.instructions) == 1)
        p.acoustic_transfer(echo.well(0), dest.wells(0, 2, 4), "25:microliter",
                            droplet_size="0.50:microliter")
        assert (len(p.instructions) == 2)
        p.acoustic_transfer(
            echo.well(0), dest2.wells(0, 2, 4), "25:microliter")
        assert (len(p.instructions) == 3)

    def test_one_source(self, dummy_protocol):
        p = dummy_protocol
        echo = p.ref("echo", None, "384-echo", discard=True)
        dest = p.ref("dest", None, "384-flat", discard=True)
        p.acoustic_transfer(echo.wells(0, 1).set_volume("2:microliter"),
                            dest.wells(0, 1, 2, 3), "1:microliter",
                            one_source=True)
        assert (
            p.instructions[-1].data["groups"][0]["transfer"][-1]["from"] ==
            echo.well(1))
        assert (
            p.instructions[-1].data["groups"][0]["transfer"][0]["from"] ==
            echo.well(0))

    def test_droplet_size(self, dummy_protocol):
        p = dummy_protocol
        echo = p.ref("echo", None, "384-echo", discard=True)
        dest = p.ref("dest", None, "384-flat", discard=True)
        with pytest.raises(RuntimeError):
            p.acoustic_transfer(echo.wells(0, 1).set_volume("2:microliter"),
                                dest.wells(0, 1), "1:microliter",
                                droplet_size="26:nanoliter")
        with pytest.raises(RuntimeError):
            p.acoustic_transfer(echo.wells(0, 1).set_volume("2:microliter"),
                                dest.wells(0, 1), "1.31:microliter")


class TestMix():

    def test_mix(self, dummy_protocol):
        p = dummy_protocol
        w = p.ref("test", None, "micro-1.5",
                  discard=True).well(0).set_volume("20:microliter")
        p.mix(w, "5:microliter")
        assert (Unit(20, "microliter") == w.volume)
        assert ("mix" in p.instructions[-1].groups[-1])

    def test_mix_one_tip(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("test", None, "96-flat", discard=True)
        p.mix(c.wells(0, 1, 2), "5:microliter", one_tip=False)
        assert (len(p.instructions[-1].groups) == 3)
        p.mix(c.wells(0, 1, 2, 4), "5:microliter", one_tip=True)
        assert (len(p.instructions[-1].groups) == 4)


class TestMagneticTransfer:

    def test_head_type(self, dummy_protocol):
        p = dummy_protocol
        pcr = p.ref("pcr", None, "96-pcr", discard=True)

        with pytest.raises(ValueError):
            p.mag_dry("96-flat", pcr, "30:minute", new_tip=False,
                      new_instruction=False)
        p.mag_dry("96-pcr", pcr, "30:minute", new_tip=False,
                  new_instruction=False)
        assert (len(p.instructions) == 1)

    def test_head_compatibility(self, dummy_protocol):
        p = dummy_protocol

        pcrs = [p.ref("pcr_%s" % cont_type, None, cont_type, discard=True)
                for cont_type in ["96-pcr", "96-v-kf", "96-flat", "96-flat-uv"]]
        deeps = [p.ref("deep_%s" % cont_type, None, cont_type, discard=True)
                 for cont_type in ["96-v-kf", "96-deep-kf", "96-deep"]]

        for i, pcr in enumerate(pcrs):
            p.mag_dry("96-pcr", pcr, "30:minute", new_tip=False,
                      new_instruction=False)
            assert (len(p.instructions[-1].groups[0]) == i + 1)

        for i, deep in enumerate(deeps):
            if i == 0:
                n_i = True
            else:
                n_i = False
            p.mag_dry("96-deep", deep, "30:minute", new_tip=False,
                      new_instruction=n_i)
            assert (len(p.instructions[-1].groups[0]) == i + 1)

        bad_pcrs = [p.ref("bad_pcr_%s" % cont_type, None,
                          cont_type, discard=True) for cont_type in ["96-pcr"]]
        bad_deeps = [p.ref("bad_deep_%s" % cont_type,
                           None, cont_type, discard=True)
                     for cont_type in ["96-deep-kf", "96-deep"]]

        for pcr in bad_pcrs:
            with pytest.raises(ValueError):
                p.mag_dry("96-deep", pcr, "30:minute", new_tip=False,
                          new_instruction=False)

        for deep in bad_deeps:
            with pytest.raises(ValueError):
                p.mag_dry("96-pcr", deep, "30:minute", new_tip=False,
                          new_instruction=False)

    def test_unit_converstion(self, dummy_protocol):
        p = dummy_protocol
        pcr = p.ref("pcr", None, "96-pcr", discard=True)
        p.mag_mix("96-pcr", pcr, "30:second", "5:hertz",
                  center=0.75, amplitude=0.25,
                  magnetize=True, temperature=None,
                  new_tip=False, new_instruction=False)
        out_dict = {'amplitude': 0.25,
                    'center': 0.75,
                    'duration': Unit(30.0, 'second'),
                    'frequency': Unit(5.0, 'hertz'),
                    'magnetize': True}
        for k, v in out_dict.items():
            assert (p.instructions[-1].groups[0][0]["mix"][k] == v)

    def test_temperature_valid(self, dummy_protocol):
        p = dummy_protocol

        pcr = p.ref("pcr", None, "96-pcr", discard=True)

        for i in range(27, 96):
            p.mag_incubate(
                "96-pcr", pcr, "30:minute", temperature="%s:celsius" % i)
            assert (len(p.instructions[-1].groups[0]) == i - 26)

        for i in range(-300, -290):
            with pytest.raises(ValueError):
                p.mag_incubate(
                    "96-pcr", pcr, "30:minute", temperature="%s:celsius" % i)

    def test_frequency_valid(self, dummy_protocol):
        p = dummy_protocol

        pcr = p.ref("pcr", None, "96-pcr", discard=True)

        for i in range(27, 96):
            p.mag_mix("96-pcr", pcr, "30:second", "%s:hertz" %
                      i, center=1, amplitude=0)
            assert (len(p.instructions[-1].groups[0]) == i - 26)

        for i in range(-10, -5):
            with pytest.raises(ValueError):
                p.mag_mix("96-pcr", pcr, "30:second", "%s:hertz" %
                          i, center=1, amplitude=0)

    def test_magnetize_valid(self, dummy_protocol):
        p = dummy_protocol

        pcr = p.ref("pcr", None, "96-pcr", discard=True)

        p.mag_mix("96-pcr", pcr, "30:second", "60:hertz",
                  center=1, amplitude=0, magnetize=True)
        assert (len(p.instructions[-1].groups[0]) == 1)

        p.mag_mix("96-pcr", pcr, "30:second", "60:hertz",
                  center=1, amplitude=0, magnetize=False)
        assert (len(p.instructions[-1].groups[0]) == 2)

        with pytest.raises(ValueError):
            p.mag_mix("96-pcr", pcr, "30:second", "60:hertz",
                      center=1, amplitude=0, magnetize="Foo")

    def test_center_valid(self, dummy_protocol):
        p = dummy_protocol

        pcr = p.ref("pcr", None, "96-pcr", discard=True)

        for i in range(0, 200):
            p.mag_mix("96-pcr", pcr, "30:second", "60:hertz",
                      center=float(i) / 100, amplitude=0)
            assert (len(p.instructions[-1].groups[0]) == i * 4 + 1)
            p.mag_collect("96-pcr", pcr, 5, "30:second",
                          bottom_position=float(i) / 100)
            assert (len(p.instructions[-1].groups[0]) == i * 4 + 2)
            p.mag_incubate("96-pcr", pcr, "30:minute",
                           tip_position=float(i) / 100)
            assert (len(p.instructions[-1].groups[0]) == i * 4 + 3)
            p.mag_release("96-pcr", pcr, "30:second", "1:hertz",
                          center=float(i) / 100, amplitude=0)
            assert (len(p.instructions[-1].groups[0]) == i * 4 + 4)

        for i in range(-1, 3, 4):
            with pytest.raises(ValueError):
                p.mag_mix("96-pcr", pcr, "30:second", "60:hertz",
                          center=i, amplitude=0)
            with pytest.raises(ValueError):
                p.mag_collect("96-pcr", pcr, 5, "30:second", bottom_position=i)
            with pytest.raises(ValueError):
                p.mag_incubate("96-pcr", pcr, "30:minute", tip_position=i)
            with pytest.raises(ValueError):
                p.mag_release("96-pcr", pcr, "30:second", "1:hertz",
                              center=i, amplitude=0)

    def test_amplitude_valid(self, dummy_protocol):
        p = dummy_protocol

        pcr = p.ref("pcr", None, "96-pcr", discard=True)

        for i in range(0, 100):
            p.mag_mix("96-pcr", pcr, "30:second", "60:hertz",
                      center=1, amplitude=float(i) / 100)
            assert (len(p.instructions[-1].groups[0]) == i * 2 + 1)
            p.mag_release("96-pcr", pcr, "30:second", "1:hertz",
                          center=1, amplitude=float(i) / 100)
            assert (len(p.instructions[-1].groups[0]) == i * 2 + 2)

        for i in range(-1, 2, 3):
            with pytest.raises(ValueError):
                p.mag_mix("96-pcr", pcr, "30:second", "60:hertz",
                          center=1, amplitude=i)
            with pytest.raises(ValueError):
                p.mag_release("96-pcr", pcr, "30:second", "1:hertz",
                              center=1, amplitude=i)

    def test_mag_append(self, dummy_protocol):
        p = dummy_protocol

        pcrs = [p.ref("pcr_%s" % i, None, "96-pcr", storage="cold_20")
                for i in range(7)]

        pcr = pcrs[0]

        p.mag_dry("96-pcr", pcr, "30:minute", new_tip=False,
                  new_instruction=False)
        assert (len(p.instructions[-1].groups[0]) == 1)
        assert (len(p.instructions[-1].groups) == 1)

        p.mag_dry("96-pcr", pcr, "30:minute", new_tip=True,
                  new_instruction=False)
        assert (len(p.instructions[-1].groups) == 2)
        assert (len(p.instructions) == 1)

        p.mag_dry("96-pcr", pcr, "30:minute", new_tip=True,
                  new_instruction=True)
        assert (len(p.instructions) == 2)

        for plate in pcrs:
            p.mag_dry("96-pcr", plate, "30:minute", new_tip=False,
                      new_instruction=False)
            assert (len(p.instructions) == 2)

        with pytest.raises(RuntimeError):
            pcr_too_many = p.ref("pcr_7", None, "96-pcr", discard=True)
            p.mag_dry("96-pcr", pcr_too_many, "30:minute",
                      new_tip=False, new_instruction=False)

        p.mag_dry("96-pcr", pcr, "30:minute", new_tip=True,
                  new_instruction=True)
        assert (len(p.instructions) == 3)

        p.mag_dry("96-pcr", pcr, "30:minute", new_tip=True,
                  new_instruction=False)
        assert (len(p.instructions[-1].groups) == 2)

        with pytest.raises(RuntimeError):
            for plate in pcrs:
                p.mag_dry("96-pcr", plate, "30:minute", new_tip=False,
                          new_instruction=False)

    def test_remove_cover(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("96-deep-kf", None, "96-deep-kf", discard=True)
        p.cover(c)
        p.mag_mix("96-deep", c, "30:second", "60:hertz", center=0.75,
                  amplitude=0.25, magnetize=True, temperature=None,
                  new_tip=False, new_instruction=False)
        assert p.instructions[-2].op == "uncover"


class TestAutopick:

    def test_autopick(self, dummy_protocol):
        p = dummy_protocol
        dest_plate = p.ref("dest", None, "96-flat", discard=True)
        p.refs["agar_plate"] = Ref("agar_plate", {"reserve": "ki17reefwqq3sq",
                                   "discard": True},
                                   Container(None, p.container_type("6-flat"),
                                             name="agar_plate"))

        agar_plate = Container(None, p.container_type("6-flat"),
                               name="agar_plate")
        p.refs["agar_plate_1"] = Ref("agar_plate_1",
                                     {"reserve": "ki17reefwqq3sq",
                                      "discard": True},
                                     Container(None, p.container_type("6-flat"),
                                               name="agar_plate_1"))

        agar_plate_1 = Container(
            None, p.container_type("6-flat"), name="agar_plate_1")

        p.autopick([agar_plate.well(0), agar_plate.well(1)],
                   [dest_plate.well(1)] * 4, min_abort=0,
                   dataref="0", newpick=False)

        assert (len(p.instructions) == 1)
        assert (len(p.instructions[0].groups) == 1)
        assert (len(p.instructions[0].groups[0]["from"]) == 2)

        p.autopick([agar_plate.well(0), agar_plate.well(1)],
                   [dest_plate.well(1)] * 4, min_abort=0,
                   dataref="1", newpick=True)

        assert (len(p.instructions) == 2)

        p.autopick([agar_plate.well(0), agar_plate.well(1)],
                   [dest_plate.well(1)] * 4, min_abort=0,
                   dataref="1", newpick=False)

        assert (len(p.instructions) == 2)

        for i in range(20):
            p.autopick([agar_plate.well(i % 6), agar_plate.well((i + 1) % 6)],
                       [dest_plate.well(i % 96)] * 4, min_abort=i,
                       dataref="1", newpick=False)

        assert (len(p.instructions) == 2)

        p.autopick([agar_plate_1.well(0), agar_plate_1.well(1)],
                   [dest_plate.well(1)] * 4, min_abort=0,
                   dataref="1", newpick=False)

        assert (len(p.instructions) == 3)

        p.autopick([agar_plate_1.well(0), agar_plate_1.well(1)],
                   [dest_plate.well(1)] * 4, min_abort=0,
                   dataref="2", newpick=False)

        assert (len(p.instructions) == 4)

        with pytest.raises(RuntimeError):
            p.autopick([agar_plate.well(0), agar_plate_1.well(1)],
                       [dest_plate.well(1)] * 4, min_abort=0,
                       dataref="1", newpick=False)


class TestMeasureConcentration:

    def test_measure_concentration_single_well(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref("test_plate", id=None, cont_type="96-flat",
                           storage=None, discard=True)
        for well in test_plate.all_wells():
            well.set_volume("150:microliter")
        p.measure_concentration(wells=test_plate.well(0),
                                dataref="mc_test", measurement="DNA",
                                volume=Unit(2, "microliter"))
        assert (len(p.instructions) == 1)

    def test_measure_concentration_multi_well(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref("test_plate", id=None, cont_type="96-flat",
                           storage=None, discard=True)
        for well in test_plate.all_wells():
            well.set_volume("150:microliter")
        p.measure_concentration(wells=test_plate.wells_from(0, 96),
                                dataref="mc_test", measurement="DNA",
                                volume=Unit(2, "microliter"))
        assert (len(p.instructions) == 1)

    def test_measure_concentration_multi_sample_class(self, dummy_protocol):
        sample_classes = ["ssDNA", "DNA", "RNA", "protein"]
        p = dummy_protocol
        test_plate = p.ref("test_plate", id=None, cont_type="96-flat",
                           storage=None, discard=True)
        for well in test_plate.all_wells():
            well.set_volume("150:microliter")
        for i, sample_class in enumerate(sample_classes):
            p.measure_concentration(wells=test_plate.well(i),
                                    dataref="mc_test_%s" % sample_class,
                                    measurement=sample_class,
                                    volume=Unit(2, "microliter"))
            assert (p.as_dict()["instructions"][i]["measurement"] ==
                    sample_class)
        assert (len(p.instructions) == 4)


class TestMeasureMass:

    def test_measure_mass_single_container(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref("test_plate", id=None, cont_type="96-flat",
                           storage=None, discard=True)
        p.measure_mass(test_plate, "test_ref")
        assert (len(p.instructions) == 1)

    def test_measure_mass_list_containers(self, dummy_protocol):
        p = dummy_protocol
        test_plates = [p.ref("test_plate_%s" % i, id=None, cont_type="96-flat",
                             storage=None, discard=True) for i in range(5)]
        p.measure_mass(test_plates, "test_ref")
        assert (len(p.instructions) == 1)

    def test_measure_mass_bad_list(self, dummy_protocol):
        p = dummy_protocol
        test_plates = [p.ref("test_plate_%s" % i, id=None, cont_type="96-flat",
                             storage=None, discard=True) for i in range(5)]
        test_plates.append("foo")
        with pytest.raises(TypeError):
            p.measure_mass(test_plates, "test_ref")

    def test_measure_mass_bad_input(self, dummy_protocol):
        p = dummy_protocol
        with pytest.raises(TypeError):
            p.measure_mass("foo", "test_ref")


class TestMeasureVolume:

    def test_measure_volume_single_well(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref("test_plate", id=None, cont_type="96-flat",
                           storage=None, discard=True)
        p.measure_volume(test_plate.well(0), "test_ref")
        assert (len(p.instructions) == 1)

    def test_measure_volume_list_well(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref("test_plate", id=None, cont_type="96-flat",
                           storage=None, discard=True)
        p.measure_volume(test_plate.wells_from(0, 12), "test_ref")
        assert (len(p.instructions) == 1)


class TestSpin:

    def test_spin_default(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref("test_plate", id=None, cont_type="96-flat",
                           storage=None, discard=True)
        p.spin(test_plate, "1000:g", "20:minute")
        p.spin(test_plate, "1000:g", "20:minute", flow_direction="outward")
        p.spin(test_plate, "1000:g", "20:minute",
               spin_direction=["ccw", "cw", "ccw"])
        p.spin(test_plate, "1000:g", "20:minute", flow_direction="inward")
        assert (len(p.instructions) == 7)
        with pytest.raises(AttributeError):
            p.instructions[1].flow_direction
        with pytest.raises(AttributeError):
            p.instructions[1].spin_direction
        assert (p.instructions[3].flow_direction == "outward")
        assert (p.instructions[3].spin_direction == ["cw", "ccw"])
        with pytest.raises(AttributeError):
            p.instructions[5].flow_direction
        assert (p.instructions[5].spin_direction == ["ccw", "cw", "ccw"])
        assert (p.instructions[6].flow_direction == "inward")
        assert (p.instructions[6].spin_direction == ["cw"])

    def test_spin_bad_values(self):
        p = Protocol()
        test_plate2 = p.ref("test_plate2", id=None, cont_type="96-flat",
                            storage=None, discard=True)
        with pytest.raises(ValueError):
            p.spin(test_plate2, "1000:g", "20:minute",
                   flow_direction="bad_value")
        with pytest.raises(ValueError):
            p.spin(test_plate2, "1000:g", "20:minute",
                   spin_direction=["cw", "bad_value"])
        with pytest.raises(TypeError):
            p.spin(test_plate2, "1000:g", "20:minute", spin_direction={})
        with pytest.raises(ValueError):
            p.spin(test_plate2, "1000:g", "20:minute", spin_direction=[])


class TestGelPurify:

    def test_gel_purify_lane_set(self, dummy_protocol):
        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr",
                             discard=True).wells_from(0, 9)
        extract_wells = [p.ref("extract_%s" % i, None, "micro-1.5",
                               storage="cold_4").well(0)for i in sample_wells]
        extract_too_many_samples = [
            {
                "source": sample_wells[i],
                "band_list": [{
                    "band_size_range": {"min_bp": 0, "max_bp": 10},
                    "elution_volume": Unit("5:microliter"),
                    "elution_buffer": "water",
                    "destination": d
                }],
                "lane": i,
                "gel": None
            } for i, d in enumerate(extract_wells)
        ]
        with pytest.raises(RuntimeError):
            p.gel_purify(extract_too_many_samples,
                         "10:microliter", "size_select(8,0.8%)", "ladder1",
                         "gel_purify_test")
        extract = extract_too_many_samples[:8]
        p.gel_purify(extract, "10:microliter",
                     "size_select(8,0.8%)", "ladder1", "gel_purify_test")
        assert (len(p.instructions) == 1)
        with pytest.raises(KeyError):
            p.gel_purify({"broken": "extract"}, "10:microliter",
                         "size_select(8,0.8%)", "ladder1", "gel_purify_test")
        extract[2]["band_list"][0]["band_size_range"]["min_bp"] = 20
        with pytest.raises(ValueError):
            p.gel_purify(extract, "10:microliter",
                         "size_select(8,0.8%)", "ladder1", "gel_purify_test")
        del extract[2]["band_list"][0]["band_size_range"]
        with pytest.raises(KeyError):
            p.gel_purify(extract, "10:microliter",
                         "size_select(8,0.8%)", "ladder1", "gel_purify_test")

    def test_gel_purify_no_lane(self, dummy_protocol):
        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr",
                             discard=True).wells_from(0, 20)
        extract_wells = [p.ref("extract_%s" % i, None, "micro-1.5",
                               storage="cold_4").well(0)for i in sample_wells]
        extract = [
            {
                "source": sample_wells[i],
                "band_list": [{
                    "band_size_range": {"min_bp": 0, "max_bp": 10},
                    "elution_volume": Unit("5:microliter"),
                    "elution_buffer": "water",
                    "destination": d
                }],
                "lane": None,
                "gel": None
            } for i, d in enumerate(extract_wells)
        ]
        p.gel_purify(extract, "10:microliter",
                     "size_select(8,0.8%)", "ladder1", "gel_purify_test")
        assert (len(p.instructions) == 3)
        assert (p.instructions[0].extract[1]["lane"] == 1)
        assert (p.instructions[2].extract[-1]["lane"] == 3)

    def test_gel_purify_one_lane(self, dummy_protocol):
        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr",
                             discard=True).wells_from(0, 8)
        extract_wells = [p.ref("extract_%s" % i, None, "micro-1.5",
                               storage="cold_4").well(0)for i in sample_wells]
        extract = [
            {
                "source": sample_wells[i],
                "band_list": [{
                    "band_size_range": {"min_bp": 0, "max_bp": 10},
                    "elution_volume": Unit("5:microliter"),
                    "elution_buffer": "water",
                    "destination": d
                }],
                "lane": None,
                "gel": None
            } for i, d in enumerate(extract_wells)
        ]
        extract[7]["lane"] = 5
        with pytest.raises(RuntimeError):
            p.gel_purify(extract, "10:microliter",
                         "size_select(8,0.8%)", "ladder1", "gel_purify_test")
        extract[7]["lane"] = None
        p.gel_purify(extract, "10:microliter",
                     "size_select(8,0.8%)", "ladder1", "gel_purify_test")
        assert (len(p.instructions) == 1)
        assert (p.instructions[-1].extract[0]["lane"] == 0)
        assert (p.instructions[0].extract[7]["lane"] == 7)

    def test_make_gel_extract_params(self, dummy_protocol):
        from autoprotocol.util import make_gel_extract_params
        from autoprotocol.util import make_band_param

        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr",
                             discard=True).wells_from(0, 8)
        extract_wells = [p.ref("extract_" + str(i), None, "micro-1.5",
                               storage="cold_4").well(0) for i in sample_wells]
        extracts = [
            make_gel_extract_params(w, make_band_param("TE",
                                                       "5:microliter", 80, 79,
                                                       extract_wells[i]))
            for i, w in enumerate(sample_wells)]
        with pytest.raises(RuntimeError):
            p.gel_purify(extracts, "10:microliter", "bad_gel",
                         "ladder1", "gel_purify_test")
        p.gel_purify(extracts, "10:microliter",
                     "size_select(8,0.8%)", "ladder1", "gel_purify_test")
        assert (len(p.instructions) == 1)
        assert (p.instructions[0].extract[-1]["lane"] == 7)
        assert (p.instructions[-1].extract[0]["lane"] == 0)
        assert (p.instructions[-1].extract[1]["lane"] == 1)

    def test_gel_purify_extract_param_checker(self, dummy_protocol):
        from autoprotocol.util import make_gel_extract_params
        from autoprotocol.util import make_band_param

        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr",
                             discard=True).wells_from(0, 8)
        extract_wells = [p.ref("extract_" + str(i), None, "micro-1.5",
                               storage="cold_4").well(0) for i in sample_wells]
        extracts = [
            make_gel_extract_params(w, make_band_param("TE",
                                                       "5:microliter", 80, 79,
                                                       extract_wells[i]))
            for i, w in enumerate(sample_wells)]
        extracts[7]["band_list"][0]["elution_volume"] = "not_a_unit"
        with pytest.raises(ValueError):
            p.gel_purify(extracts, "5:microliter",
                         "size_select(8,0.8%)", "ladder1", "gel_purify_test")
        extracts[3]["band_list"][0]["destination"] = "not_a_well"
        with pytest.raises(ValueError):
            p.gel_purify(extracts[:4], "5:microliter",
                         "size_select(8,0.8%)", "ladder1", "gel_purify_test")


class TestIlluminaSeq:

    def test_illumina_seq(self, dummy_protocol):
        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr",
                             discard=True).wells_from(0, 8)
        p.illuminaseq("PE", [{"object": sample_wells[0],
                              "library_concentration": 1.0},
                             {"object": sample_wells[1],
                              "library_concentration": 2}],
                      "nextseq", "mid", 'none', 34, "dataref")

        assert (len(p.instructions) == 1)

        p.illuminaseq("PE",
                      [
                          {"object": sample_wells[0],
                              "library_concentration": 1.0},
                          {"object": sample_wells[
                              1], "library_concentration": 5.32},
                          {"object": sample_wells[2],
                              "library_concentration": 54},
                          {"object": sample_wells[3],
                              "library_concentration": 20},
                          {"object": sample_wells[4],
                              "library_concentration": 23},
                          {"object": sample_wells[5],
                              "library_concentration": 23},
                          {"object": sample_wells[6],
                              "library_concentration": 21},
                          {"object": sample_wells[7],
                              "library_concentration": 62}
                      ],
                      "hiseq", "rapid", 'none', 250, "dataref",
                      {"read_2": 300, "read_1": 100,
                       "index_1": 4, "index_2": 12})
        assert (len(p.instructions) == 2)
        assert (len(p.instructions[1].lanes) == 8)

    def test_illumina_seq_default(self, dummy_protocol):
        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr",
                             discard=True).wells_from(0, 8)
        p.illuminaseq("PE", [{"object": sample_wells[0],
                              "library_concentration": 1.0},
                             {"object": sample_wells[1],
                              "library_concentration": 2}],
                      "nextseq", "mid", 'none', 34, "dataref", {"read_1": 100})

        assert (len(p.instructions) == 1)
        assert ("index_1" in p.instructions[0].cycles)
        assert (0 == p.instructions[0].cycles["index_2"])

    def test_illumina_bad_params(self, dummy_protocol):
        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr",
                             discard=True).wells_from(0, 3)
        with pytest.raises(TypeError):
            p.illuminaseq("PE", "not_a_list", "nextseq",
                          "mid", 'none', 250, "bad_lane_param")
        with pytest.raises(ValueError):
            p.illuminaseq("PE", [{"object": sample_wells[0],
                                  "library_concentration": 1.0},
                                 {"object": sample_wells[1],
                                  "library_concentration": 2}],
                          "nextseq", "rapid", 'none', 34, "dataref")
        with pytest.raises(ValueError):
            p.illuminaseq("PE",
                          [
                              {"object": sample_wells[
                                  0], "library_concentration": 1.0},
                              {"object": sample_wells[
                                  1], "library_concentration": 2}
                          ],
                          "miseq", "high", 'none', 250, "not_enough_lanes")
        with pytest.raises(RuntimeError):
            p.illuminaseq("SR",
                          [
                              {"object": sample_wells[
                                  0], "library_concentration": 1.0},
                              {"object": sample_wells[
                                  1], "library_concentration": 2}
                          ],
                          "nextseq", "high", "none", 250, "wrong_seq",
                          {"read_2": 500, "read_1": 2})
        with pytest.raises(ValueError):
            p.illuminaseq("PE",
                          [
                              {"object": sample_wells[
                                  0], "library_concentration": 1.0},
                              {"object": sample_wells[
                                  1], "library_concentration": 2}
                          ],
                          "nextseq", "high", "none", 250, "index_too_high",
                          {"read_2": 300, "read_1": 100,
                           "index_1": 4, "index_2": 13})


class TestCoverStatus:

    def test_ref_cover_status(self, dummy_protocol):
        p = dummy_protocol
        cont = p.ref("cont", None, "96-pcr", discard=True, cover="ultra-clear")
        assert (cont.cover)
        assert (cont.cover == "ultra-clear")

    def test_ref_invalid_seal(self, dummy_protocol):
        p = dummy_protocol
        with pytest.raises(AttributeError):
            cont = p.ref("cont", None, "96-pcr", discard=True, cover="clear")
            assert (not cont.cover)
            assert (cont.cover != "clear")
            assert (not p.refs[cont.name].opts['cover'])

    def test_implicit_unseal(self, dummy_protocol):
        p = dummy_protocol
        cont = p.ref("cont", None, "96-pcr", discard=True)
        assert (not cont.cover)
        p.seal(cont)
        assert (cont.cover)
        assert (cont.cover == "ultra-clear")
        p.mix(cont.well(0))
        assert (not cont.cover)

    def test_implicit_uncover(self, dummy_protocol):
        p = dummy_protocol
        cont = p.ref("cont", None, "96-flat", discard=True)
        assert (not cont.cover)
        p.cover(cont, "universal")
        assert (cont.cover)
        assert (cont.cover == "universal")
        p.mix(cont.well(0))
        assert (not cont.cover)


class TestDispense:

    def test_resource_id(self, dummy_protocol):
        p = dummy_protocol
        container = p.ref("Test_Container", cont_type="96-pcr", discard=True)
        p.dispense(container, "rs17gmh5wafm5p",
                   [{"column": 0, "volume": "10:ul"}], is_resource_id=True)
        assert (Unit(10, "microliter") == container.well("B1").volume)
        assert (container.well(3).volume is None)
        assert (hasattr(p.instructions[0], "resource_id"))
        with pytest.raises(AttributeError):
            p.instructions[0].reagent

    def test_reagent(self, dummy_protocol):
        p = dummy_protocol
        container = p.ref("Test_Container", cont_type="96-pcr", discard=True)
        p.dispense_full_plate(container, "rs17gmh5wafm5p", "10:ul",
                              is_resource_id=False)
        assert (Unit(10, "microliter") == container.well("E1").volume)
        assert (container.well(3).volume is not None)
        assert (hasattr(p.instructions[0], "reagent"))
        with pytest.raises(AttributeError):
            p.instructions[0].resource_id

    def test_step_size(self, dummy_protocol):
        # Initialize protocol and container
        p = dummy_protocol
        container = p.ref("Test_Container", cont_type="96-pcr", discard=True)

        # Test p.dispense while setting step_size to None
        p.dispense(container, "rs17gmh5wafm5p",
                   [{"column": 0, "volume": "10:microliter"}],
                   is_resource_id=True, step_size=None)
        assert ("step_size" not in p.instructions[-1].data)
        assert ("x_human" not in p.instructions[-1].data)

        # Test p.dispense while using step_size default
        p.dispense(container, "rs17gmh5wafm5p",
                   [{"column": 0, "volume": "10:microliter"}],
                   is_resource_id=True)
        assert (p.instructions[-1].data["step_size"] == Unit(5, "microliter"))
        assert ("x_human" not in p.instructions[-1].data)

        # Test p.dispense with step_size of 5 microliter
        p.dispense(container, "rs17gmh5wafm5p",
                   [{"column": 1, "volume": "10:microliter"}],
                   is_resource_id=True, step_size="5:microliter")
        assert (p.instructions[-1].data["step_size"] == Unit(5, "microliter"))
        assert ("x_human" not in p.instructions[-1].data)

        # Test p.dispense with step_size of 0.5 microliter
        p.dispense(container, "rs17gmh5wafm5p",
                   [{"column": 2, "volume": "0.5:microliter"}],
                   is_resource_id=True, step_size="0.5:microliter")
        assert (p.instructions[-1].data["step_size"] == Unit(0.5, "microliter"))
        assert (p.instructions[-1].data["x_human"] is True)

        # Test p.dispense with step_size of 0.5 microliter,
        # submitted as a Unit object
        p.dispense(container, "rs17gmh5wafm5p",
                   [{"column": 2, "volume": "0.5:microliter"}],
                   is_resource_id=True, step_size=Unit(0.5, "microliter"))
        assert (p.instructions[-1].data["step_size"] == Unit(0.5, "microliter"))
        assert (p.instructions[-1].data["x_human"] is True)

        # Test p.dispense with step_size in nanoliters
        p.dispense(container, "rs17gmh5wafm5p",
                   [{"column": 2, "volume": "0.5:microliter"}],
                   is_resource_id=True, step_size="500:nanoliter")
        assert (p.instructions[-1].data["step_size"] == Unit(0.5, "microliter"))
        assert (p.instructions[-1].data["x_human"] is True)

        # Test bad type for step_size
        with pytest.raises(TypeError):
            p.dispense(container, "rs17gmh5wafm5p",
                       [{"column": 1, "volume": "10:microliter"}],
                       is_resource_id=True, step_size="5:micrometer")
        with pytest.raises(TypeError):
            p.dispense(container, "rs17gmh5wafm5p",
                       [{"column": 1, "volume": "10:microliter"}],
                       is_resource_id=True, step_size="5microliter")
        with pytest.raises(TypeError):
            p.dispense(container, "rs17gmh5wafm5p",
                       [{"column": 1, "volume": "10:microliter"}],
                       is_resource_id=True, step_size=5)

        # Test disallowed step_size
        with pytest.raises(ValueError):
            p.dispense(container, "rs17gmh5wafm5p",
                       [{"column": 1, "volume": "10:microliter"}],
                       is_resource_id=True, step_size="1:microliter")

        # Test volume that is not an integer multiple of step_size
        with pytest.raises(RuntimeError):
            p.dispense(container, "rs17gmh5wafm5p",
                       [{"column": 1, "volume": "11:microliter"}],
                       is_resource_id=True, step_size="5:microliter")
        with pytest.raises(RuntimeError):
            p.dispense(container, "rs17gmh5wafm5p",
                       [{"column": 2, "volume": "1.6:microliter"}],
                       is_resource_id=True, step_size="0.5:microliter")

        # Test p.dispense_full_plate while setting step_size to None
        p.dispense_full_plate(container, "rs17gmh5wafm5p",
                              "10:microliter", is_resource_id=True,
                              step_size=None)
        assert ("step_size" not in p.instructions[-1].data)
        assert ("x_human" not in p.instructions[-1].data)

        # Test p.dispense_full_plate while using step_size default
        p.dispense_full_plate(container, "rs17gmh5wafm5p", "10:microliter",
                              is_resource_id=True)
        assert (p.instructions[-1].data["step_size"] == Unit(5, "microliter"))
        assert ("x_human" not in p.instructions[-1].data)

        # Test p.dispense_full_plate with step_size of 5 microliter
        p.dispense_full_plate(container, "rs17gmh5wafm5p", "10:microliter",
                              is_resource_id=True, step_size="5:microliter")
        assert (p.instructions[-1].data["step_size"] == Unit(5, "microliter"))
        assert ("x_human" not in p.instructions[-1].data)

        # Test p.dispense_full_plate with step_size of 0.5 microliter
        p.dispense_full_plate(container, "rs17gmh5wafm5p", "0.5:microliter",
                              is_resource_id=True, step_size="0.5:microliter")
        assert (p.instructions[-1].data["step_size"] == Unit(0.5, "microliter"))
        assert (p.instructions[-1].data["x_human"] is True)

        # Test p.dispense_full_plate with step_size of 0.5 microliter,
        # submitted as a Unit object
        p.dispense_full_plate(container, "rs17gmh5wafm5p", "0.5:microliter",
                              is_resource_id=True,
                              step_size=Unit(0.5, "microliter"))
        assert (p.instructions[-1].data["step_size"] == Unit(0.5, "microliter"))
        assert (p.instructions[-1].data["x_human"] is True)

        # Test p.dispense_full_plate with step_size in nanoliters
        p.dispense_full_plate(container, "rs17gmh5wafm5p", "0.5:microliter",
                              is_resource_id=True, step_size="500:nanoliter")
        assert (p.instructions[-1].data["step_size"] == Unit(0.5, "microliter"))
        assert (p.instructions[-1].data["x_human"] is True)

        # Test bad type for step_size
        with pytest.raises(TypeError):
            p.dispense_full_plate(container, "rs17gmh5wafm5p", "10:microliter",
                                  is_resource_id=True, step_size="5:micrometer")
        with pytest.raises(TypeError):
            p.dispense_full_plate(container, "rs17gmh5wafm5p", "10:microliter",
                                  is_resource_id=True, step_size="5microliter")
        with pytest.raises(TypeError):
            p.dispense_full_plate(container, "rs17gmh5wafm5p", "10:microliter",
                                  is_resource_id=True, step_size=5)

        # Test disallowed step_size
        with pytest.raises(ValueError):
            p.dispense_full_plate(container, "rs17gmh5wafm5p", "10:microliter",
                                  is_resource_id=True, step_size="1:microliter")

        # Test volume that is not an integer multiple of step_size
        with pytest.raises(RuntimeError):
            p.dispense_full_plate(container, "rs17gmh5wafm5p", "11:microliter",
                                  is_resource_id=True, step_size="5:microliter")
        with pytest.raises(RuntimeError):
            p.dispense_full_plate(container, "rs17gmh5wafm5p", "1.6:microliter",
                                  is_resource_id=True,
                                  step_size="0.5:microliter")

    def test_x_cassette(self, dummy_protocol):
        # Initialize protocol and container
        p = dummy_protocol
        container = p.ref("Test_Container", cont_type="96-pcr", discard=True)

        # Test p.dispense without setting x_cassette
        p.dispense(container, "water",
                   [{"column": 0, "volume": "10:microliter"}])
        assert ("x_cassette" not in p.instructions[-1].data)
        assert (p.instructions[-1].data["step_size"] == Unit(5, "microliter"))
        assert ("x_human" not in p.instructions[-1].data)

        # Test p.dispense with x_cassette specified
        p.dispense(container, "water",
                   [{"column": 1, "volume": "10:microliter"}],
                   step_size="0.5:microliter",
                   x_cassette="ThermoFisher #24073295")
        assert (p.instructions[-1].data["x_cassette"] ==
                "ThermoFisher #24073295")
        assert (p.instructions[-1].data["step_size"] == Unit(0.5, "microliter"))
        assert (p.instructions[-1].data["x_human"] is True)

        # Test bad x_cassette type
        with pytest.raises(ValueError):
            p.dispense(container, "water",
                       [{"column": 1, "volume": "10:microliter"}],
                       step_size="0.5:microliter",
                       x_cassette="bad cassette type")

        # Test mismatch between step_size and x_cassette
        with pytest.raises(ValueError):
            p.dispense(container, "water",
                       [{"column": 1, "volume": "10:microliter"}],
                       step_size="5:microliter",
                       x_cassette="ThermoFisher #24073295")

        # Test specification of x_cassette without step_size
        with pytest.raises(ValueError):
            p.dispense(container, "water",
                       [{"column": 1, "volume": "10:microliter"}],
                       x_cassette="ThermoFisher #24073295")

        # Test p.dispense_full_plate without setting x_cassette
        p.dispense_full_plate(container, "water", "10:microliter")
        assert ("x_cassette" not in p.instructions[-1].data)
        assert (p.instructions[-1].data["step_size"] == Unit(5, "microliter"))
        assert ("x_human" not in p.instructions[-1].data)

        # Test p.dispense_full_plate with x_cassette specified
        p.dispense_full_plate(container, "water", "10:microliter",
                              step_size="0.5:microliter",
                              x_cassette="ThermoFisher #24073295")
        assert (p.instructions[-1].data["x_cassette"] ==
                "ThermoFisher #24073295")
        assert (p.instructions[-1].data["step_size"] == Unit(0.5, "microliter"))
        assert (p.instructions[-1].data["x_human"] is True)

        # Test bad x_cassette type
        with pytest.raises(ValueError):
            p.dispense_full_plate(container, "water", "10:microliter",
                                  step_size="0.5:microliter",
                                  x_cassette="bad cassette type")

        # Test mismatch between step_size and x_cassette
        with pytest.raises(ValueError):
            p.dispense_full_plate(container, "water", "10:microliter",
                                  step_size="5:microliter",
                                  x_cassette="ThermoFisher #24073295")

        # Test specification of x_cassette without step_size
        with pytest.raises(ValueError):
            p.dispense_full_plate(container, "water", "10:microliter",
                                  x_cassette="ThermoFisher #24073295")

    def test_reagent_source(self, dummy_protocol):
        # Initialize protocol and containers for testing dispense
        p = dummy_protocol
        dest1 = p.ref("destination_plate_1", cont_type="96-pcr", discard=True)
        src1 = p.ref("source_well_1", None, cont_type="micro-2.0",
                     discard=True).well(0)
        src1.volume = Unit(2, "milliliter")

        dest2 = p.ref("destination_plate_2", cont_type="96-pcr", discard=True)
        src2 = p.ref("source_well_2", None, cont_type="96-deep", discard=True,
                     cover="universal").well(0)

        dest3 = p.ref("destination_plate_3", cont_type="96-pcr", discard=True)

        dummy_plate = p.ref("dummy_plate", cont_type="96-pcr", discard=True)

        # Test p.dispense with reagent
        p.dispense(dest3, "water", [{"column": 0, "volume": "10:microliter"}])
        assert (p.instructions[-1].data["reagent"] == "water")
        assert ("resource_id" not in p.instructions[-1].data)
        assert ("reagent_source" not in p.instructions[-1].data)
        assert ("x_human" not in p.instructions[-1].data)

        # Test p.dispense with resource_id
        p.dispense(dest3, "rs17gmh5wafm5p",
                   [{"column": 0, "volume": "10:microliter"}],
                   is_resource_id=True)
        assert ("reagent" not in p.instructions[-1].data)
        assert (p.instructions[-1].data["resource_id"] == "rs17gmh5wafm5p")
        assert ("reagent_source" not in p.instructions[-1].data)
        assert ("x_human" not in p.instructions[-1].data)

        p.dispense(dest1, src1, [{"column": 0, "volume": "10:microliter"},
                   {"column": 1, "volume": "30:microliter"}])
        assert (src1.container.cover is None)
        assert ("reagent" not in p.instructions[-1].data)
        assert ("resource_id" not in p.instructions[-1].data)
        assert (p.instructions[-1].data["reagent_source"] == src1)
        assert (p.instructions[-1].data["x_human"] is True)

        # Check volumes
        for well in dest1.wells_from(0, 8, columnwise=True):
            assert (well.volume == Unit(10, "microliter"))
        for well in dest1.wells_from(1, 8, columnwise=True):
            assert (well.volume == Unit(30, "microliter"))
        assert (src1.volume == Unit(1680, "microliter"))

        # Test improper inputs for reagent
        with pytest.raises(TypeError):
            p.dispense(dest1, 1, [{"column": 0, "volume": "10:microliter"},
                       {"column": 1, "volume": "30:microliter"}])
        with pytest.raises(TypeError):
            p.dispense(dest1, dummy_plate.all_wells(),
                       [{"column": 0, "volume": "10:microliter"},
                       {"column": 1, "volume": "30:microliter"}])

        # Test p.dispense_full_plate with reagent
        p.dispense_full_plate(dest3, "water", "10:microliter")
        assert (p.instructions[-1].data["reagent"] == "water")
        assert ("resource_id" not in p.instructions[-1].data)
        assert ("reagent_source" not in p.instructions[-1].data)
        assert ("x_human" not in p.instructions[-1].data)

        # Test p.dispense_full_plate with resource_id
        p.dispense_full_plate(dest3, "rs17gmh5wafm5p", "10:microliter",
                              is_resource_id=True)
        assert ("reagent" not in p.instructions[-1].data)
        assert (p.instructions[-1].data["resource_id"] == "rs17gmh5wafm5p")
        assert ("reagent_source" not in p.instructions[-1].data)
        assert ("x_human" not in p.instructions[-1].data)

        # Test p.dispense_full_plate with reagent_source
        assert(src2.container.cover == "universal")

        p.dispense_full_plate(dest2, src2, "10:microliter")
        assert (src2.container.cover is None)
        assert ("reagent" not in p.instructions[-1].data)
        assert ("resource_id" not in p.instructions[-1].data)
        assert (p.instructions[-1].data["reagent_source"] == src2)
        assert (p.instructions[-1].data["x_human"] is True)

        # Check volumes
        for well in dest2.all_wells():
            assert (well.volume == Unit(10, "microliter"))
        assert (src2.volume == Unit(-960, "microliter"))

        # Test improper inputs for reagent
        with pytest.raises(TypeError):
            p.dispense_full_plate(dest2, 2, "10:microliter")
        with pytest.raises(TypeError):
            p.dispense_full_plate(dest2, dummy_plate.all_wells(),
                                  "10:microliter")


class TestFlowAnalyze:

    def test_default(self, dummy_protocol):
        p = dummy_protocol
        container = p.ref("Test_Container1", cont_type="96-pcr", discard=True)
        container2 = p.ref("Test_Container2", cont_type="96-flat", discard=True)
        p.cover(container2, lid="standard")
        assert (container2.cover)
        p.flow_analyze(dataref="Test",
                       FSC={"voltage_range": {"low": "230:volt",
                                              "high": "280:volt"}},
                       SSC={"voltage_range": {"low": "230:volt",
                                              "high": "380:volt"}},
                       neg_controls=[{"well": container.well(0),
                                      "volume": "200:microliter",
                                      "channel": ["FSC", "SSC"]}],
                       samples=[{"well": container2.well(0),
                                 "volume": "200:microliter"},
                                {"well": container2.well(1),
                                 "volume": "200:microliter"},
                                {"well": container2.well(2),
                                 "volume": "200:microliter"}])
        assert (not container2.cover)
        assert (p.instructions[1].op == "uncover")
        assert (hasattr(p.instructions[2], "channels"))

    def test_flow_bad_params(self, dummy_protocol):
        p = dummy_protocol
        container = p.ref("Test_Container1", cont_type="96-pcr", discard=True)
        container2 = p.ref("Test_Container2", cont_type="96-flat", discard=True)
        colors = [
            {"excitation_wavelength": "4:not_a_unit",
             "emission_wavelength": "4:nanometer",
             "name": "some_name"}
        ]
        with pytest.raises(TypeError):
            p.flow_analyze(dataref="Test",
                           FSC=[{"voltage_range": {"low": "230:volt",
                                "high": "380:volt"}}],
                           SSC={"voltage_range": {"low": "230:volt",
                                "high": "380:volt"}},
                           neg_controls=[{"well": container.well(0),
                                          "volume": "200:microliter",
                                          "channel": ["FSC", "SSC"]}],
                           samples=[{"well": container2.well(0),
                                    "volume": "200:microliter"},
                                    {"well": container2.well(1),
                                     "volume": "200:microliter"},
                                    {"well": container2.well(2),
                                     "volume": "200:microliter"}])
        with pytest.raises(AssertionError):
            p.flow_analyze(dataref="Test",
                           FSC={},
                           SSC={"voltage_range": {"low": "230:volt",
                                                  "high": "380:volt"}},
                           neg_controls=[{"well": container.well(0),
                                          "volume": "200:microliter",
                                          "channel": ["FSC", "SSC"]}],
                           samples=[{"well": container2.well(0),
                                     "volume": "200:microliter"},
                                    {"well": container2.well(1),
                                     "volume": "200:microliter"},
                                    {"well": container2.well(2),
                                     "volume": "200:microliter"}])
        with pytest.raises(TypeError):
            p.flow_analyze(dataref="Test",
                           FSC={"voltage_range": {"low": "230:volt",
                                                  "high": "280:volt"}},
                           SSC={"voltage_range": {"low": "230:volt",
                                                  "high": "380:volt"}},
                           neg_controls=[{"well": container,
                                          "volume": "200:microliter",
                                          "channel": ["FSC", "SSC"]}],
                           samples=[{"well": container2.well(0),
                                     "volume": "200:microliter"},
                                    {"well": container2.well(1),
                                     "volume": "200:microliter"},
                                    {"well": container2.well(2),
                                     "volume": "200:microliter"}])
        with pytest.raises(ValueError):
            p.flow_analyze(dataref="Test",
                           FSC={"voltage_range": {"low": "230:volt",
                                                  "high": "280:volt"}},
                           SSC={"voltage_range": {"low": "230:volt",
                                                  "high": "380:volt"}},
                           neg_controls=[{"well": container.well(0),
                                          "channel": ["FSC", "SSC"]}],
                           samples=[{"well": container2.well(0),
                                     "volume": "200:microliter"},
                                    {"well": container2.well(1),
                                     "volume": "200:microliter"},
                                    {"well": container2.well(2),
                                     "volume": "200:microliter"}])
        with pytest.raises(UnitError):
            p.flow_analyze(dataref="Test",
                           FSC={"voltage_range": {"low": "230:volt",
                                                  "high": "280:volt"}},
                           SSC={"voltage_range": {"low": "230:volt",
                                                  "high": "380:volt"}},
                           neg_controls=[{"well": container.well(0),
                                          "volume": "200:microliter",
                                          "channel": ["FSC", "SSC"]}],
                           samples=[{"well": container2.well(0),
                                     "volume": "200:microliter"},
                                    {"well": container2.well(1),
                                     "volume": "200:microliter"},
                                    {"well": container2.well(2),
                                     "volume": "200:microliter"}],
                           colors=colors)


class TestDyeTest:

    def test_add_dye_to_preview_refs(self, dummy_protocol):
        p1 = dummy_protocol
        c1 = p1.ref("c1", id=None, cont_type="96-pcr", discard=True)
        c1.well(0).set_volume("10:microliter")
        _add_dye_to_preview_refs(p1)

        assert (len(p1.instructions) == 1)
        assert (p1.instructions[0].data["op"] == "provision")
        assert (p1.instructions[0].data["resource_id"] == "rs18qmhr7t9jwq")
        assert (len(p1.instructions[0].data["to"]) == 1)
        assert (p1.instructions[0].data["to"][0]["volume"] ==
                Unit(10, "microliter"))
        assert (p1.instructions[0].data["to"][0]["well"] == c1.well(0))
        assert (c1.well(0).volume == Unit(10, "microliter"))

        p2 = Protocol()
        c2 = p2.ref("c2", id="ctXXXXX", cont_type="96-pcr", discard=True)
        c2.well(0).set_volume("10:microliter")

        with pytest.raises(RuntimeError):
            _add_dye_to_preview_refs(p2)

    def test_convert_provision(self):
        p1 = Protocol()
        c1 = p1.ref("c1", id=None, cont_type="96-pcr", discard=True)
        p1.incubate(c1, where="ambient", duration="1:hour", uncovered=True)
        p1.provision("rs18s8x4qbsvjz", c1.well(0), volumes="10:microliter")
        p1.incubate(c1, where="ambient", duration="1:hour", uncovered=True)
        p1.provision("rs18s8x4qbsvjz", c1.well(0), volumes="10:microliter")
        _convert_provision_instructions(p1, 3, 3)

        assert (p1.instructions[1].data["resource_id"] == "rs18s8x4qbsvjz")
        assert (p1.instructions[3].data["resource_id"] == "rs17gmh5wafm5p")

        with pytest.raises(ValueError):
            _convert_provision_instructions(p1, "2", 3)

        with pytest.raises(ValueError):
            _convert_provision_instructions(p1, 2, "3")

        with pytest.raises(ValueError):
            _convert_provision_instructions(p1, -1, 3)

        with pytest.raises(ValueError):
            _convert_provision_instructions(p1, 4, 5)

        with pytest.raises(ValueError):
            _convert_provision_instructions(p1, 2, 5)

        with pytest.raises(ValueError):
            _convert_provision_instructions(p1, 3, 2)

    def test_convert_dispense(self):
        p1 = Protocol()
        c1 = p1.ref("c1", id=None, cont_type="96-pcr", discard=True)
        p1.incubate(c1, where="ambient", duration="1:hour", uncovered=True)
        p1.dispense(c1, "rs18s8x4qbsvjz",
                    [{"column": 0, "volume": "10:microliter"}],
                    is_resource_id=True)
        p1.dispense(c1, "pbs", [{"column": 1, "volume": "10:microliter"}])
        p1.incubate(c1, where="ambient", duration="1:hour", uncovered=True)
        p1.dispense(c1, "rs18s8x4qbsvjz",
                    [{"column": 2, "volume": "10:microliter"}],
                    is_resource_id=True)
        p1.dispense(c1, "pbs", [{"column": 3, "volume": "10:microliter"}])
        _convert_dispense_instructions(p1, 3, 5)
        assert ("resource_id" in p1.instructions[1].data)
        assert ("reagent" not in p1.instructions[1].data)
        assert ("resource_id" not in p1.instructions[2].data)
        assert ("reagent" in p1.instructions[2].data)
        assert ("resource_id" in p1.instructions[4].data)
        assert ("reagent" not in p1.instructions[4].data)
        assert ("resource_id" in p1.instructions[5].data)
        assert ("reagent" not in p1.instructions[5].data)
        assert (p1.instructions[1].data["resource_id"] == "rs18s8x4qbsvjz")
        assert (p1.instructions[2].data["reagent"] == "pbs")
        assert (p1.instructions[4].data["resource_id"] == "rs17gmh5wafm5p")
        assert (p1.instructions[5].data["resource_id"] == "rs17gmh5wafm5p")

        with pytest.raises(ValueError):
            _convert_dispense_instructions(p1, "3", 5)

        with pytest.raises(ValueError):
            _convert_dispense_instructions(p1, 3, "5")

        with pytest.raises(ValueError):
            _convert_dispense_instructions(p1, -1, 5)

        with pytest.raises(ValueError):
            _convert_dispense_instructions(p1, 6, 7)

        with pytest.raises(ValueError):
            _convert_dispense_instructions(p1, 3, 7)

        with pytest.raises(ValueError):
            _convert_dispense_instructions(p1, 5, 3)


class TestIncubate:

    def test_incubate(self, dummy_protocol):
        p = dummy_protocol
        c1 = p.ref("c1", id=None,
                   cont_type="96-10-spot-vplex-m-pro-inflamm1-MSD",
                   discard=True)

        p.incubate(c1, "ambient", "10:minute", shaking=True,
                   target_temperature="50:celsius",
                   shaking_params={"path": "cw_orbital",
                                   "frequency": "1700:rpm"})
        assert (p.instructions[-1].op == "incubate")

    def test_shaking_params(self, dummy_protocol, dummy_96):
        p = dummy_protocol
        with pytest.raises(KeyError):
            p.incubate(dummy_96, "ambient", "1:minute",
                       shaking_params={"path": "cw_orbital"})
        with pytest.raises(TypeError):
            p.incubate(dummy_96, "ambient", "1:minute",
                       shaking_params="not_dict")
        with pytest.raises(ValueError):
            p.incubate(dummy_96, "ambient", "10:minute",
                       target_temperature="50:celsius",
                       shaking_params={"path": "cw_orbital",
                                       "frequency": "2000:rpm"})

    def test_shaking_freq(self, dummy_protocol, dummy_96):
        p = dummy_protocol
        with pytest.raises(ValueError):
            p.incubate(dummy_96, "ambient", "10:minute",
                       target_temperature="50:celsius",
                       shaking_params={"path": "landscape_linear",
                                       "frequency": "601:rpm"})
        with pytest.raises(ValueError):
            p.incubate(dummy_96, "ambient", "10:minute",
                       target_temperature="50:celsius",
                       shaking_params={"path": "portrait_linear",
                                       "frequency": "401:rpm"})
        with pytest.raises(ValueError):
            p.incubate(dummy_96, "ambient", "10:minute",
                       target_temperature="50:celsius",
                       shaking_params={"path": "ccw_diamond",
                                       "frequency": "701:rpm"})
