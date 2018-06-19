from autoprotocol import Unit
from autoprotocol.instruction import Dispense
import pytest


class TestInstruction(object):
    def test_dispense_defined_sources(self):
        default_args = {
            "object": "foo",
            "columns": [{"column": 0, "volume": Unit(5, "uL")}]
        }

        with pytest.raises(ValueError):
            Dispense(**default_args)

        Dispense(reagent="baz", **default_args)
        Dispense(resource_id="baz", **default_args)
        Dispense(reagent_source="baz", **default_args)

        with pytest.raises(ValueError):
            Dispense(reagent="baz", resource_id="baz", **default_args)
