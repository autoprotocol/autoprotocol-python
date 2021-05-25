import pytest

from autoprotocol.container_type import _CONTAINER_TYPES
from autoprotocol.instruction import LiquidHandle
from autoprotocol.protocol import Protocol
from autoprotocol.unit import Unit
from autoprotocol.util import _check_container_type_with_shape, parse_unit


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
        # asserts that no exception is raised. If it raises an exception, we catch it, display it, and assert False.
        try:
            container_type = _CONTAINER_TYPES["res-sw384-lp"]
            shape = LiquidHandle.builders.shape(1, 1, "SBS384")
            _check_container_type_with_shape(container_type, shape)
        except Exception as exc:  # pylint: disable=W0703
            assert False, f"{exc}"
        # asserts that an exception is raised of class ValueError
        with pytest.raises(ValueError):
            container_type = _CONTAINER_TYPES["res-sw96-hp"]
            shape = LiquidHandle.builders.shape(1, 1, "SBS384")
            _check_container_type_with_shape(container_type, shape)

    def test_stamp_single_well_to_384_well_reservoir(self):
        # asserts that no exception is raised. If it raises an exception, we catch it, display it, and assert False.
        try:
            p = Protocol()
            source = p.ref("source", cont_type="res-sw384-lp", discard=True)
            destination = p.ref("destination", cont_type="384-flat", discard=True)
            p.transfer(
                source=source.well(0),
                destination=destination.well(0),
                volume="10:microliter",
                rows=16,
                columns=24,
            )
        except Exception as exc:  # pylint: disable=W0703
            assert False, f"{exc}"
