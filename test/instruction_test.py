import pytest

from autoprotocol.compound import Compound
from autoprotocol.container import WellGroup
from autoprotocol.informatics import AttachCompounds
from autoprotocol.instruction import Dispense, Instruction
from autoprotocol.protocol import Protocol

# pylint: disable=protected-access
from autoprotocol.types.protocol import DispenseColumn
from autoprotocol.unit import Unit


class TestBaseInstruction(object):
    @pytest.fixture
    def test_instruction(self):
        example_data = {
            "dict_1": {
                "dict_1a": {
                    "empty": None,
                    "some_int": 12,
                    "list_1": [{"empty": None, "some_str": "something"}, {}],
                }
            },
            "empty": None,
            "dict_2": {"empty": None, "empty_list": [], "some_bool": False},
        }
        return Instruction(op="test_instruction", data=example_data)

    def test_remove_empty_fields(self):
        assert dict(some_str="something") == Instruction._remove_empty_fields(
            {"some_str": "something", "empty": None}
        )

        assert dict(
            some_str="something", dict_1=dict(some_int=1)
        ) == Instruction._remove_empty_fields(
            {
                "some_str": "something",
                "empty": None,
                "dict_1": {"some_int": 1, "empty": None},
            }
        )

        assert [dict(some_bool=True)] == Instruction._remove_empty_fields(
            [dict(some_bool=True, empty=None)]
        )
        assert [dict(some_bool=True)] == Instruction._remove_empty_fields(
            [dict(some_bool=True, empty={})]
        )
        assert [dict(some_bool=True)] == Instruction._remove_empty_fields(
            [dict(some_bool=True, empty=[])]
        )

        assert Instruction(
            op="some instruction",
            data={"not_empty": {"foo": "bar"}, "empty": {"foo": None, "bar": None}},
        ).data == {"not_empty": {"foo": "bar"}}

        assert Instruction(
            op="some instruction",
            data={"not_empty": ["foo", "bar"], "empty": [None, None]},
        ).data == {"not_empty": ["foo", "bar"]}

        assert (
            Instruction(
                op="some instruction",
                data={"some_param": "some_value"},
                informatics=None,
            ).informatics
            == []
        )

    @staticmethod
    def test_op(test_instruction):
        assert test_instruction.op == "test_instruction"

    @staticmethod
    def test_data(test_instruction):
        assert test_instruction.data == {
            "dict_1": {
                "dict_1a": {"some_int": 12, "list_1": [{"some_str": "something"}]}
            },
            "dict_2": {"some_bool": False},
        }

    @staticmethod
    def test_informatics():
        p = Protocol()
        cont1 = p.ref("cont1", None, "6-flat", discard=True)
        compd = Compound("Daylight Canonical SMILES", "CN1C=NC2=C1C(=O)N(C(=O)N2C)C")
        example_data = {
            "wells": [cont1.well(0), cont1.well(1)],
            "some_int": 1,
        }
        example_informatics = [AttachCompounds(cont1.well(0), [compd])]
        instr = Instruction(
            op="test_instruction", data=example_data, informatics=example_informatics
        )
        assert isinstance(instr.informatics[0], AttachCompounds)
        assert instr.informatics[0].compounds[0].value == "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"

        instr_multi = Instruction(
            op="test_instruction",
            data=example_data,
            informatics=[
                AttachCompounds(cont1.well(0), [compd]),
                AttachCompounds(cont1.well(1), [compd]),
            ],
        )
        assert len(instr_multi.informatics) == 2

    def test_get_wells(self):
        p = Protocol()
        cont1 = p.ref("cont1", None, "6-flat", discard=True)
        cont2 = p.ref("cont2", None, "6-flat", discard=True)
        example_data = {
            "list": [cont1.well(0), cont1.well(1)],
            "well": cont2,
            "dict": {"key1": 1, "key2": "bar", "dict_well": cont1.well(2)},
            "bar": [
                {"key4": "value", "key5": {"well": cont1.well(3)}},
                {"key4": "value", "key5": {"well_group": WellGroup([cont1.well(4)])}},
            ],
            "duplicate": cont1.well(0),
            "nest": [{"list": [{"more_nested": [{"wells": [cont1.well(5)]}]}]}],
        }
        inst = Instruction(op="test", data=example_data)

        wells = set(cont1.all_wells().wells + cont2.all_wells().wells)
        assert set(inst.get_wells(example_data)) == wells

    def test_info_wells_checker(self):
        p = Protocol()
        cont1 = p.ref("cont1", None, "6-flat", discard=True)
        compd = Compound("Daylight Canonical SMILES", "CN1C=NC2=C1C(=O)N(C(=O)N2C)C")
        example_data = {"objects": [cont1.well(0), cont1.well(1)], "some_int": 1}
        instr = Instruction(
            op="test_instruction",
            data=example_data,
            informatics=[AttachCompounds(cont1.well(0), [compd])],
        )
        avail_wells = instr.get_wells(instr.data)
        with pytest.raises(ValueError):
            instr.informatics[0].wells = None
            instr._check_info_wells(instr.informatics[0], avail_wells)
        with pytest.raises(TypeError):
            instr.informatics[0].wells = "cont1/0"
            instr._check_info_wells(instr.informatics[0], avail_wells)
        with pytest.raises(ValueError):
            instr.informatics[0].wells = cont1.well(10)
            instr._check_info_wells(instr.informatics[0], avail_wells)


class TestInstruction(object):
    def test_dispense_defined_sources(self):
        default_args = {
            "object": "foo",
            "columns": [{"column": 0, "volume": Unit(5, "uL")}],
        }

        with pytest.raises(ValueError):
            Dispense(**default_args)

        Dispense(reagent="baz", **default_args)
        Dispense(resource_id="baz", **default_args)
        Dispense(reagent_source="baz", **default_args)

        with pytest.raises(ValueError):
            Dispense(reagent="baz", resource_id="baz", **default_args)

    def test_dispense_defined_dispense_columns(self):
        default_args = {
            "object": "foo",
            "columns": [DispenseColumn(**{"column": 0, "volume": Unit(5, "uL")})],
        }

        with pytest.raises(ValueError):
            Dispense(**default_args)

        Dispense(reagent="baz", **default_args)
        Dispense(resource_id="baz", **default_args)
        Dispense(reagent_source="baz", **default_args)

        with pytest.raises(ValueError):
            Dispense(reagent="baz", resource_id="baz", **default_args)
