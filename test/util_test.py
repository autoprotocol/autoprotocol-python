import pytest

from autoprotocol.container_type import _CONTAINER_TYPES
from autoprotocol.instruction import LiquidHandle
from autoprotocol.protocol import Protocol
from autoprotocol.unit import Unit
from autoprotocol.util import (
    _check_container_type_with_shape,
    parse_unit,
    _validate_liha_shape,
)


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
    def test_liha_validation(self):
        # asserts that no exception is raised if liha params are valid.
        # Otherwise, raises ValueError
        try:
            _validate_liha_shape("x_mantis", {"rows": 1, "columns": 1})
        except Exception as exc: # pylint: disable=W0703
            assert False, f"{exc}"
        with pytest.raises(ValueError):
            _validate_liha_shape("x_mantis", {"rows": 2, "columns": 1})

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

    def test_stamp_384_well_to_single_well_reservoir_and_reverse(self):
        p = Protocol()
        source = p.ref("destination", cont_type="384-flat", discard=True)
        destination = p.ref("source", cont_type="res-sw384-lp", discard=True)
        p.transfer(
            source=source.well(0),
            destination=destination.well(0),
            volume="10:microliter",
            rows=16,
            columns=24,
        )
        assert p.instructions[-1].op == "liquid_handle"

        p = Protocol()
        source = p.ref("destination", cont_type="res-sw384-lp", discard=True)
        destination = p.ref("source", cont_type="384-flat", discard=True)
        p.transfer(
            source=source.well(0),
            destination=destination.well(0),
            volume="10:microliter",
            rows=16,
            columns=24,
        )
        assert p.instructions[-1].op == "liquid_handle"

    def test_stamp_384_reservoir_and_384_well_plate_to_96_well_plate(self):
        p = Protocol()
        source = p.ref("destination", cont_type="384-flat", discard=True)
        destination = p.ref("source", cont_type="96-flat", discard=True)
        with pytest.raises(ValueError):
            p.transfer(
                source=source.well(0),
                destination=destination.well(0),
                volume="10:microliter",
                rows=16,
                columns=24,
            )

        p = Protocol()
        source = p.ref("destination", cont_type="res-sw384-lp", discard=True)
        destination = p.ref("source", cont_type="96-flat", discard=True)
        with pytest.raises(ValueError):
            p.transfer(
                source=source.well(0),
                destination=destination.well(0),
                volume="10:microliter",
                rows=16,
                columns=24,
            )
