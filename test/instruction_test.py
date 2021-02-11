import pytest

from autoprotocol import Unit
from autoprotocol.instruction import Dispense, Instruction


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

    @pytest.fixture
    def test_inst_with_informatics(self):
        example_data = {
            "some_param": "foo/1",
            "some_int": 1,
        }
        example_informatics = [
            {
                "type": "attach_compounds",
                "data": {
                    "wells": "foo/0",
                    "compounds": ["1S/C6H6/c1-2-4-6-5-3-1/h1-6H"],
                },
            }
        ]
        return Instruction(
            op="test_instruction", data=example_data, informatics=example_informatics
        )

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

    @staticmethod
    def test_informatics(test_inst_with_informatics):
        assert test_inst_with_informatics.informatics == [
            {
                "type": "attach_compounds",
                "data": {
                    "wells": "foo/0",
                    "compounds": ["1S/C6H6/c1-2-4-6-5-3-1/h1-6H"],
                },
            }
        ]

    def test_verify_informatics_field(self):
        assert Instruction(
            op="some_instruction",
            data={"some_field": "some_value"},
            informatics=[
                {
                    "type": "attach_compounds",
                    "data": {
                        "wells": "foo/0",
                        "compounds": ["1S/C6H6/c1-2-4-6-5-3-1/h1-6H"],
                    },
                }
            ],
        ).informatics == [
            {
                "type": "attach_compounds",
                "data": {
                    "wells": "foo/0",
                    "compounds": ["1S/C6H6/c1-2-4-6-5-3-1/h1-6H"],
                },
            }
        ]

        with pytest.raises(ValueError):
            Instruction(
                op="some instruction",
                data={"some_param": "some_value"},
                informatics=[
                    {
                        "type": "attach_compounds",
                        "data": {"wells": [], "compounds": None},
                    }
                ],
            )

        with pytest.raises(TypeError):
            Instruction._verify_informatics_field(["foo", "bar"])
        with pytest.raises(ValueError):
            Instruction._verify_informatics_field(
                [
                    {
                        "type": "foo",
                        "data": {
                            "wells": "foo/1",
                            "compounds": ["1S/ClH.Na/h1H;/q;+1/p-1/i;1+1"],
                        },
                    }
                ]
            )
        with pytest.raises(ValueError):
            Instruction._verify_informatics_field(
                [
                    {
                        "type": "attach_compounds",
                    }
                ]
            )
        with pytest.raises(ValueError):
            Instruction._verify_informatics_field(
                [{"type": "attach_compounds", "data": {"foo": "some_data"}}]
            )
        with pytest.raises(ValueError):
            Instruction._verify_informatics_field([{"foo": "bar"}])


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
