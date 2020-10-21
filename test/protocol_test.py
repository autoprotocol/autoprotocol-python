# pragma pylint: disable=missing-docstring,protected-access
# pragma pylint: disable=attribute-defined-outside-init
import pytest
from autoprotocol.container import Container, Well, WellGroup
from autoprotocol.container_type import _CONTAINER_TYPES
from autoprotocol.instruction import (
    Thermocycle,
    Incubate,
    Spin,
    Dispense,
    GelPurify,
    Fluorescence,
    Absorbance,
    Luminescence,
    Instruction,
    SPE,
)
from autoprotocol.protocol import Protocol, Ref
from autoprotocol.unit import Unit, UnitError
from autoprotocol.harness import (
    _add_dye_to_preview_refs,
    _convert_provision_instructions,
    _convert_dispense_instructions,
)
import warnings


class TestProtocolMultipleExist(object):
    def test_multiple_exist(self, dummy_protocol, dummy_96):
        p1 = dummy_protocol
        p2 = Protocol()

        p1.cover(dummy_96)
        p1.incubate(dummy_96, "warm_37", "560:second")
        assert len(p2.instructions) == 0
        assert len(p1.instructions) == 2


class TestProtocolBasic(object):
    def test_basic_protocol(self, dummy_protocol):
        protocol = dummy_protocol
        resource = protocol.ref("resource", None, "96-flat", discard=True)
        pcr = protocol.ref("pcr", None, "96-flat", discard=True)
        bacteria = protocol.ref("bacteria", None, "96-flat", discard=True)

        bacteria_wells = WellGroup(
            [
                bacteria.well("B1"),
                bacteria.well("C5"),
                bacteria.well("A5"),
                bacteria.well("A1"),
            ]
        )

        protocol.transfer(
            resource.well("A1").set_volume("40:microliter"),
            pcr.wells_from("A1", 5),
            "5:microliter",
            one_tip=True,
        )
        protocol.transfer(
            resource.well("A1").set_volume("40:microliter"),
            bacteria_wells,
            "5:microliter",
            one_tip=True,
        )
        # Test for correct number of refs
        assert len(protocol.as_dict()["refs"]) == 3
        assert protocol.as_dict()["refs"]["resource"] == {
            "new": "96-flat",
            "discard": True,
        }

        assert len(protocol.instructions) == 2
        assert protocol.instructions[0].op == "liquid_handle"

        protocol.incubate(bacteria, "warm_37", "30:minute")

        assert len(protocol.instructions) == 4
        assert protocol.instructions[2].op == "cover"
        assert protocol.instructions[3].op == "incubate"
        assert protocol.instructions[3].duration == "30:minute"


class TestProtocolAppendReturn(object):
    def test_protocol_append_return(self, dummy_protocol):
        p = dummy_protocol
        # assert empty list of instructions
        assert len(p.instructions) == 0

        # pylint: disable=protected-access
        inst = p._append_and_return(
            Spin("dummy_ref", "100:meter/second^2", "60:second")
        )
        assert len(p.instructions) == 1
        assert p.instructions[0].op == "spin"
        assert inst.op == "spin"

    def test_protocol_append_return_multiple(self, dummy_protocol):
        p = dummy_protocol

        # pylint: disable=protected-access
        insts = p._append_and_return(
            [
                Incubate("dummy_ref", "ambient", "30:second"),
                Spin("dummy_ref", "2000:rpm", "120:second"),
            ]
        )
        assert len(p.instructions) == 2
        assert p.instructions[0].op == "incubate"
        assert p.instructions[1].op == "spin"

        assert insts[0].op == "incubate"
        assert insts[1].op == "spin"


class TestRef(object):
    def test_duplicates_not_allowed(self, dummy_protocol):
        p = dummy_protocol
        p.ref("test", None, "96-flat", discard=True)
        with pytest.raises(RuntimeError):
            p.ref("test", None, "96-flat", storage="cold_20")
        assert p.refs["test"].opts["discard"]
        assert "where" not in p.refs["test"].opts

    # pragma pylint: disable=expression-not-assigned
    def test_storage_condition_change(self, dummy_protocol):
        p = dummy_protocol
        c1 = p.ref("discard_test", None, "96-flat", storage="cold_20")
        p.cover(c1)
        assert p.refs["discard_test"].opts["store"]["where"] == "cold_20"
        with pytest.raises(KeyError):
            p.as_dict()["refs"]["discard_test"]["discard"]
        c1.discard()
        assert p.as_dict()["refs"]["discard_test"]["discard"]
        with pytest.raises(KeyError):
            p.as_dict()["refs"]["discard_test"]["store"]
        c1.set_storage("cold_4")
        assert p.as_dict()["refs"]["discard_test"]["store"]["where"] == "cold_4"

    # pragma pylint: enable=expression-not-assigned

    def test_cover_state_propagation(self):
        for name, ct in _CONTAINER_TYPES.items():
            for covers in filter(None, [ct.cover_types, ct.seal_types]):
                for cover in covers:
                    p = Protocol()
                    c = p.ref(name + cover, cont_type=name, cover=cover, discard=True)
                    p.image(c, "top", "image")
                    ref = list(p.as_dict()["refs"].values())[0]
                    assert ref["cover"] == cover


class TestThermocycle(object):
    def test_thermocycle_append(self):
        t = Thermocycle(
            "plate",
            [
                {
                    "cycles": 1,
                    "steps": [
                        {"temperature": "95:celsius", "duration": "60:second"},
                    ],
                },
                {
                    "cycles": 30,
                    "steps": [
                        {"temperature": "95:celsius", "duration": "15:second"},
                        {"temperature": "55:celsius", "duration": "15:second"},
                        {"temperature": "72:celsius", "duration": "10:second"},
                    ],
                },
                {
                    "cycles": 1,
                    "steps": [
                        {"temperature": "72:celsius", "duration": "600:second"},
                        {"temperature": "12:celsius", "duration": "120:second"},
                    ],
                },
            ],
            "20:microliter",
        )
        # Test for correct number of groups
        assert len(t.data["groups"]) == 3
        assert t.data["volume"] == "20:microliter"

    def test_thermocycle_dyes_and_datarefs(self):
        pytest.raises(
            ValueError,
            Thermocycle,
            "plate",
            [
                {
                    "cycles": 1,
                    "steps": [{"temperature": "50: celsius", "duration": "20:minute"}],
                }
            ],
            dyes={"FAM": ["A1"]},
        )
        pytest.raises(
            ValueError,
            Thermocycle,
            "plate",
            [
                {
                    "cycles": 1,
                    "steps": [{"temperature": "50: celsius", "duration": "20:minute"}],
                }
            ],
            dataref="test_dataref",
        )
        pytest.raises(
            ValueError,
            Thermocycle,
            "plate",
            [
                {
                    "cycles": 1,
                    "steps": [{"temperature": "50: celsius", "duration": "20:minute"}],
                }
            ],
            dyes={"ThisDyeIsInvalid": ["A1"]},
        )

    def test_thermocycle_melting(self):
        pytest.raises(
            ValueError,
            Thermocycle,
            "plate",
            [
                {
                    "cycles": 1,
                    "steps": [{"temperature": "50: celsius", "duration": "20:minute"}],
                }
            ],
            melting={"start": "50:celsius"},
        )
        pytest.raises(
            ValueError,
            Thermocycle,
            "plate",
            [
                {
                    "cycles": 1,
                    "steps": [{"temperature": "50: celsius", "duration": "20:minute"}],
                }
            ],
            melting={
                "start": "50:celsius",
                "end": "60:celsius",
                "increment": "1:celsius",
                "rate": "2:minute",
            },
        )

    def test_thermocycle_lid_temperature(self):
        groups = [
            {
                "cycles": 1,
                "steps": [
                    {"temperature": "95:celsius", "duration": "60:second"},
                ],
            }
        ]
        p = Protocol()
        dummy = p.ref("plate", cont_type="96-pcr", discard=True)
        p.thermocycle(dummy, groups, lid_temperature="55:celsius")
        assert p.instructions[-1].lid_temperature == Unit("55:celsius")

    def test_thermocycle_builders(self):
        t = Thermocycle(
            "plate",
            [
                Thermocycle.builders.group(
                    steps=[Thermocycle.builders.step("95:celsius", "5:minute")]
                ),
                Thermocycle.builders.group(
                    steps=[
                        Thermocycle.builders.step("95:celsius", "30:second"),
                        Thermocycle.builders.step("56:celsius", "20:second"),
                        Thermocycle.builders.step(
                            {"top": "72:celsius", "bottom": "70:celsius"}, "20:second"
                        ),
                    ],
                    cycles=30,
                ),
                Thermocycle.builders.group(
                    steps=[Thermocycle.builders.step("4:celsius", "10:minute")]
                ),
            ],
        )
        assert t.data["groups"] == [
            {
                "cycles": 1,
                "steps": [
                    {"duration": Unit("5:minute"), "temperature": Unit("95:celsius")}
                ],
            },
            {
                "cycles": 30,
                "steps": [
                    {"duration": Unit("30:second"), "temperature": Unit("95:celsius")},
                    {"duration": Unit("20:second"), "temperature": Unit("56:celsius")},
                    {
                        "duration": Unit("20:second"),
                        "gradient": {
                            "top": Unit("72:celsius"),
                            "bottom": Unit("70:celsius"),
                        },
                    },
                ],
            },
            {
                "cycles": 1,
                "steps": [
                    {"duration": Unit("10:minute"), "temperature": Unit("4:celsius")}
                ],
            },
        ]


class TestRefify(object):
    # pragma pylint: disable=protected-access
    def test_refifying_various(self, dummy_protocol):
        p = dummy_protocol
        # refify container
        refs = {"plate": p.ref("test", None, "96-flat", "cold_20")}
        assert p._refify(refs["plate"]) == "test"
        # refify dict
        assert p._refify(refs) == {"plate": "test"}

        # refify Well
        well = refs["plate"].well("A1")
        assert p._refify(well) == "test/0"

        # refify WellGroup
        wellgroup = refs["plate"].wells_from("A2", 3)
        assert p._refify(wellgroup) == ["test/1", "test/2", "test/3"]

        # refify Unit
        a_unit = Unit("30:microliter")
        assert p._refify(a_unit) == "30:microliter"

        # refify Instruction
        p.cover(refs["plate"])
        assert p._refify(p.instructions[0]) == p._refify(p.instructions[0]._as_AST())

        # refify Ref
        assert p._refify(p.refs["test"]) == p.refs["test"].opts

        # refify other
        s = "randomstring"
        i = 24
        assert "randomstring" == p._refify(s)
        assert 24 == p._refify(i)

    # pragma pylint: enable=protected-access
    def test_serialization(self, dummy_protocol):
        expected = {
            "instructions": [
                {"op": "cover", "object": "test", "lid": "low_evaporation"},
                {
                    "op": "incubate",
                    "object": "test",
                    "where": "ambient",
                    "duration": "5:minute",
                    "shaking": False,
                    "co2_percent": 0,
                },
            ],
            "refs": {"test": {"new": "96-flat", "discard": True}},
            "time_constraints": [
                {
                    "from": {"instruction_end": 0},
                    "to": {"instruction_start": 1},
                    "ideal": {"optimization_cost": "linear", "value": "5:second"},
                }
            ],
        }
        a = dummy_protocol.ref("test", cont_type="96-flat", discard=True)
        dummy_protocol.incubate(a, "ambient", "5:minute")
        # time_constraints is not serialized if empty
        assert "time_constraints" not in dummy_protocol.as_dict().keys()
        dummy_protocol.add_time_constraint(
            {"mark": 0, "state": "end"}, {"mark": 1, "state": "start"}, ideal="5:second"
        )
        assert dummy_protocol.as_dict() == expected


class TestOuts(object):
    def test_outs(self, dummy_protocol):
        p = dummy_protocol
        plate = p.ref("plate", None, "96-pcr", discard=True)
        p.seal(plate)
        assert "outs" not in p.as_dict()
        plate.well(0).set_name("test_well")
        plate.well(0).set_properties({"test": "foo"})
        assert plate.well(0).name == "test_well"
        assert list(p.as_dict()["outs"].keys()) == ["plate"]
        assert list(list(p.as_dict()["outs"].values())[0].keys()) == ["0"]
        assert list(p.as_dict()["outs"].values())[0]["0"]["name"] == "test_well"
        assert list(p.as_dict()["outs"].values())[0]["0"]["properties"]["test"] == "foo"


