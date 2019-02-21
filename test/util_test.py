import pytest

from autoprotocol.util import parse_unit
from autoprotocol.unit import Unit


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
