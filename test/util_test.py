import pytest
from autoprotocol.util import check_unit
from autoprotocol.unit import Unit


class TestCheckUnit(object):
    def test_check_unit_inputs(self):
        with pytest.raises(TypeError):
            check_unit("1:s", "1:s", "1:s")
        with pytest.raises(TypeError):
            check_unit(Unit("1:s"), Unit("1:s"), Unit("1:celsius"))
        with pytest.raises(ValueError):
            check_unit(Unit("1:s"))

    def test_check_unit_outputs(self):
        val = Unit("1:s")
        lb = Unit("0:s")
        ub = Unit("2:s")

        # These are all valid checks
        assert(val == check_unit(val, lb))
        assert (val == check_unit(val, lb=val))

        assert (val == check_unit(val, ub=ub))
        assert (val == check_unit(val, ub=val))

        assert (val == check_unit(val, lb, ub))
        assert (val == check_unit(val, lb=val, ub=val))

        with pytest.raises(
            ValueError,
            message="Time 1:second has to be greater or equal to 2:second"
        ):
            check_unit(val, lb=Unit("2:s"))

        with pytest.raises(
            ValueError,
            message="Time 1:second has to be less than or equal to 0:second"
        ):
            check_unit(val, ub=Unit("0:s"))

        with pytest.raises(
                ValueError,
                message="Time 3:second has to be within [0:second, 2:second]"
        ):
            check_unit(Unit("3:s"), lb=lb, ub=ub)