class TestInstructionIndex(object):
    def test_instruction_index(self, dummy_protocol):
        p = dummy_protocol
        plate = p.ref("plate", None, "96-flat", discard=True)

        with pytest.raises(ValueError):
            p.get_instruction_index()
        p.cover(plate)
        assert p.get_instruction_index() == 0
        p.uncover(plate)
        assert p.get_instruction_index() == 1


class TestBatchContainers(object):
    def test_batch_containers(self):
        p = Protocol()

        plate_1 = p.ref("p1", None, "96-pcr", storage="cold_4")
        plate_2 = p.ref("p2", None, "96-pcr", storage="cold_4")

        with pytest.raises(TypeError):
            p.batch_containers("not_a_list")
        with pytest.raises(TypeError):
            p.batch_containers([plate_1, "not_a_plate"])

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            p.batch_containers([plate_1])
            p.batch_containers([plate_1, plate_2], False)
            assert len(w) == 2
            for m in w:
                assert "has no effect" in str(m.message)

        p.batch_containers([plate_1, plate_2])
        assert len(p.time_constraints) == 2
        p.batch_containers([plate_1, plate_2], False, True)
        assert len(p.time_constraints) == 4
        p.time_constraints = []
        p.batch_containers([plate_1, plate_2], True, True)
        assert len(p.time_constraints) == 4


class TestTimeConstraints(object):
    def test_time_constraint(self, dummy_protocol):
        p = dummy_protocol

        plate_1 = p.ref("plate_1", id=None, cont_type="96-flat", discard=True)
        plate_2 = p.ref("plate_2", id=None, cont_type="96-flat", discard=True)

        p.cover(plate_1)
        time_point_1 = p.get_instruction_index()
        p.cover(plate_2)
        time_point_2 = p.get_instruction_index()

        p.add_time_constraint(
            {"mark": time_point_1, "state": "start"},
            {"mark": time_point_1, "state": "end"},
            "10:minute",
        )
        p.add_time_constraint(
            {"mark": time_point_1, "state": "start"},
            {"mark": time_point_2, "state": "end"},
            "10:minute",
        )
        p.add_time_constraint(
            {"mark": time_point_2, "state": "start"},
            {"mark": time_point_1, "state": "end"},
            "10:minute",
        )
        p.add_time_constraint(
            {"mark": time_point_1, "state": "start"},
            {"mark": plate_1, "state": "end"},
            "10:minute",
        )
        p.add_time_constraint(
            {"mark": plate_2, "state": "start"},
            {"mark": plate_1, "state": "end"},
            "10:minute",
        )
        p.add_time_constraint(
            {"mark": plate_2, "state": "start"},
            {"mark": plate_2, "state": "end"},
            "10:minute",
        )

        assert len(p.time_constraints) == 6

        p.add_time_constraint(
            {"mark": time_point_1, "state": "end"},
            {"mark": time_point_2, "state": "end"},
            "10:minute",
            True,
        )

        assert len(p.time_constraints) == 8

    def test_time_constraint_checker(self, dummy_protocol):
        p = dummy_protocol

        plate_1 = p.ref("plate_1", id=None, cont_type="96-flat", discard=True)
        plate_2 = p.ref("plate_2", id=None, cont_type="96-flat", discard=True)

        p.cover(plate_1)
        p.cover(plate_2)

        with pytest.raises(ValueError):
            p.add_time_constraint(
                {"mark": -1, "state": "start"},
                {"mark": plate_2, "state": "end"},
                "10:minute",
            )

        with pytest.raises(TypeError):
            p.add_time_constraint(
                {"mark": "foo", "state": "start"},
                {"mark": plate_2, "state": "end"},
                "10:minute",
            )

        with pytest.raises(TypeError):
            p.add_time_constraint(
                {"mark": plate_1, "state": "foo"},
                {"mark": plate_2, "state": "end"},
                "10:minute",
            )

        with pytest.raises(ValueError):
            p.add_time_constraint(
                {"mark": plate_1, "state": "start"},
                {"mark": plate_2, "state": "end"},
                "-10:minute",
            )

        with pytest.raises(RuntimeError):
            p.add_time_constraint(
                {"mark": plate_1, "state": "start"},
                {"mark": plate_1, "state": "start"},
                "10:minute",
            )

        with pytest.raises(RuntimeError):
            p.add_time_constraint(
                {"mark": plate_1, "state": "end"},
                {"mark": plate_1, "state": "start"},
                "10:minute",
            )

        with pytest.raises(KeyError):
            p.add_time_constraint(
                {"mark": plate_1}, {"mark": plate_1, "state": "start"}, "10:minute"
            )

        with pytest.raises(KeyError):
            p.add_time_constraint(
                {"state": "end"}, {"mark": plate_1, "state": "start"}, "10:minute"
            )

    def test_time_more_than(self, dummy_protocol):
        p = dummy_protocol

        plate_1 = p.ref("plate_1", id=None, cont_type="96-flat", discard=True)
        plate_2 = p.ref("plate_2", id=None, cont_type="96-flat", discard=True)

        p.cover(plate_1)
        p.cover(plate_2)

        # Mirror has no effect with only more_than
        p.add_time_constraint(
            {"mark": plate_1, "state": "start"},
            {"mark": plate_2, "state": "start"},
            more_than="1:minute",
            mirror=True,
        )

        assert len(p.time_constraints) == 1

        # this adds 3 more constraints
        p.add_time_constraint(
            {"mark": plate_1, "state": "start"},
            {"mark": plate_2, "state": "start"},
            less_than="10:minute",
            more_than="1:minute",
            mirror=True,
        )

        assert len(p.time_constraints) == 4


