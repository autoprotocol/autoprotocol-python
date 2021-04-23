import pytest

from autoprotocol.unit import Unit
from autoprotocol.util import parse_unit, _is_reservoir, _check_container_type_with_shape
from autoprotocol.container_type import _CONTAINER_TYPES


class TestParseUnit(object):
    def test_casting_to_unit(self):
        assert Unit("1:second") == parse_unit("1:second")
        assert Unit("1:ul") == parse_unit("1:microliter")

        with pytest.raises(TypeError):
            parse_unit("1 second")

    def test_accepted_unit(self):
        assert Unit("1:ul") == parse_unit("1:ul", "ml")
        assert Unit("1:ul") == parse_unit("1:ul", "milliliter")
        assert Unit("1:ul") == parse_unit("1:ul", "1:ml")
        assert Unit("1:ul") == parse_unit("1:ul", ["kg", "ml"])

        assert Unit("1:ul") == parse_unit(Unit("1:ul"), "ml")

        with pytest.raises(TypeError):
            parse_unit("1:ul", "second")

        with pytest.raises(TypeError):
            parse_unit("1:ul", ["second", "kg"])


    def test_reservoir(self):
        container_type = _CONTAINER_TYPES["res-sw384-lp"]
        shape_format = "SBS384"
        assert _is_reservoir(container_type, shape_format) == True

# For this to work I need to generate a legit shape, not sure how to do that.
""" 
from autoprotocol.builders import InstructionBuilders
    # def test_check_container_type_with_shape(self):
    #     container_type =  _CONTAINER_TYPES["res-sw384-lp"]
    #     shape = InstructionBuilders.shape(self, rows=1, columns=1, format="SBS384")
    #     _check_container_type_with_shape(container_type, shape)

"""

# a = TestParseUnit()

# a.test_reservoir()

# a.test_check_container_type_with_shape()

