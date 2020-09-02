from autoprotocol import Unit
from autoprotocol.instruction import Instruction, Dispense
import pytest


# pylint: disable=protected-access
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

        assert (
            Instruction(
                op="some instruction",
                data={"not_empty": {"foo": "bar"}, "empty": {"foo": None, "bar": None}},
            ).data
            == {"not_empty": {"foo": "bar"}}
        )

        assert (
            Instruction(
                op="some instruction",
                data={"not_empty": ["foo", "bar"], "empty": [None, None]},
            ).data
            == {"not_empty": ["foo", "bar"]}
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