class TestAbsorbance(object):
    def test_single_well(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.absorbance(test_plate, test_plate.well(0), "475:nanometer", "test_reading")
        assert isinstance(p.instructions[0].wells, list)

    def test_bad_well(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        with pytest.raises(TypeError):
            p.absorbance(
                test_plate,
                "bad_well_ref",
                wavelength="450:nanometer",
                dataref="bad_wells",
            )

    def test_temperature(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.absorbance(
            test_plate,
            test_plate.well(0),
            "475:nanometer",
            "test_reading",
            temperature="30:celsius",
        )
        assert p.instructions[0].temperature == "30:celsius"

    def test_settle_time(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.absorbance(
            test_plate,
            test_plate.well(0),
            "475:nanometer",
            "test_reading",
            settle_time=Unit(1, "microsecond"),
        )
        assert p.instructions[-1].settle_time == Unit(1, "microsecond")
        with pytest.raises(ValueError):
            p.absorbance(
                test_plate,
                test_plate.well(0),
                "475:nanometer",
                "test_reading",
                settle_time="-1:microsecond",
            )

    def test_incubate(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.absorbance(
            test_plate,
            test_plate.well(0),
            "475:nanometer",
            "test_reading",
            incubate_before=Absorbance.builders.incubate_params(
                "10:second", "3:millimeter", True
            ),
        )

        assert p.instructions[0].incubate_before["shaking"]["orbital"]
        assert p.instructions[0].incubate_before["shaking"]["amplitude"] == Unit(
            "3:millimeter"
        )
        assert p.instructions[0].incubate_before["duration"] == Unit("10:second")

        p.absorbance(
            test_plate,
            test_plate.well(0),
            "475:nanometer",
            "test_reading",
            incubate_before=Absorbance.builders.incubate_params("10:second"),
        )

        assert "shaking" not in p.instructions[1].incubate_before
        assert p.instructions[1].incubate_before["duration"] == Unit("10:second")

        with pytest.raises(ValueError):
            p.absorbance(
                test_plate,
                test_plate.well(0),
                "475:nanometer",
                "test_reading",
                incubate_before=Absorbance.builders.incubate_params(
                    "10:second", "-3:millimeter", True
                ),
            )

        with pytest.raises(TypeError):
            p.absorbance(
                test_plate,
                test_plate.well(0),
                "475:nanometer",
                "test_reading",
                incubate_before=Absorbance.builders.incubate_params(
                    "10:second", "3:millimeter", "foo"
                ),
            )

        with pytest.raises(ValueError):
            p.absorbance(
                test_plate,
                test_plate.well(0),
                "475:nanometer",
                "test_reading",
                incubate_before=Absorbance.builders.incubate_params(
                    "-10:second", "3:millimeter", True
                ),
            )

        with pytest.raises(ValueError):
            p.absorbance(
                test_plate,
                test_plate.well(0),
                "475:nanometer",
                "test_reading",
                incubate_before=Absorbance.builders.incubate_params(
                    "10:second", "3:millimeter"
                ),
            )

        with pytest.raises(ValueError):
            p.absorbance(
                test_plate,
                test_plate.well(0),
                "475:nanometer",
                "test_reading",
                incubate_before=Absorbance.builders.incubate_params(
                    "10:second", shake_orbital=True
                ),
            )

        with pytest.raises(TypeError):
            p.absorbance(
                test_plate,
                test_plate.well(0),
                "475:nanometer",
                "test_reading",
                incubate_before={"shaking": {"amplitude": "3:mm", "orbital": True}},
            )

        with pytest.raises(ValueError):
            p.absorbance(
                test_plate,
                test_plate.well(0),
                "475:nanometer",
                "test_reading",
                incubate_before={"duration": "10:minute", "shaking": {"orbital": True}},
            )

        with pytest.raises(ValueError):
            p.absorbance(
                test_plate,
                test_plate.well(0),
                "475:nanometer",
                "test_reading",
                incubate_before={
                    "duration": "10:minute",
                    "shaking": {"amplitude": "3:mm"},
                },
            )
        with pytest.raises(TypeError):
            p.absorbance(
                test_plate,
                test_plate.well(0),
                "475:nanometer",
                "test_reading",
                incubate_before={
                    "duration": "10:minute",
                    "shake": {"amplitude": "3:mm", "orbital": True},
                },
            )


class TestFluorescence(object):
    def test_single_well(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.fluorescence(
            test_plate,
            test_plate.well(0),
            excitation="587:nanometer",
            emission="610:nanometer",
            dataref="test_reading",
        )
        assert isinstance(p.instructions[0].wells, list)

    def test_temperature(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.fluorescence(
            test_plate,
            test_plate.well(0),
            excitation="587:nanometer",
            emission="610:nanometer",
            dataref="test_reading",
            temperature="30:celsius",
        )
        assert p.instructions[0].temperature == "30:celsius"

    def test_gain(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        for i in range(0, 10):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref=f"test_reading_{i}",
                gain=(i * 0.1),
            )
            assert p.instructions[i].gain == (i * 0.1)

        with pytest.raises(ValueError):
            for i in range(-6, 10, 5):
                p.fluorescence(
                    test_plate,
                    test_plate.well(0),
                    excitation="587:nanometer",
                    emission="610:nanometer",
                    dataref="test_reading",
                    gain=i,
                )

    def test_incubate(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.fluorescence(
            test_plate,
            test_plate.well(0),
            excitation="587:nanometer",
            emission="610:nanometer",
            dataref="test_reading",
            incubate_before=Fluorescence.builders.incubate_params(
                "10:second", "3:millimeter", True
            ),
        )

        assert p.instructions[0].incubate_before["shaking"]["orbital"]
        assert p.instructions[0].incubate_before["shaking"]["amplitude"] == Unit(
            "3:millimeter"
        )
        assert p.instructions[0].incubate_before["duration"] == Unit("10:second")

        p.fluorescence(
            test_plate,
            test_plate.well(0),
            excitation="587:nanometer",
            emission="610:nanometer",
            dataref="test_reading",
            incubate_before=Fluorescence.builders.incubate_params("10:second"),
        )

        assert "shaking" not in p.instructions[1].incubate_before
        assert p.instructions[1].incubate_before["duration"] == Unit("10:second")

        with pytest.raises(ValueError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                incubate_before=Fluorescence.builders.incubate_params(
                    "10:second", "-3:millimeter", True
                ),
            )

        with pytest.raises(TypeError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                incubate_before=Fluorescence.builders.incubate_params(
                    "10:second", "3:millimeter", "foo"
                ),
            )

        with pytest.raises(ValueError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                incubate_before=Fluorescence.builders.incubate_params(
                    "-10:second", "3:millimeter", True
                ),
            )

        with pytest.raises(ValueError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                incubate_before=Fluorescence.builders.incubate_params(
                    "10:second", "3:millimeter"
                ),
            )

        with pytest.raises(ValueError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                incubate_before=Fluorescence.builders.incubate_params(
                    "10:second", shake_orbital=True
                ),
            )

        with pytest.raises(TypeError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                incubate_before={"shaking": {"amplitude": "3:mm", "orbital": True}},
            )

        with pytest.raises(ValueError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                incubate_before={"duration": "10:minute", "shaking": {"orbital": True}},
            )

        with pytest.raises(ValueError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                incubate_before={
                    "duration": "10:minute",
                    "shaking": {"amplitude": "3:mm"},
                },
            )

    def test_detection_mode(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.fluorescence(
            test_plate,
            test_plate.well(0),
            excitation="587:nanometer",
            emission="610:nanometer",
            dataref="test_reading",
            detection_mode="top",
        )
        assert p.instructions[-1].detection_mode == "top"
        p.fluorescence(
            test_plate,
            test_plate.well(0),
            excitation="587:nanometer",
            emission="610:nanometer",
            dataref="test_reading",
            detection_mode="bottom",
        )
        assert p.instructions[-1].detection_mode == "bottom"
        with pytest.raises(ValueError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                detection_mode="not_valid",
            )

    def test_time_parameters(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        neg_time = Unit(-1, "second")
        valid_time = Unit(1, "second")
        with pytest.raises(ValueError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                settle_time=neg_time,
            )
        with pytest.raises(ValueError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                lag_time=neg_time,
            )
        with pytest.raises(ValueError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                integration_time=neg_time,
            )
        p.fluorescence(
            test_plate,
            test_plate.well(0),
            excitation="587:nanometer",
            emission="610:nanometer",
            dataref="test_reading",
            integration_time=valid_time,
            settle_time=valid_time,
            lag_time=valid_time,
        )
        assert all(
            time in p.instructions[-1].data
            for time in ["settle_time", "lag_time", "integration_time"]
        )

    def test_position_z(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        with pytest.raises(KeyError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                position_z={"bad_key": "not_valid"},
            )
        with pytest.raises(ValueError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                position_z={
                    "manual": Unit(0, "meter"),
                    "calculated_from_wells": [test_plate.well(0)],
                },
            )
        with pytest.raises(ValueError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                position_z={"manual": Unit(-1, "meter")},
            )
        # uncomment lines below once 'calculated_from_wells' has
        # been implemented
        # p.fluorescence(test_plate, test_plate.well(0),
        #                excitation="587:nanometer",
        #                emission="610:nanometer",
        #                dataref="test_reading",
        #                detection_mode="top",
        #                position_z={"calculated_from_wells":
        #                               [test_plate.well(0)]})
        # assert (p.instructions[-1].detection_mode == "top")
        # assert "calculated_from_wells" in (p.instructions[-1].position_z.keys())
        # assert test_plate.well(0) in (p.instructions[-1].position_z["calculated_from_wells"])
        with pytest.raises(ValueError):
            p.fluorescence(
                test_plate,
                test_plate.well(0),
                excitation="587:nanometer",
                emission="610:nanometer",
                dataref="test_reading",
                detection_mode="bottom",
                position_z={"manual": Unit(0, "meter")},
            )
        p.fluorescence(
            test_plate,
            test_plate.well(0),
            excitation="587:nanometer",
            emission="610:nanometer",
            dataref="test_reading",
            detection_mode="top",
            position_z={"manual": Unit(1, "micrometer")},
        )
        assert p.instructions[-1].data["position_z"]["manual"] == Unit(1, "micrometer")


class TestLuminescence(object):
    def test_single_well(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.luminescence(test_plate, test_plate.well(0), "test_reading")
        assert isinstance(p.instructions[0].wells, list)

    def test_temperature(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.luminescence(
            test_plate, test_plate.well(0), "test_reading", temperature="30:celsius"
        )
        assert p.instructions[0].temperature == "30:celsius"

    def test_settle_time(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.luminescence(
            test_plate,
            test_plate.well(0),
            "test_reading",
            settle_time=Unit(1, "microsecond"),
        )
        assert p.instructions[-1].settle_time == Unit(1, "microsecond")
        with pytest.raises(ValueError):
            p.luminescence(
                test_plate,
                test_plate.well(0),
                "test_reading",
                settle_time="-1:microsecond",
            )

    def test_integration_time(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.luminescence(
            test_plate,
            test_plate.well(0),
            "test_reading",
            integration_time=Unit(1, "microsecond"),
        )
        assert p.instructions[-1].integration_time == Unit(1, "microsecond")
        with pytest.raises(ValueError):
            p.luminescence(
                test_plate,
                test_plate.well(0),
                "test_reading",
                integration_time="-1:microsecond",
            )

    def test_incubate(self):
        p = Protocol()
        test_plate = p.ref("test", None, "96-flat", discard=True)
        p.luminescence(
            test_plate,
            test_plate.well(0),
            "test_reading",
            incubate_before=Luminescence.builders.incubate_params(
                "10:second", "3:millimeter", True
            ),
        )

        assert p.instructions[0].incubate_before["shaking"]["orbital"]
        assert p.instructions[0].incubate_before["shaking"]["amplitude"] == Unit(
            "3:millimeter"
        )
        assert p.instructions[0].incubate_before["duration"] == Unit("10:second")

        p.luminescence(
            test_plate,
            test_plate.well(0),
            "test_reading",
            incubate_before=Luminescence.builders.incubate_params("10:second"),
        )

        assert not p.instructions[1].incubate_before.get("shaking")
        assert p.instructions[1].incubate_before["duration"] == Unit("10:second")

        with pytest.raises(ValueError):
            p.luminescence(
                test_plate,
                test_plate.well(0),
                "test_reading",
                incubate_before=Luminescence.builders.incubate_params(
                    "10:second", "-3:millimeter", True
                ),
            )

        with pytest.raises(TypeError):
            p.luminescence(
                test_plate,
                test_plate.well(0),
                "test_reading",
                incubate_before=Luminescence.builders.incubate_params(
                    "10:second", "3:millimeter", "foo"
                ),
            )

        with pytest.raises(ValueError):
            p.luminescence(
                test_plate,
                test_plate.well(0),
                "test_reading",
                incubate_before=Luminescence.builders.incubate_params(
                    "-10:second", "3:millimeter", True
                ),
            )

        with pytest.raises(ValueError):
            p.luminescence(
                test_plate,
                test_plate.well(0),
                "test_reading",
                incubate_before=Luminescence.builders.incubate_params(
                    "10:second", "3:millimeter"
                ),
            )

        with pytest.raises(ValueError):
            p.luminescence(
                test_plate,
                test_plate.well(0),
                "test_reading",
                incubate_before=Luminescence.builders.incubate_params(
                    "10:second", shake_orbital=True
                ),
            )

        with pytest.raises(TypeError):
            p.luminescence(
                test_plate,
                test_plate.well(0),
                "test_reading",
                incubate_before={"shaking": {"amplitude": "3:mm", "orbital": True}},
            )

        with pytest.raises(ValueError):
            p.luminescence(
                test_plate,
                test_plate.well(0),
                "test_reading",
                incubate_before={"duration": "10:minute", "shaking": {"orbital": True}},
            )

        with pytest.raises(ValueError):
            p.luminescence(
                test_plate,
                test_plate.well(0),
                "test_reading",
                incubate_before={
                    "duration": "10:minute",
                    "shaking": {"amplitude": "3:mm"},
                },
            )


class TestAcousticTransfer(object):
    def test_append(self, dummy_protocol):
        p = dummy_protocol
        echo = p.ref("echo", None, "384-echo", discard=True)
        dest = p.ref("dest", None, "384-flat", discard=True)
        dest2 = p.ref("dest2", None, "384-flat", discard=True)
        p.acoustic_transfer(echo.well(0), dest.wells(1, 3, 5), "25:microliter")
        assert len(p.instructions) == 1
        p.acoustic_transfer(echo.well(0), dest.wells(0, 2, 4), "25:microliter")
        assert len(p.instructions) == 2
        p.acoustic_transfer(
            echo.well(0),
            dest.wells(0, 2, 4),
            "25:microliter",
            droplet_size="0.50:microliter",
        )
        assert len(p.instructions) == 3
        p.acoustic_transfer(
            echo.well(0),
            dest2.wells(0, 2, 4),
            "25:microliter",
            droplet_size="2.5:nanoliter",
        )
        assert len(p.instructions) == 4

    @pytest.mark.parametrize(
        "source_vol", ["2:microliter", "50:microliter", "17:microliter"]
    )
    @pytest.mark.parametrize("source_wells", [[0, 1, 2, 3], list(range(0, 60))])
    @pytest.mark.parametrize(
        "transfer_vol", ["1:microliter", "1.5:microliter", "2:microliter"]
    )
    def test_one_source(self, dummy_protocol, source_vol, source_wells, transfer_vol):
        p = dummy_protocol
        echo = p.ref("echo", None, "384-echo", discard=True)
        dest = p.ref("dest", None, "384-flat", discard=True)
        one_source = echo.wells(source_wells).set_volume(source_vol)
        dest_wells = dest.wells(list(range(0, 60)))

        if sum([w.available_volume() for w in one_source]) < (
            len(dest_wells) * Unit(transfer_vol)
        ):
            with pytest.raises(RuntimeError):
                p.acoustic_transfer(
                    one_source,
                    dest_wells,
                    transfer_vol,
                    one_source=True,
                )
        else:
            p.acoustic_transfer(
                one_source,
                dest_wells,
                transfer_vol,
                one_source=True,
            )
            for w in one_source:
                assert w.volume >= echo.container_type.dead_volume_ul

    def test_droplet_size(self, dummy_protocol):
        p = dummy_protocol
        echo = p.ref("echo", None, "384-echo", discard=True)
        dest = p.ref("dest", None, "384-flat", discard=True)
        with pytest.raises(RuntimeError):
            p.acoustic_transfer(
                echo.wells(0, 1).set_volume("2:microliter"),
                dest.wells(0, 1),
                "1:microliter",
                droplet_size="26:nanoliter",
            )
        with pytest.raises(RuntimeError):
            p.acoustic_transfer(
                echo.wells(0, 1).set_volume("2:microliter"),
                dest.wells(0, 1),
                "1.31:microliter",
            )


class TestMagneticTransfer(object):
    def test_head_type(self, dummy_protocol):
        p = dummy_protocol
        pcr = p.ref("pcr", None, "96-pcr", discard=True)

        with pytest.raises(KeyError):
            p.mag_dry("96-flat", pcr, "30:minute", new_tip=False, new_instruction=False)
        p.mag_dry("96-pcr", pcr, "30:minute", new_tip=False, new_instruction=False)
        assert len(p.instructions) == 1

    def test_head_compatibility(self, dummy_protocol):
        p = dummy_protocol

        pcrs = [
            p.ref(f"pcr_{cont_type}", None, cont_type, discard=True)
            for cont_type in ["96-pcr", "96-v-kf", "96-flat", "96-flat-uv"]
        ]
        deeps = [
            p.ref(f"deep_{cont_type}", None, cont_type, discard=True)
            for cont_type in ["96-v-kf", "96-deep-kf", "96-deep"]
        ]

        for i, pcr in enumerate(pcrs):
            p.mag_dry("96-pcr", pcr, "30:minute", new_tip=False, new_instruction=False)
            assert len(p.instructions[-1].groups[0]) == i + 1

        for i, deep in enumerate(deeps):
            if i == 0:
                n_i = True
            else:
                n_i = False
            p.mag_dry("96-deep", deep, "30:minute", new_tip=False, new_instruction=n_i)
            assert len(p.instructions[-1].groups[0]) == i + 1

        bad_pcrs = [
            p.ref(f"bad_pcr_{cont_type}", None, cont_type, discard=True)
            for cont_type in ["96-pcr"]
        ]
        bad_deeps = [
            p.ref(f"bad_deep_{cont_type}", None, cont_type, discard=True)
            for cont_type in ["96-deep-kf", "96-deep"]
        ]

        for pcr in bad_pcrs:
            with pytest.raises(ValueError):
                p.mag_dry(
                    "96-deep", pcr, "30:minute", new_tip=False, new_instruction=False
                )

        for deep in bad_deeps:
            with pytest.raises(ValueError):
                p.mag_dry(
                    "96-pcr", deep, "30:minute", new_tip=False, new_instruction=False
                )

    def test_unit_converstion(self, dummy_protocol):
        p = dummy_protocol
        pcr = p.ref("pcr", None, "96-pcr", discard=True)
        p.mag_mix(
            "96-pcr",
            pcr,
            "30:second",
            "5:hertz",
            center=0.75,
            amplitude=0.25,
            magnetize=True,
            temperature=None,
            new_tip=False,
            new_instruction=False,
        )
        out_dict = {
            "amplitude": 0.25,
            "center": 0.75,
            "duration": Unit(30.0, "second"),
            "frequency": Unit(5.0, "hertz"),
            "magnetize": True,
        }
        for k, v in out_dict.items():
            assert p.instructions[-1].groups[0][0]["mix"][k] == v

    def test_temperature_valid(self, dummy_protocol):
        p = dummy_protocol

        pcr = p.ref("pcr", None, "96-pcr", discard=True)

        for i in range(27, 96):
            p.mag_incubate("96-pcr", pcr, "30:minute", temperature=f"{i}:celsius")
            assert len(p.instructions[-1].groups[0]) == i - 26

    def test_frequency_valid(self, dummy_protocol):
        pcr = dummy_protocol.ref("pcr", None, "96-pcr", discard=True)

        frequencies = [f"{_}:hertz" for _ in range(27, 96)]
        for index, frequency in enumerate(frequencies):
            dummy_protocol.mag_mix(
                "96-pcr", pcr, "30:second", frequency, center=1, amplitude=0
            )
            assert len(dummy_protocol.instructions[-1].groups[0]) == index + 1

    def test_magnetize_valid(self, dummy_protocol):
        pcr = dummy_protocol.ref("pcr", None, "96-pcr", discard=True)

        dummy_protocol.mag_mix(
            "96-pcr",
            pcr,
            "30:second",
            "60:hertz",
            center=1,
            amplitude=0,
            magnetize=True,
        )
        assert len(dummy_protocol.instructions[-1].groups[0]) == 1

        dummy_protocol.mag_mix(
            "96-pcr",
            pcr,
            "30:second",
            "60:hertz",
            center=1,
            amplitude=0,
            magnetize=False,
        )
        assert len(dummy_protocol.instructions[-1].groups[0]) == 2

        with pytest.raises(TypeError):
            dummy_protocol.mag_mix(
                "96-pcr",
                pcr,
                "30:second",
                "60:hertz",
                center=1,
                amplitude=0,
                magnetize="Foo",
            )

    def test_center_valid(self, dummy_protocol):
        pcr = dummy_protocol.ref("pcr", None, "96-pcr", discard=True)

        common_params = {"head": "96-pcr", "container": pcr}

        for index, position in enumerate([0, 0.5, 1]):
            dummy_protocol.mag_mix(
                duration="30:second",
                frequency="60:hertz",
                center=position,
                amplitude=0,
                **common_params,
            )
            assert len(dummy_protocol.instructions[-1].groups[0]) == index * 4 + 1
            dummy_protocol.mag_collect(
                cycles=5,
                pause_duration="30:second",
                bottom_position=position,
                **common_params,
            )
            assert len(dummy_protocol.instructions[-1].groups[0]) == index * 4 + 2
            dummy_protocol.mag_incubate(
                duration="30:minute", tip_position=position, **common_params
            )
            assert len(dummy_protocol.instructions[-1].groups[0]) == index * 4 + 3
            dummy_protocol.mag_release(
                duration="30:second",
                frequency="1:hertz",
                center=position,
                amplitude=0,
                **common_params,
            )
            assert len(dummy_protocol.instructions[-1].groups[0]) == index * 4 + 4

        with pytest.raises(ValueError):
            dummy_protocol.mag_mix(
                duration="30:second",
                frequency="60:hertz",
                amplitude=0,
                center=-1,
                **common_params,
            )
        with pytest.raises(ValueError):
            dummy_protocol.mag_collect(
                cycles=5,
                pause_duration="30:second",
                bottom_position=-1,
                **common_params,
            )
        with pytest.raises(ValueError):
            dummy_protocol.mag_incubate(
                duration="30:minute", tip_position=-1, **common_params
            )
        with pytest.raises(ValueError):
            dummy_protocol.mag_release(
                duration="30:second",
                frequency="1:hertz",
                amplitude=0,
                center=-1,
                **common_params,
            )

    def test_amplitude_valid(self, dummy_protocol):
        pcr = dummy_protocol.ref("pcr", None, "96-pcr", discard=True)

        common_params = {"head": "96-pcr", "container": pcr}

        for index, position in enumerate([0, 0.5, 1]):
            dummy_protocol.mag_mix(
                duration="30:second",
                frequency="60:hertz",
                center=position,
                amplitude=0,
                **common_params,
            )
            assert len(dummy_protocol.instructions[-1].groups[0]) == index * 2 + 1
            dummy_protocol.mag_release(
                duration="30:second",
                frequency="1:hertz",
                center=position,
                amplitude=0,
                **common_params,
            )
            assert len(dummy_protocol.instructions[-1].groups[0]) == index * 2 + 2

        with pytest.raises(ValueError):
            dummy_protocol.mag_mix(
                duration="30:second",
                frequency="60:hertz",
                amplitude=2,
                center=1,
                **common_params,
            )
        with pytest.raises(ValueError):
            dummy_protocol.mag_release(
                duration="30:second",
                frequency="1:hertz",
                amplitude=2,
                center=1,
                **common_params,
            )

    def test_mag_append(self, dummy_protocol):
        p = dummy_protocol

        pcrs = [p.ref(f"pcr_{i}", None, "96-pcr", storage="cold_20") for i in range(7)]

        pcr = pcrs[0]

        p.mag_dry("96-pcr", pcr, "30:minute", new_tip=False, new_instruction=False)
        assert len(p.instructions[-1].groups[0]) == 1
        assert len(p.instructions[-1].groups) == 1

        p.mag_dry("96-pcr", pcr, "30:minute", new_tip=True, new_instruction=False)
        assert len(p.instructions[-1].groups) == 2
        assert len(p.instructions) == 1

        p.mag_dry("96-pcr", pcr, "30:minute", new_tip=True, new_instruction=True)
        assert len(p.instructions) == 2

        for plate in pcrs:
            p.mag_dry(
                "96-pcr", plate, "30:minute", new_tip=False, new_instruction=False
            )
            assert len(p.instructions) == 2

        with pytest.raises(RuntimeError):
            pcr_too_many = p.ref("pcr_7", None, "96-pcr", discard=True)
            p.mag_dry(
                "96-pcr",
                pcr_too_many,
                "30:minute",
                new_tip=False,
                new_instruction=False,
            )

        p.mag_dry("96-pcr", pcr, "30:minute", new_tip=True, new_instruction=True)
        assert len(p.instructions) == 3

        p.mag_dry("96-pcr", pcr, "30:minute", new_tip=True, new_instruction=False)
        assert len(p.instructions[-1].groups) == 2

        with pytest.raises(RuntimeError):
            for plate in pcrs:
                p.mag_dry(
                    "96-pcr", plate, "30:minute", new_tip=False, new_instruction=False
                )

    def test_remove_cover(self, dummy_protocol):
        p = dummy_protocol
        c = p.ref("96-deep-kf", None, "96-deep-kf", discard=True)
        p.cover(c)
        p.mag_mix(
            "96-deep",
            c,
            "30:second",
            "60:hertz",
            center=0.75,
            amplitude=0.25,
            magnetize=True,
            temperature=None,
            new_tip=False,
            new_instruction=False,
        )
        assert p.instructions[-2].op == "uncover"


class TestAutopick(object):
    def test_autopick(self):
        p = Protocol()
        dest_plate = p.ref("dest", None, "96-flat", discard=True)

        p.refs["agar_plate"] = Ref(
            "agar_plate",
            {"reserve": "ki17reefwqq3sq", "discard": True},
            Container(None, p.container_type("6-flat"), name="agar_plate"),
        )

        agar_plate = Container(None, p.container_type("6-flat"), name="agar_plate")

        p.autopick(
            [agar_plate.well(0), agar_plate.well(1)],
            [dest_plate.well(1)] * 4,
            min_abort=0,
            dataref="1",
        )

        assert len(p.instructions) == 1
        assert len(p.instructions[0].groups) == 1
        assert len(p.instructions[0].groups[0]["from"]) == 2


class TestMeasureConcentration(object):
    def test_measure_concentration_single_well(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref(
            "test_plate", id=None, cont_type="96-flat", storage=None, discard=True
        )
        for well in test_plate.all_wells():
            well.set_volume("150:microliter")
        p.measure_concentration(
            wells=test_plate.well(0),
            dataref="mc_test",
            measurement="DNA",
            volume=Unit(2, "microliter"),
        )
        assert len(p.instructions) == 1

    def test_measure_concentration_multi_well(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref(
            "test_plate", id=None, cont_type="96-flat", storage=None, discard=True
        )
        for well in test_plate.all_wells():
            well.set_volume("150:microliter")
        p.measure_concentration(
            wells=test_plate.wells_from(0, 96),
            dataref="mc_test",
            measurement="DNA",
            volume=Unit(2, "microliter"),
        )
        assert len(p.instructions) == 1

    def test_measure_concentration_multi_sample_class(self, dummy_protocol):
        sample_classes = ["ssDNA", "DNA", "RNA", "protein"]
        p = dummy_protocol
        test_plate = p.ref(
            "test_plate", id=None, cont_type="96-flat", storage=None, discard=True
        )
        for well in test_plate.all_wells():
            well.set_volume("150:microliter")
        for i, sample_class in enumerate(sample_classes):
            p.measure_concentration(
                wells=test_plate.well(i),
                dataref=f"mc_test_{sample_class}",
                measurement=sample_class,
                volume=Unit(2, "microliter"),
            )
            assert p.as_dict()["instructions"][i]["measurement"] == sample_class
        assert len(p.instructions) == 4


class TestMeasureMass(object):
    def test_measure_mass_single_container(self):
        p = Protocol()
        test_plate = p.ref(
            "test_plate", id=None, cont_type="96-flat", storage=None, discard=True
        )
        p.measure_mass(test_plate, "test_ref")
        assert len(p.instructions) == 1

    def test_measure_mass_list_containers(self):
        p = Protocol()
        test_plates = [
            p.ref(
                f"test_plate_{i}",
                id=None,
                cont_type="96-flat",
                storage=None,
                discard=True,
            )
            for i in range(5)
        ]
        with pytest.raises(TypeError):
            p.measure_mass(test_plates, "test_ref")

    def test_measure_mass_bad_list(self):
        p = Protocol()
        test_plates = [
            p.ref(
                f"test_plate_{i}",
                id=None,
                cont_type="96-flat",
                storage=None,
                discard=True,
            )
            for i in range(5)
        ]
        test_plates.append("foo")
        with pytest.raises(TypeError):
            p.measure_mass(test_plates, "test_ref")

    def test_measure_mass_bad_input(self):
        p = Protocol()
        with pytest.raises(TypeError):
            p.measure_mass("foo", "test_ref")


class TestMeasureVolume(object):
    def test_measure_volume_single_well(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref(
            "test_plate", id=None, cont_type="96-flat", storage=None, discard=True
        )
        p.measure_volume(test_plate.well(0), "test_ref")
        assert len(p.instructions) == 1

    def test_measure_volume_list_well(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref(
            "test_plate", id=None, cont_type="96-flat", storage=None, discard=True
        )
        p.measure_volume(test_plate.wells_from(0, 12), "test_ref")
        assert len(p.instructions) == 1


class TestSpin(object):

    # pragma pylint: disable=pointless-statement
    def test_spin_default(self, dummy_protocol):
        p = dummy_protocol
        test_plate = p.ref(
            "test_plate", id=None, cont_type="96-flat", storage=None, discard=True
        )
        p.spin(test_plate, "1000:g", "20:minute")
        p.spin(test_plate, "1000:g", "20:minute", flow_direction="outward")
        p.spin(test_plate, "1000:g", "20:minute", spin_direction=["ccw", "cw", "ccw"])
        p.spin(test_plate, "1000:g", "20:minute", flow_direction="inward")
        assert len(p.instructions) == 7

        with pytest.raises(AttributeError):
            p.instructions[1].flow_direction
        with pytest.raises(AttributeError):
            p.instructions[1].spin_direction
        assert p.instructions[3].flow_direction == "outward"
        assert p.instructions[3].spin_direction == ["cw", "ccw"]
        with pytest.raises(AttributeError):
            p.instructions[5].flow_direction
        assert p.instructions[5].spin_direction == ["ccw", "cw", "ccw"]
        assert p.instructions[6].flow_direction == "inward"
        assert p.instructions[6].spin_direction == ["cw"]
        # pragma pylint: enable=pointless-statement

    def test_spin_bad_values(self):
        p = Protocol()
        test_plate2 = p.ref(
            "test_plate2", id=None, cont_type="96-flat", storage=None, discard=True
        )
        with pytest.raises(ValueError):
            p.spin(test_plate2, "1000:g", "20:minute", flow_direction="bad_value")
        with pytest.raises(ValueError):
            p.spin(
                test_plate2, "1000:g", "20:minute", spin_direction=["cw", "bad_value"]
            )
        with pytest.raises(TypeError):
            p.spin(test_plate2, "1000:g", "20:minute", spin_direction={})
        with pytest.raises(ValueError):
            p.spin(test_plate2, "1000:g", "20:minute", spin_direction=[])


class TestGelPurify(object):
    def test_gel_purify_lane_set(self, dummy_protocol):
        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr", discard=True).wells_from(
            0, 9
        )
        extract_wells = [
            p.ref(f"extract_{i}", None, "micro-1.5", storage="cold_4").well(0)
            for i in sample_wells
        ]
        extract_too_many_samples = [
            {
                "source": sample_wells[i],
                "band_list": [
                    {
                        "band_size_range": {"min_bp": 0, "max_bp": 10},
                        "elution_volume": Unit("5:microliter"),
                        "elution_buffer": "water",
                        "destination": d,
                    }
                ],
                "lane": i,
                "gel": None,
            }
            for i, d in enumerate(extract_wells)
        ]
        with pytest.raises(RuntimeError):
            p.gel_purify(
                extract_too_many_samples,
                "10:microliter",
                "size_select(8,0.8%)",
                "ladder1",
                "gel_purify_test",
            )
        extract = extract_too_many_samples[:8]
        p.gel_purify(
            extract,
            "10:microliter",
            "size_select(8,0.8%)",
            "ladder1",
            "gel_purify_test",
        )
        assert len(p.instructions) == 1
        with pytest.raises(TypeError):
            p.gel_purify(
                {"broken": "extract"},
                "10:microliter",
                "size_select(8,0.8%)",
                "ladder1",
                "gel_purify_test",
            )
        extract[2]["band_list"][0]["band_size_range"]["min_bp"] = 20
        with pytest.raises(ValueError):
            p.gel_purify(
                extract,
                "10:microliter",
                "size_select(8,0.8%)",
                "ladder1",
                "gel_purify_test",
            )
        del extract[2]["band_list"][0]["band_size_range"]
        with pytest.raises(TypeError):
            p.gel_purify(
                extract,
                "10:microliter",
                "size_select(8,0.8%)",
                "ladder1",
                "gel_purify_test",
            )

    def test_gel_purify_no_lane(self):
        p = Protocol()
        sample_wells = p.ref("test_plate", None, "96-pcr", discard=True).wells_from(
            0, 20
        )
        extract_wells = [
            p.ref(f"extract_{i}", None, "micro-1.5", storage="cold_4").well(0)
            for i in sample_wells
        ]
        extract = [
            {
                "source": sample_wells[i],
                "band_list": [
                    {
                        "band_size_range": {"min_bp": 0, "max_bp": 10},
                        "elution_volume": Unit("5:microliter"),
                        "elution_buffer": "water",
                        "destination": d,
                    }
                ],
                "lane": None,
                "gel": None,
            }
            for i, d in enumerate(extract_wells)
        ]
        p.gel_purify(
            extract,
            "10:microliter",
            "size_select(8,0.8%)",
            "ladder1",
            "gel_purify_test",
        )
        assert len(p.instructions) == 3
        assert p.instructions[0].extract[1]["lane"] == 1
        assert p.instructions[2].extract[-1]["lane"] == 3

    def test_gel_purify_one_lane(self, dummy_protocol):
        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr", discard=True).wells_from(
            0, 8
        )
        extract_wells = [
            p.ref(f"extract_{i}", None, "micro-1.5", storage="cold_4").well(0)
            for i in sample_wells
        ]
        extract = [
            {
                "source": sample_wells[i],
                "band_list": [
                    {
                        "band_size_range": {"min_bp": 0, "max_bp": 10},
                        "elution_volume": Unit("5:microliter"),
                        "elution_buffer": "water",
                        "destination": d,
                    }
                ],
                "lane": None,
                "gel": None,
            }
            for i, d in enumerate(extract_wells)
        ]
        extract[7]["lane"] = 5
        with pytest.raises(RuntimeError):
            p.gel_purify(
                extract,
                "10:microliter",
                "size_select(8,0.8%)",
                "ladder1",
                "gel_purify_test",
            )
        extract[7]["lane"] = None
        p.gel_purify(
            extract,
            "10:microliter",
            "size_select(8,0.8%)",
            "ladder1",
            "gel_purify_test",
        )
        assert len(p.instructions) == 1
        assert p.instructions[-1].extract[0]["lane"] == 0
        assert p.instructions[0].extract[7]["lane"] == 7

    def test_make_gel_extract_params(self, dummy_protocol):
        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr", discard=True).wells_from(
            0, 8
        )
        extract_wells = [
            p.ref("extract_" + str(i), None, "micro-1.5", storage="cold_4").well(0)
            for i in sample_wells
        ]
        extracts = [
            GelPurify.builders.extract(
                w,
                GelPurify.builders.band("TE", "5:microliter", extract_wells[i], 79, 80),
            )
            for i, w in enumerate(sample_wells)
        ]
        with pytest.raises(RuntimeError):
            p.gel_purify(
                extracts, "10:microliter", "bad_gel", "ladder1", "gel_purify_test"
            )
        p.gel_purify(
            extracts,
            "10:microliter",
            "size_select(8,0.8%)",
            "ladder1",
            "gel_purify_test",
        )
        assert len(p.instructions) == 1
        assert p.instructions[0].extract[-1]["lane"] == 7
        assert p.instructions[-1].extract[0]["lane"] == 0
        assert p.instructions[-1].extract[1]["lane"] == 1

    def test_gel_purify_extract_param_checker(self, dummy_protocol):
        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr", discard=True).wells_from(
            0, 8
        )
        extract_wells = [
            p.ref("extract_" + str(i), None, "micro-1.5", storage="cold_4").well(0)
            for i in sample_wells
        ]
        extracts = [
            GelPurify.builders.extract(
                w,
                GelPurify.builders.band("TE", "5:microliter", extract_wells[i], 79, 80),
            )
            for i, w in enumerate(sample_wells)
        ]
        extracts[7]["band_list"][0]["elution_volume"] = "not_a_unit"
        with pytest.raises(TypeError):
            p.gel_purify(
                extracts,
                "5:microliter",
                "size_select(8,0.8%)",
                "ladder1",
                "gel_purify_test",
            )
        extracts[3]["band_list"][0]["destination"] = "not_a_well"
        with pytest.raises(TypeError):
            p.gel_purify(
                extracts[:4],
                "5:microliter",
                "size_select(8,0.8%)",
                "ladder1",
                "gel_purify_test",
            )


class TestIlluminaSeq(object):
    def test_illumina_seq(self, dummy_protocol):
        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr", discard=True).wells_from(
            0, 8
        )
        p.illuminaseq(
            "PE",
            [
                {"object": sample_wells[0], "library_concentration": 1.0},
                {"object": sample_wells[1], "library_concentration": 2},
            ],
            "nextseq",
            "mid",
            "none",
            34,
            "dataref",
        )

        assert len(p.instructions) == 1

        p.illuminaseq(
            "PE",
            [
                {"object": sample_wells[0], "library_concentration": 1.0},
                {"object": sample_wells[1], "library_concentration": 5.32},
                {"object": sample_wells[2], "library_concentration": 54},
                {"object": sample_wells[3], "library_concentration": 20},
                {"object": sample_wells[4], "library_concentration": 23},
                {"object": sample_wells[5], "library_concentration": 23},
                {"object": sample_wells[6], "library_concentration": 21},
                {"object": sample_wells[7], "library_concentration": 62},
            ],
            "hiseq",
            "rapid",
            "none",
            250,
            "dataref",
            {"read_2": 300, "read_1": 100, "index_1": 4, "index_2": 12},
        )
        assert len(p.instructions) == 2
        assert len(p.instructions[1].lanes) == 8

    def test_illumina_seq_default(self, dummy_protocol):
        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr", discard=True).wells_from(
            0, 8
        )
        p.illuminaseq(
            "PE",
            [
                {"object": sample_wells[0], "library_concentration": 1.0},
                {"object": sample_wells[1], "library_concentration": 2},
            ],
            "nextseq",
            "mid",
            "none",
            34,
            "dataref",
            {"read_1": 100},
        )

        assert len(p.instructions) == 1
        assert "index_1" in p.instructions[0].cycles
        assert 0 == p.instructions[0].cycles["index_2"]

    def test_illumina_bad_params(self, dummy_protocol):
        p = dummy_protocol
        sample_wells = p.ref("test_plate", None, "96-pcr", discard=True).wells_from(
            0, 3
        )
        with pytest.raises(TypeError):
            p.illuminaseq(
                "PE", "not_a_list", "nextseq", "mid", "none", 250, "bad_lane_param"
            )
        with pytest.raises(ValueError):
            p.illuminaseq(
                "PE",
                [
                    {"object": sample_wells[0], "library_concentration": 1.0},
                    {"object": sample_wells[1], "library_concentration": 2},
                ],
                "nextseq",
                "rapid",
                "none",
                34,
                "dataref",
            )
        with pytest.raises(ValueError):
            p.illuminaseq(
                "PE",
                [
                    {"object": sample_wells[0], "library_concentration": 1.0},
                    {"object": sample_wells[1], "library_concentration": 2},
                ],
                "miseq",
                "high",
                "none",
                250,
                "not_enough_lanes",
            )
        with pytest.raises(ValueError):
            p.illuminaseq(
                "SR",
                [
                    {"object": sample_wells[0], "library_concentration": 1.0},
                    {"object": sample_wells[1], "library_concentration": 2},
                ],
                "nextseq",
                "high",
                "none",
                250,
                "wrong_seq",
                {"read_2": 500, "read_1": 2},
            )
        with pytest.raises(ValueError):
            p.illuminaseq(
                "PE",
                [
                    {"object": sample_wells[0], "library_concentration": 1.0},
                    {"object": sample_wells[1], "library_concentration": 2},
                ],
                "nextseq",
                "high",
                "none",
                250,
                "index_too_high",
                {"read_2": 300, "read_1": 100, "index_1": 4, "index_2": 13},
            )


class TestCoverStatus(object):
    def test_implicit_unseal(self, dummy_protocol):
        p = dummy_protocol
        cont = p.ref("cont", None, "96-pcr", discard=True)
        assert not cont.cover
        p.seal(cont)
        assert cont.cover
        p.mix(cont.well(0), "5:microliter")
        assert not cont.cover

    def test_implicit_uncover(self, dummy_protocol):
        p = dummy_protocol
        cont = p.ref("cont", None, "96-flat", discard=True)
        assert not cont.cover
        p.cover(cont)
        assert cont.cover
        p.mix(cont.well(0), "5:microliter")
        assert not cont.cover

    def test_ref_cover_status(self, dummy_protocol):
        p = dummy_protocol
        cont = p.ref("cont", None, "96-pcr", discard=True, cover="ultra-clear")
        assert cont.cover
        assert cont.cover == "ultra-clear"

    def test_ref_invalid_seal(self, dummy_protocol):
        p = dummy_protocol
        with pytest.raises(AttributeError):
            cont = p.ref("cont", None, "96-pcr", discard=True, cover="clear")
            assert not cont.cover
            assert cont.cover != "clear"
            assert not p.refs[cont.name].opts["cover"]


class TestDispense(object):
    def test_resource_id(self):
        p = Protocol()
        container = p.ref("Test_Container", cont_type="96-pcr", discard=True)
        p.dispense(
            container,
            "rs17gmh5wafm5p",
            [{"column": 0, "volume": "10:ul"}],
            is_resource_id=True,
        )
        assert Unit(10, "microliter") == container.well("B1").volume
        assert container.well(3).volume is None
        assert hasattr(p.instructions[0], "resource_id")
        with pytest.raises(AttributeError):
            p.instructions[0].reagent  # pylint: disable=pointless-statement

    def test_reagent(self):
        p = Protocol()
        container = p.ref("Test_Container", cont_type="96-pcr", discard=True)
        p.dispense_full_plate(
            container, "rs17gmh5wafm5p", "10:ul", is_resource_id=False
        )
        assert Unit(10, "microliter") == container.well("E1").volume
        assert container.well(3).volume is not None
        assert hasattr(p.instructions[0], "reagent")
        with pytest.raises(AttributeError):
            p.instructions[0].resource_id  # pylint: disable=pointless-statement

    def test_flowrate(self):
        p = Protocol()
        container = p.ref("Test_Container", cont_type="96-pcr", discard=True)
        p.dispense_full_plate(container, "water", "10:ul", flowrate="5:ul/s")

        with pytest.raises(TypeError):
            p.dispense_full_plate(container, "water", "10:ul", flowrate="5:s")

    def test_shape(self):
        p = Protocol()
        container = p.ref("Test_Container", cont_type="96-pcr", discard=True)
        p.dispense_full_plate(
            container,
            "water",
            "10:ul",
            shape={"rows": 8, "columns": 1, "format": "SBS96"},
        )

        with pytest.raises(TypeError):
            p.dispense_full_plate(container, "water", "10:ul", shape="SBS96")

    def test_shake_after(self):
        p = Protocol()
        container = p.ref("Test_Container", cont_type="96-pcr", discard=True)
        p.dispense_full_plate(
            container,
            "water",
            "10:ul",
            shake_after=Dispense.builders.shake_after("5:second"),
        )

        assert p.instructions[-1].data["shake_after"] == {"duration": Unit(5, "second")}

    def test_pre_dispense(self):
        p = Protocol()
        container = p.ref("Test_Container", cont_type="96-pcr", discard=True)
        p.dispense_full_plate(container, "water", "10:ul", pre_dispense="10:uL")
        p.dispense_full_plate(container, "water", "10:ul", pre_dispense="0:uL")

        with pytest.raises(ValueError):
            p.dispense_full_plate(container, "water", "10:ul", pre_dispense="5:uL")

        with pytest.raises(ValueError):
            p.dispense_full_plate(container, "water", "10:ul", pre_dispense="11:uL")

    def test_step_size(self):
        # Initialize protocol and container
        p = Protocol()
        container = p.ref("Test_Container", cont_type="96-pcr", discard=True)

        # Test p.dispense while setting step_size to None
        p.dispense(
            container,
            "rs17gmh5wafm5p",
            [{"column": 0, "volume": "10:microliter"}],
            is_resource_id=True,
            step_size=None,
        )
        assert "step_size" not in p.instructions[-1].data

        # Test p.dispense while using step_size default
        p.dispense(
            container,
            "rs17gmh5wafm5p",
            [{"column": 0, "volume": "10:microliter"}],
            is_resource_id=True,
        )
        assert p.instructions[-1].data["step_size"] == Unit(5, "microliter")

        # Test p.dispense with step_size of 5 microliter
        p.dispense(
            container,
            "rs17gmh5wafm5p",
            [{"column": 1, "volume": "10:microliter"}],
            is_resource_id=True,
            step_size="5:microliter",
        )
        assert p.instructions[-1].data["step_size"] == Unit(5, "microliter")

        # Test p.dispense with step_size of 0.5 microliter
        p.dispense(
            container,
            "rs17gmh5wafm5p",
            [{"column": 2, "volume": "0.5:microliter"}],
            is_resource_id=True,
            step_size="0.5:microliter",
        )
        assert p.instructions[-1].data["step_size"] == Unit(0.5, "microliter")

        # Test p.dispense with step_size of 0.5 microliter, submitted as a Unit object
        p.dispense(
            container,
            "rs17gmh5wafm5p",
            [{"column": 2, "volume": "0.5:microliter"}],
            is_resource_id=True,
            step_size=Unit(0.5, "microliter"),
        )
        assert p.instructions[-1].data["step_size"] == Unit(0.5, "microliter")

        # Test p.dispense with step_size in nanoliters
        p.dispense(
            container,
            "rs17gmh5wafm5p",
            [{"column": 2, "volume": "0.5:microliter"}],
            is_resource_id=True,
            step_size="500:nanoliter",
        )
        assert p.instructions[-1].data["step_size"] == Unit(0.5, "microliter")

        # Test bad type for step_size
        with pytest.raises(TypeError):
            p.dispense(
                container,
                "rs17gmh5wafm5p",
                [{"column": 1, "volume": "10:microliter"}],
                is_resource_id=True,
                step_size="5:micrometer",
            )
        with pytest.raises(TypeError):
            p.dispense(
                container,
                "rs17gmh5wafm5p",
                [{"column": 1, "volume": "10:microliter"}],
                is_resource_id=True,
                step_size="5microliter",
            )
        with pytest.raises(TypeError):
            p.dispense(
                container,
                "rs17gmh5wafm5p",
                [{"column": 1, "volume": "10:microliter"}],
                is_resource_id=True,
                step_size=5,
            )

        # Test disallowed step_size
        with pytest.raises(ValueError):
            p.dispense(
                container,
                "rs17gmh5wafm5p",
                [{"column": 1, "volume": "10:microliter"}],
                is_resource_id=True,
                step_size="1:microliter",
            )

        # Test volume that is not an integer multiple of step_size
        with pytest.raises(ValueError):
            p.dispense(
                container,
                "rs17gmh5wafm5p",
                [{"column": 1, "volume": "11:microliter"}],
                is_resource_id=True,
                step_size="5:microliter",
            )
        with pytest.raises(ValueError):
            p.dispense(
                container,
                "rs17gmh5wafm5p",
                [{"column": 2, "volume": "1.6:microliter"}],
                is_resource_id=True,
                step_size="0.5:microliter",
            )

        # Test p.dispense_full_plate while setting step_size to None
        p.dispense_full_plate(
            container,
            "rs17gmh5wafm5p",
            "10:microliter",
            is_resource_id=True,
            step_size=None,
        )
        assert "step_size" not in p.instructions[-1].data

        # Test p.dispense_full_plate while using step_size default
        p.dispense_full_plate(
            container, "rs17gmh5wafm5p", "10:microliter", is_resource_id=True
        )
        assert p.instructions[-1].data["step_size"] == Unit(5, "microliter")

        # Test p.dispense_full_plate with step_size of 5 microliter
        p.dispense_full_plate(
            container,
            "rs17gmh5wafm5p",
            "10:microliter",
            is_resource_id=True,
            step_size="5:microliter",
        )
        assert p.instructions[-1].data["step_size"] == Unit(5, "microliter")

        # Test p.dispense_full_plate with step_size of 0.5 microliter
        p.dispense_full_plate(
            container,
            "rs17gmh5wafm5p",
            "0.5:microliter",
            is_resource_id=True,
            step_size="0.5:microliter",
        )
        assert p.instructions[-1].data["step_size"] == Unit(0.5, "microliter")

        # Test p.dispense_full_plate with step_size of 0.5 microliter,
        # submitted as a Unit object
        p.dispense_full_plate(
            container,
            "rs17gmh5wafm5p",
            "0.5:microliter",
            is_resource_id=True,
            step_size=Unit(0.5, "microliter"),
        )
        assert p.instructions[-1].data["step_size"] == Unit(0.5, "microliter")

        # Test p.dispense_full_plate with step_size in nanoliters
        p.dispense_full_plate(
            container,
            "rs17gmh5wafm5p",
            "0.5:microliter",
            is_resource_id=True,
            step_size="500:nanoliter",
        )
        assert p.instructions[-1].data["step_size"] == Unit(0.5, "microliter")

        # Test bad type for step_size
        with pytest.raises(TypeError):
            p.dispense_full_plate(
                container,
                "rs17gmh5wafm5p",
                "10:microliter",
                is_resource_id=True,
                step_size="5:micrometer",
            )
        with pytest.raises(TypeError):
            p.dispense_full_plate(
                container,
                "rs17gmh5wafm5p",
                "10:microliter",
                is_resource_id=True,
                step_size="5microliter",
            )
        with pytest.raises(TypeError):
            p.dispense_full_plate(
                container,
                "rs17gmh5wafm5p",
                "10:microliter",
                is_resource_id=True,
                step_size=5,
            )

        # Test disallowed step_size
        with pytest.raises(ValueError):
            p.dispense_full_plate(
                container,
                "rs17gmh5wafm5p",
                "10:microliter",
                is_resource_id=True,
                step_size="1:microliter",
            )

        # Test volume that is not an integer multiple of step_size
        with pytest.raises(ValueError):
            p.dispense_full_plate(
                container,
                "rs17gmh5wafm5p",
                "11:microliter",
                is_resource_id=True,
                step_size="5:microliter",
            )
        with pytest.raises(ValueError):
            p.dispense_full_plate(
                container,
                "rs17gmh5wafm5p",
                "1.6:microliter",
                is_resource_id=True,
                step_size="0.5:microliter",
            )

    def test_reagent_source(self):
        # Initialize protocol and containers for testing dispense
        p = Protocol()
        dest1 = p.ref("destination_plate_1", cont_type="96-pcr", discard=True)
        src1 = p.ref(
            "source_well_1", None, cont_type="1-flat", discard=True, cover="universal"
        ).well(0)
        src1.volume = Unit(40, "milliliter")

        dest2 = p.ref("destination_plate_2", cont_type="96-pcr", discard=True)
        src2 = p.ref(
            "source_well_2", None, cont_type="96-deep", discard=True, cover="universal"
        ).well(0)

        dest3 = p.ref("destination_plate_3", cont_type="96-pcr", discard=True)

        dummy_plate = p.ref("dummy_plate", cont_type="96-pcr", discard=True)

        # Test p.dispense with reagent
        p.dispense(dest3, "water", [{"column": 0, "volume": "10:microliter"}])
        assert p.instructions[-1].data["reagent"] == "water"
        assert "resource_id" not in p.instructions[-1].data
        assert "reagent_source" not in p.instructions[-1].data

        # Test p.dispense with resource_id
        p.dispense(
            dest3,
            "rs17gmh5wafm5p",
            [{"column": 0, "volume": "10:microliter"}],
            is_resource_id=True,
        )
        assert "reagent" not in p.instructions[-1].data
        assert p.instructions[-1].data["resource_id"] == "rs17gmh5wafm5p"
        assert "reagent_source" not in p.instructions[-1].data

        # Test p.dispense with reagent_source
        assert src1.container.cover == "universal"

        p.dispense(
            dest1,
            src1,
            [
                {"column": 0, "volume": "10:microliter"},
                {"column": 1, "volume": "30:microliter"},
            ],
        )
        assert src1.container.cover is None
        assert "reagent" not in p.instructions[-1].data
        assert "resource_id" not in p.instructions[-1].data
        assert p.instructions[-1].data["reagent_source"] == src1

        # Check volumes
        for well in dest1.wells_from(0, 8, columnwise=True):
            assert well.volume == Unit(10, "microliter")
        for well in dest1.wells_from(1, 8, columnwise=True):
            assert well.volume == Unit(30, "microliter")
        assert src1.volume == Unit(39680, "microliter")

        # Test improper inputs for reagent
        with pytest.raises(TypeError):
            p.dispense(
                dest1,
                1,
                [
                    {"column": 0, "volume": "10:microliter"},
                    {"column": 1, "volume": "30:microliter"},
                ],
            )
        with pytest.raises(TypeError):
            p.dispense(
                dest1,
                dummy_plate.all_wells(),
                [
                    {"column": 0, "volume": "10:microliter"},
                    {"column": 1, "volume": "30:microliter"},
                ],
            )

        # Test p.dispense_full_plate with reagent
        p.dispense_full_plate(dest3, "water", "10:microliter")
        assert p.instructions[-1].data["reagent"] == "water"
        assert "resource_id" not in p.instructions[-1].data
        assert "reagent_source" not in p.instructions[-1].data

        # Test p.dispense_full_plate with resource_id
        p.dispense_full_plate(
            dest3, "rs17gmh5wafm5p", "10:microliter", is_resource_id=True
        )
        assert "reagent" not in p.instructions[-1].data
        assert p.instructions[-1].data["resource_id"] == "rs17gmh5wafm5p"
        assert "reagent_source" not in p.instructions[-1].data

        # Test p.dispense_full_plate with reagent_source
        assert src2.container.cover == "universal"

        p.dispense_full_plate(dest2, src2, "10:microliter")
        assert src2.container.cover is None
        assert "reagent" not in p.instructions[-1].data
        assert "resource_id" not in p.instructions[-1].data
        assert p.instructions[-1].data["reagent_source"] == src2

        # Check volumes
        for well in dest2.all_wells():
            assert well.volume == Unit(10, "microliter")
        assert src2.volume == Unit(-960, "microliter")

        # Test improper inputs for reagent
        with pytest.raises(TypeError):
            p.dispense_full_plate(dest2, 2, "10:microliter")
        with pytest.raises(TypeError):
            p.dispense_full_plate(dest2, dummy_plate.all_wells(), "10:microliter")


class TestFlowAnalyze(object):
    def test_default(self, dummy_protocol):
        p = dummy_protocol
        container = p.ref("Test_Container1", cont_type="96-pcr", discard=True)
        container2 = p.ref("Test_Container2", cont_type="96-flat", discard=True)
        p.cover(container2, lid="standard")
        assert container2.cover
        p.flow_analyze(
            dataref="Test",
            FSC={"voltage_range": {"low": "230:volt", "high": "280:volt"}},
            SSC={"voltage_range": {"low": "230:volt", "high": "380:volt"}},
            neg_controls=[
                {
                    "well": container.well(0),
                    "volume": "200:microliter",
                    "channel": ["FSC", "SSC"],
                }
            ],
            samples=[
                {"well": container2.well(0), "volume": "200:microliter"},
                {"well": container2.well(1), "volume": "200:microliter"},
                {"well": container2.well(2), "volume": "200:microliter"},
            ],
        )
        assert not container2.cover
        assert p.instructions[1].op == "uncover"
        assert hasattr(p.instructions[2], "channels")

    def test_flow_bad_params(self):
        p = Protocol()
        container = p.ref("Test_Container1", cont_type="96-pcr", discard=True)
        container2 = p.ref("Test_Container2", cont_type="96-flat", discard=True)
        colors = [
            {
                "excitation_wavelength": "4:not_a_unit",
                "emission_wavelength": "4:nanometer",
                "name": "some_name",
            }
        ]
        with pytest.raises(TypeError):
            p.flow_analyze(
                dataref="Test",
                FSC=[{"voltage_range": {"low": "230:volt", "high": "380:volt"}}],
                SSC={"voltage_range": {"low": "230:volt", "high": "380:volt"}},
                neg_controls=[
                    {
                        "well": container.well(0),
                        "volume": "200:microliter",
                        "channel": ["FSC", "SSC"],
                    }
                ],
                samples=[
                    {"well": container2.well(0), "volume": "200:microliter"},
                    {"well": container2.well(1), "volume": "200:microliter"},
                    {"well": container2.well(2), "volume": "200:microliter"},
                ],
            )
        with pytest.raises(AssertionError):
            p.flow_analyze(
                dataref="Test",
                FSC={},
                SSC={"voltage_range": {"low": "230:volt", "high": "380:volt"}},
                neg_controls=[
                    {
                        "well": container.well(0),
                        "volume": "200:microliter",
                        "channel": ["FSC", "SSC"],
                    }
                ],
                samples=[
                    {"well": container2.well(0), "volume": "200:microliter"},
                    {"well": container2.well(1), "volume": "200:microliter"},
                    {"well": container2.well(2), "volume": "200:microliter"},
                ],
            )
        with pytest.raises(TypeError):
            p.flow_analyze(
                dataref="Test",
                FSC={"voltage_range": {"low": "230:volt", "high": "280:volt"}},
                SSC={"voltage_range": {"low": "230:volt", "high": "380:volt"}},
                neg_controls=[
                    {
                        "well": container,
                        "volume": "200:microliter",
                        "channel": ["FSC", "SSC"],
                    }
                ],
                samples=[
                    {"well": container2.well(0), "volume": "200:microliter"},
                    {"well": container2.well(1), "volume": "200:microliter"},
                    {"well": container2.well(2), "volume": "200:microliter"},
                ],
            )
        with pytest.raises(UnitError):
            p.flow_analyze(
                dataref="Test",
                FSC={"voltage_range": {"low": "230:volt", "high": "280:volt"}},
                SSC={"voltage_range": {"low": "230:volt", "high": "380:volt"}},
                neg_controls=[{"well": container.well(0), "channel": ["FSC", "SSC"]}],
                samples=[
                    {"well": container2.well(0), "volume": "200:microliter"},
                    {"well": container2.well(1), "volume": "200:microliter"},
                    {"well": container2.well(2), "volume": "200:microliter"},
                ],
            )
        with pytest.raises(UnitError):
            p.flow_analyze(
                dataref="Test",
                FSC={"voltage_range": {"low": "230:volt", "high": "280:volt"}},
                SSC={"voltage_range": {"low": "230:volt", "high": "380:volt"}},
                neg_controls=[
                    {
                        "well": container.well(0),
                        "volume": "200:microliter",
                        "channel": ["FSC", "SSC"],
                    }
                ],
                samples=[
                    {"well": container2.well(0), "volume": "200:microliter"},
                    {"well": container2.well(1), "volume": "200:microliter"},
                    {"well": container2.well(2), "volume": "200:microliter"},
                ],
                colors=colors,
            )


class TestDyeTest(object):
    def test_add_dye_to_preview_refs(self):
        p1 = Protocol()
        c1 = p1.ref("c1", id=None, cont_type="96-pcr", discard=True)
        c1.well(0).set_volume("10:microliter")
        _add_dye_to_preview_refs(p1)

        assert len(p1.instructions) == 1
        assert p1.instructions[0].op == "provision"
        assert p1.instructions[0].data["resource_id"] == "rs18qmhr7t9jwq"
        assert len(p1.instructions[0].data["to"]) == 1
        assert p1.instructions[0].data["to"][0]["volume"] == Unit(10, "microliter")
        assert p1.instructions[0].data["to"][0]["well"] == c1.well(0)
        assert c1.well(0).volume == Unit(10, "microliter")

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

        assert p1.instructions[1].data["resource_id"] == "rs18s8x4qbsvjz"
        assert p1.instructions[3].data["resource_id"] == "rs17gmh5wafm5p"

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
        c2 = p1.ref("c2", id=None, cont_type="res-sw96-hp", discard=True)
        c2.well(0).set_volume("50:milliliter")
        p1.incubate(c1, where="ambient", duration="1:hour", uncovered=True)
        p1.dispense(
            c1,
            "rs18s8x4qbsvjz",
            [{"column": 0, "volume": "10:microliter"}],
            is_resource_id=True,
        )
        p1.dispense(c1, "pbs", [{"column": 1, "volume": "10:microliter"}])
        p1.dispense(c1, c2.well(0), [{"column": 2, "volume": "10:microliter"}])
        p1.incubate(c1, where="ambient", duration="1:hour", uncovered=True)
        p1.dispense(
            c1,
            "rs18s8x4qbsvjz",
            [{"column": 3, "volume": "10:microliter"}],
            is_resource_id=True,
        )
        p1.dispense(c1, "pbs", [{"column": 4, "volume": "10:microliter"}])
        p1.dispense(c1, c2.well(0), [{"column": 5, "volume": "10:microliter"}])
        _convert_dispense_instructions(p1, 4, 7)

        assert "resource_id" in p1.instructions[1].data
        assert "reagent" not in p1.instructions[1].data
        assert "reagent_source" not in p1.instructions[1].data

        assert "resource_id" not in p1.instructions[2].data
        assert "reagent" in p1.instructions[2].data
        assert "reagent_source" not in p1.instructions[2].data

        assert "resource_id" not in p1.instructions[3].data
        assert "reagent" not in p1.instructions[3].data
        assert "reagent_source" in p1.instructions[3].data

        assert "resource_id" in p1.instructions[5].data
        assert "reagent" not in p1.instructions[5].data
        assert "reagent_source" not in p1.instructions[5].data

        assert "resource_id" in p1.instructions[6].data
        assert "reagent" not in p1.instructions[6].data
        assert "reagent_source" not in p1.instructions[6].data

        assert "resource_id" not in p1.instructions[7].data
        assert "reagent" not in p1.instructions[7].data
        assert "reagent_source" in p1.instructions[7].data

        assert p1.instructions[1].data["resource_id"] == "rs18s8x4qbsvjz"
        assert p1.instructions[2].data["reagent"] == "pbs"
        assert p1.instructions[3].data["reagent_source"] == c2.well(0)
        assert p1.instructions[5].data["resource_id"] == "rs17gmh5wafm5p"
        assert p1.instructions[6].data["resource_id"] == "rs17gmh5wafm5p"
        assert p1.instructions[7].data["reagent_source"] == c2.well(0)

        with pytest.raises(ValueError):
            _convert_dispense_instructions(p1, "4", 7)

        with pytest.raises(ValueError):
            _convert_dispense_instructions(p1, 4, "7")

        with pytest.raises(ValueError):
            _convert_dispense_instructions(p1, -1, 7)

        with pytest.raises(ValueError):
            _convert_dispense_instructions(p1, 8, 9)

        with pytest.raises(ValueError):
            _convert_dispense_instructions(p1, 3, 9)

        with pytest.raises(ValueError):
            _convert_dispense_instructions(p1, 7, 4)


class TestAgitate(object):
    # pylint: disable=invalid-name
    p = Protocol()
    pl1 = p.ref("pl1", id=None, cont_type="96-pcr", discard=True)
    t1 = p.ref("t1", id=None, cont_type="micro-2.0", discard=True)

    def test_param_checks(self):
        with pytest.raises(TypeError):
            self.p.agitate(self.pl1, "roll", duration="5:minute", speed="100:rpm")
        with pytest.raises(TypeError):
            self.p.agitate(self.pl1, "invert", duration="5:minute", speed="100:rpm")
        with pytest.raises(ValueError):
            self.p.agitate(self.t1, "invert", duration="5:minute", speed="0:rpm")
        with pytest.raises(ValueError):
            self.p.agitate(self.pl1, "fake", duration="5:minute", speed="100:rpm")
        with pytest.raises(ValueError):
            self.p.agitate(self.pl1, "stir_bar", duration="5:minute", speed="100:rpm")
        with pytest.raises(TypeError):
            self.p.agitate(self.t1, "invert", duration="30:gram", speed="100;rpm")
        with pytest.raises(ValueError):
            self.p.agitate(self.t1, mode="vortex", duration="0:second", speed="100:rpm")
        with pytest.raises(ValueError):
            self.p.agitate(
                self.t1,
                mode="vortex",
                duration="3:minute",
                speed="250:rpm",
                mode_params={
                    "wells": Well(self.t1, 0),
                    "bar_shape": "cross",
                    "bar_length": "234:micrometer",
                },
            )
        with pytest.raises(ValueError):
            self.p.agitate(
                self.t1,
                mode="stir_bar",
                duration="3:minute",
                speed="250:rpm",
                mode_params={
                    "not_wells": Well(self.t1, 0),
                    "not_bar_shape": "cross",
                    "not_bar_length": "234:micrometer",
                },
            )
        with pytest.raises(ValueError):
            self.p.agitate(
                self.t1,
                mode="stir_bar",
                duration="3:minute",
                speed="250:rpm",
                mode_params={"wells": Well(self.t1, 0)},
            )

    # pylint: disable=no-self-use
    def test_roll(self, dummy_protocol):
        p = dummy_protocol
        t1 = p.ref("t1", id=None, cont_type="micro-2.0", discard=True)
        p.agitate(t1, "roll", duration="5:minute", speed="100:rpm")
        assert p.instructions[0].data["mode"] == "roll"

    def test_stir_bar(self, dummy_protocol):
        p = dummy_protocol
        t1 = p.ref("t1", id=None, cont_type="micro-2.0", discard=True)
        wells = Well(t1, 0)
        p.agitate(
            t1,
            "stir_bar",
            duration="5:minute",
            speed="1000:rpm",
            mode_params={
                "wells": wells,
                "bar_shape": "cross",
                "bar_length": "234:micrometer",
            },
        )
        assert p.instructions[0].data["mode"] == "stir_bar"

    def test_invert(self, dummy_protocol):
        p = dummy_protocol
        t1 = p.ref("t1", id=None, cont_type="micro-2.0", discard=True)
        p.agitate(t1, "invert", duration="5:minute", speed="100:rpm")
        assert p.instructions[0].data["mode"] == "invert"

    def test_vortex(self, dummy_protocol):
        p = dummy_protocol
        t1 = p.ref("t1", id=None, cont_type="micro-2.0", discard=True)
        p.agitate(t1, "vortex", duration="5:minute", speed="1000:rpm")
        assert p.instructions[0].data["mode"] == "vortex"


class TestIncubate(object):
    def test_incubate(self, dummy_protocol):
        p = dummy_protocol
        c1 = p.ref("c1", id=None, cont_type="96-flat", discard=True)

        p.incubate(
            c1,
            "ambient",
            "10:minute",
            shaking=True,
            target_temperature="50:celsius",
            shaking_params={"path": "cw_orbital", "frequency": "1700:rpm"},
        )
        assert p.instructions[-1].op == "incubate"


class TestSonicate(object):
    # pylint: disable=invalid-name
    p = Protocol()
    ws = p.ref("c1", id=None, cont_type="96-flat", discard=True).wells_from(0, 3)

    def test_sonicate(self):
        self.p.sonicate(
            self.ws,
            "1:minute",
            "bath",
            {"sample_holder": "suspender"},
            frequency="22:kilohertz",
            temperature="4:celsius",
        )
        assert self.p.instructions[-1].data["mode"] == "bath"
        assert self.p.instructions[-1].data["mode_params"] == {
            "sample_holder": "suspender"
        }
        assert self.p.instructions[-1].data["temperature"] == Unit("4:celsius")
        assert self.p.instructions[-1].data["frequency"] == Unit("22:kilohertz")

    def test_sonicate_one_well(self):
        self.p.sonicate(
            self.ws[0],
            "1:minute",
            "horn",
            {"duty_cycle": 0.2, "amplitude": "1:micrometer"},
            frequency="25:kilohertz",
            temperature="4:celsius",
        )
        assert self.p.instructions[-1].data["mode"] == "horn"
        assert len(self.p.instructions[-1].data["wells"]) == 1
        assert self.p.instructions[-1].data["temperature"] == Unit("4:celsius")
        assert self.p.instructions[-1].data["frequency"] == Unit("25:kilohertz")

    def test_sonicate_default(self):
        self.p.sonicate(
            self.ws,
            "1:minute",
            "horn",
            {"duty_cycle": 0.1, "amplitude": "3:micrometer"},
        )
        assert self.p.instructions[-1].op == "sonicate"
        assert "temperature" not in self.p.instructions[-1].data
        assert self.p.instructions[-1].data["frequency"] == Unit("20:kilohertz")

    def test_bad_params(self):
        with pytest.raises(ValueError):
            # invalid 'duty_cycle' parameter
            self.p.sonicate(
                self.ws,
                duration="1:minute",
                mode="horn",
                mode_params={"duty_cycle": 3.1, "amplitude": "3:micrometer"},
            )
        with pytest.raises(RuntimeError):
            # invalid mode parameter
            self.p.sonicate(
                self.ws[0],
                "1:minute",
                "bad_mode",
                {"duty_cycle": 0.2, "amplitude": "1:micrometer"},
                frequency="25:kilohertz",
                temperature="4:celsius",
            )
        with pytest.raises(TypeError):
            # invalid wells
            self.p.sonicate(
                "bad_wells",
                "1:minute",
                "horn",
                {"duty_cycle": 0.2, "amplitude": "1:micrometer"},
                frequency="25:kilohertz",
                temperature="4:celsius",
            )
        with pytest.raises(TypeError):
            # invalid wells
            self.p.sonicate(
                self.ws[0],
                "1:minute",
                "horn",
                "not_a_dict",
                frequency="25:kilohertz",
                temperature="4:celsius",
            )


class TestImage(object):
    p = Protocol()
    c1 = p.ref("c1", cont_type="96-pcr", discard=True)

    def test_image(self):
        self.p.image(
            self.c1,
            "top",
            "dataref_1",
            num_images=3,
            backlighting=False,
            exposure={"iso": 4},
            magnification=1.5,
        )
        assert self.p.instructions[-1].op == "image"
        assert self.p.instructions[-1].data["magnification"] == 1.5

    def test_image_default(self):
        self.p.image(self.c1, "top", "dataref_1")
        assert self.p.instructions[-1].op == "image"
        assert self.p.instructions[-1].data["magnification"] == 1.0
        assert self.p.instructions[-1].data["num_images"] == 1

    def test_image_params(self):
        self.p.image(self.c1, "top", "dataref_2", backlighting=True)
        assert self.p.instructions[-1].op == "image"
        assert self.p.instructions[-1].data["back_lighting"]

    def test_bad_inputs(self):
        with pytest.raises(ValueError):
            self.p.image(self.c1, "bad_mode", "dataref_1")
        with pytest.raises(TypeError):
            self.p.image(self.c1, "top", "dataref_1", num_images=0)
        with pytest.raises(TypeError):
            self.p.image(self.c1, "top", "dataref_1", num_images=None)
        with pytest.raises(TypeError):
            self.p.image(self.c1, "top", "dataref_1", exposure={"iso": "true"})


class TestSeal(object):
    p = Protocol()
    c1 = p.ref("c1", cont_type="96-pcr", discard=True)
    c2 = p.ref("c2", cont_type="384-flat", discard=True)

    def test_param_checks(self):
        with pytest.raises(RuntimeError):
            self.p.cover(self.c1)
            self.p.seal(self.c1)
        with pytest.raises(RuntimeError):
            self.p.seal(self.c2, mode="illegal")
        with pytest.raises(RuntimeError):
            self.p.seal(self.c1, type="aluminum")
        with pytest.raises(RuntimeError):
            self.p.seal(self.c1, mode="illegal")
        with pytest.raises(TypeError):
            self.p.seal(self.c1, temperature="bla")
        with pytest.raises(TypeError):
            self.p.seal(self.c1, duration="184:celsius")
        with pytest.raises(RuntimeError):
            self.p.seal(self.c1, mode="adhesive", duration="1:second")

    def test_consecutive_seals(self):
        p = Protocol()
        c1 = p.ref("c1", cont_type="96-pcr", discard=True)
        p.seal(c1, type="ultra-clear")
        p.seal(c1, type="foil")

        assert len(p.instructions) == 1
        assert p.instructions[0].data["type"] == "ultra-clear"

    def test_mode_params(self):
        p = Protocol()
        c1 = p.ref("c1", cont_type="96-pcr", discard=True)
        p.seal(c1, temperature="140:celsius")
        p.unseal(c1)
        p.seal(c1, duration="3:second")
        p.unseal(c1)
        p.seal(c1, temperature="140:celsius", duration="3:second")
        seal_instructions = [
            instr.data for instr in p.instructions if instr.op == "seal"
        ]

        assert seal_instructions[0]["mode"] == "thermal"
        assert "duration" not in seal_instructions[0]["mode_params"].keys()

        assert seal_instructions[1]["mode"] == "thermal"
        assert "temperature" not in seal_instructions[1]["mode_params"]

        assert seal_instructions[2]["mode"] == "thermal"
        assert seal_instructions[2]["mode_params"]["temperature"] == Unit("140:celsius")
        assert seal_instructions[2]["mode_params"]["duration"] == Unit("3:second")


class TestCountCells(object):
    p = Protocol()
    tube = p.ref("tube", id=None, cont_type="micro-1.5", discard=True)
    plate = p.ref("plate", id=None, cont_type="96-pcr", discard=True)

    def test_good_inputs(self):
        self.p.count_cells(
            self.tube.well(0), "10:microliter", "cell_count_1", labels=["trypan_blue"]
        )
        assert len(self.p.instructions) == 1

        self.p.count_cells(
            [self.tube.well(0), self.plate.well(0)],
            "10:microliter",
            "cell_count_2",
            ["trypan_blue"],
        )
        assert len(self.p.instructions) == 2

        self.p.count_cells(
            self.plate.wells_from(5, 10),
            Unit(5, "microliter"),
            "cell_count_3",
            ["trypan_blue"],
        )
        assert len(self.p.instructions) == 3

        self.p.count_cells(
            self.plate.wells_from(5, 10),
            Unit(5, "microliter"),
            "cell_count_4",
            ["trypan_blue", "trypan_blue"],
        )
        assert len(self.p.instructions) == 4

    def test_bad_inputs(self):
        # Bad wells input
        with pytest.raises(TypeError):
            # Container used instead of Well/WellGroup
            self.p.count_cells(
                self.tube, "10:microliter", "cell_count_4", ["trypan_blue"]
            )
        # Bad volume input
        with pytest.raises(TypeError):
            # Not a unit
            self.p.count_cells(self.tube.well(0), 10, "cell_count_4", ["trypan_blue"])
        with pytest.raises(TypeError):
            # Not of correct dimensionality
            self.p.count_cells(
                self.tube.well(0), "10:meter", "cell_count_4", ["trypan_blue"]
            )


class TestSPE(object):
    p = Protocol()
    sample = p.ref("Sample", None, "micro-1.5", discard=True).well(0)
    elution_well = p.ref("Elution", None, "micro-1.5", discard=True).well(0)
    elute_params = [
        SPE.builders.mobile_phase_params(
            volume="2:microliter",
            loading_flowrate="100:ul/second",
            settle_time="2:minute",
            processing_time="3:minute",
            flow_pressure="2:bar",
            resource_id="solvent_a",
            destination_well=elution_well,
            is_elute=True,
        )
    ]

    bad_elute_params = [
        SPE.builders.mobile_phase_params(
            volume="2:microliter",
            loading_flowrate="100:ul/second",
            settle_time="2:minute",
            processing_time="3:minute",
            flow_pressure="2:bar",
            resource_id="solvent_a",
        )
    ]

    load_sample_params = SPE.builders.mobile_phase_params(
        volume="10:microliter",
        loading_flowrate="1:ul/second",
        settle_time="2:minute",
        processing_time="3:minute",
        flow_pressure="2:bar",
        is_sample=True,
    )

    cartridge = "spe_cartridge"

    def test_good_inputs(self):
        self.p.spe(
            self.sample,
            self.cartridge,
            "positive",
            load_sample=self.load_sample_params,
            elute=self.elute_params,
        )
        assert self.p.instructions[-1].op == "spe"

    def test_bad_inputs(self):
        with pytest.raises(ValueError):
            self.p.spe(
                self.sample,
                self.cartridge,
                "positive",
                load_sample=self.load_sample_params,
                elute=self.bad_elute_params,
            )


class TestTransferVolume(object):
    @pytest.fixture(autouse=True)
    def setup(self):
        self.p = Protocol()  # pylint: disable=invalid-name
        self.container = self.p.ref("container", cont_type="96-flat", discard=True)

    def test_transfers_volume(self):
        transfer_volume = Unit("5:uL")
        self.p._transfer_volume(
            self.container.well(0),
            self.container.well(1),
            transfer_volume,
            shape=Instruction.builders.shape(),
        )
        assert self.container.well(1).volume == transfer_volume

    def test_doesnt_transfer_properties_by_default(self):
        self.container.well(0).set_properties({"foo": "bar"})
        self.p._transfer_volume(
            self.container.well(0),
            self.container.well(1),
            Unit("5:uL"),
            shape=Instruction.builders.shape(),
        )
        assert not self.container.well(1).properties

    def test_can_transfer_properties(self):
        self.p.propagate_properties = True
        self.container.well(0).set_properties({"foo": "bar"})
        self.p._transfer_volume(
            self.container.well(0),
            self.container.well(1),
            Unit("5:uL"),
            shape=Instruction.builders.shape(),
        )
        assert self.container.well(1).properties == self.container.well(0).properties

    def test_can_append_properties(self):
        """Expected behavior when propagating properties to wells with prior properties."""
        self.p.propagate_properties = True
        self.container.well(0).set_properties({"foo": ["bar0"], "bar": "foo1"})
        self.container.well(1).set_properties({"foo": ["bar1"], "bar": "foo2"})
        self.p._transfer_volume(
            self.container.well(0),
            self.container.well(1),
            Unit("5:uL"),
            shape=Instruction.builders.shape(),
        )
        assert self.container.well(1).properties == {
            "bar": "foo1",
            "foo": ["bar1", "bar0"],
        }


class TestEvaporate(object):
    p = Protocol()
    t1 = p.ref("c1", cont_type="micro-2.0", discard=True)

    def test_bad_args(self):
        with pytest.raises(TypeError):
            self.p.evaporate(
                self.t1,
                mode="vortex",
                evaporator_temperature=Unit("45:celsius"),
                duration=Unit("30:gram"),
            )
        with pytest.raises(ValueError):
            self.p.evaporate(
                self.t1,
                mode="fake",
                evaporator_temperature=Unit("45:celsius"),
                duration=Unit("30:minute"),
            )
        with pytest.raises(ValueError):
            self.p.evaporate(
                self.t1,
                mode="vortex",
                evaporator_temperature=Unit("5:celsius"),
                duration=Unit("30:minutes"),
                mode_params={"condenser_temperature": Unit("10: celsius")},
            )
        with pytest.raises(TypeError):
            self.p.evaporate(
                self.t1,
                mode="fake",
                evaporator_temperature=Unit("45:gram"),
                duration=Unit("30:minute"),
            )

    def test_good_args(self):
        self.p.evaporate(
            self.t1,
            mode="vortex",
            evaporator_temperature=Unit("45:celsius"),
            duration=Unit("30:minute"),
            mode_params={
                "vortex_speed": "100:rpm",
                "vacuum_pressure": "1:torr",
                "condenser_temperature": "20:degC",
            },
        )
        assert len(self.p.instructions) == 1

        self.p.evaporate(
            self.t1,
            mode="blowdown",
            evaporator_temperature=Unit("45:celsius"),
            duration=Unit("30:minute"),
            mode_params={
                "gas": "nitrogen",
                "blow_rate": Unit("200:ul/sec"),
                "vortex_speed": Unit("200:rpm"),
            },
        )
        assert self.p.instructions[0].op == "evaporate"
