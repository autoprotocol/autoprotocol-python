import pytest

from autoprotocol.unit import Unit
from autoprotocol.util import parse_unit

from autoprotocol.container_type import _CONTAINER_TYPES
from autoprotocol.instruction import LiquidHandle
from autoprotocol.util import _check_container_type_with_shape

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

class TestUtil(object):
    def test_compatible_reservoir_container(self):
        container_type = _CONTAINER_TYPES["res-sw384-lp"]
        container_type.capabilities.append("sbs384_compatible")
        shape = LiquidHandle.builders.shape(1, 1, "SBS384")
        _check_container_type_with_shape(container_type, shape)