# pragma pylint: disable=missing-docstring,no-self-use
# pragma pylint: disable=too-few-public-methods, attribute-defined-outside-init
import pytest
from autoprotocol.instruction import LiquidHandle
from autoprotocol import Unit


class TestInstructionBuilders(object):
    def test_shape_builder(self):
        shape = {"rows": 1, "columns": 12, "format": "SBS96"}
        assert LiquidHandle.builders.shape(**shape) == shape

        with pytest.raises(ValueError):
            LiquidHandle.builders.shape(rows=100)

        with pytest.raises(ValueError):
            LiquidHandle.builders.shape(format="SBS24")

        with pytest.raises(ValueError):
            LiquidHandle.builders.shape(columns=13, format="SBS96")


class TestLiquidHandleBuilder(object):
    asp_transport = LiquidHandle.builders.transport(
        volume=Unit(1, "uL"),
        density=None,
        pump_override_volume=Unit(2, "uL"),
        flowrate=LiquidHandle.builders.flowrate(target=Unit(10, "uL/s")),
        delay_time=Unit(0.5, "s"),
        mode_params=LiquidHandle.builders.mode_params(
            liquid_class="air",
            position_z=LiquidHandle.builders.position_z(reference="preceding_position"),
        ),
    )

    def test_location_builder(self):
        location = {
            "location": "test_well/0",
            "transports": [LiquidHandle.builders.transport(volume="1:uL")],
        }
        assert LiquidHandle.builders.location(**location) == location

        with pytest.raises(ValueError):
            LiquidHandle.builders.location(transports=[])

    def test_transport_builder(self):
        transport = {
            "volume": Unit(1, "uL"),
            "density": None,
            "pump_override_volume": Unit(2, "uL"),
            "flowrate": LiquidHandle.builders.flowrate(target="2:uL/s"),
            "delay_time": Unit(5, "s"),
            "mode_params": LiquidHandle.builders.mode_params(liquid_class="air"),
        }
        assert LiquidHandle.builders.transport(**transport) == transport

    def test_transports_with_denisty_builder(self):
        transport = {
            "volume": Unit(5, "uL"),
            "density": Unit(1, "mg/ml"),
            "pump_override_volume": Unit(2, "uL"),
            "flowrate": LiquidHandle.builders.flowrate(target="2:uL/s"),
            "delay_time": Unit(5, "s"),
            "mode_params": LiquidHandle.builders.mode_params(liquid_class="air"),
        }
        density = LiquidHandle.builders.transport(**transport)["density"]
        assert density == Unit(1, "mg/ml")

    def test_flowrate_builder(self):
        flowrate = {
            "target": Unit(40, "uL/s"),
            "initial": Unit(30, "uL/s"),
            "cutoff": Unit(20, "uL/s"),
            "acceleration": Unit(10, "uL/s/s"),
            "deceleration": Unit(50, "uL/s/s"),
        }
        assert LiquidHandle.builders.flowrate(**flowrate) == flowrate

    def test_mode_params_builder(self):
        flat_mode_params = {
            "liquid_class": "air",
            "position_x": LiquidHandle.builders.position_xy(position=0.4),
            "position_y": LiquidHandle.builders.position_xy(position=0.5),
            "position_z": LiquidHandle.builders.position_z(reference="well_top"),
        }
        structured_mode_params = {
            "liquid_class": flat_mode_params["liquid_class"],
            "tip_position": {
                "position_x": flat_mode_params["position_x"],
                "position_y": flat_mode_params["position_y"],
                "position_z": flat_mode_params["position_z"],
            },
        }

        assert (
            LiquidHandle.builders.mode_params(**structured_mode_params)
            == LiquidHandle.builders.mode_params(**flat_mode_params)
            == structured_mode_params
        )

        with pytest.raises(ValueError):
            LiquidHandle.builders.mode_params(liquid_class="DMSO")

        with pytest.raises(ValueError):
            LiquidHandle.builders.mode_params(
                tip_position={"position_x": flat_mode_params["position_x"]},
                **flat_mode_params
            )

    def test_position_xy_builder(self):
        position_xy = {
            "position": 1,
            "move_rate": LiquidHandle.builders.move_rate(target="5:mm/s"),
        }
        assert LiquidHandle.builders.position_xy(**position_xy) == position_xy

        with pytest.raises(ValueError):
            LiquidHandle.builders.position_xy(position=2)

    def test_position_z_builder(self):
        flat_position_z = {
            "reference": "liquid_surface",
            "offset": Unit(-1, "mm"),
            "move_rate": LiquidHandle.builders.move_rate(target="10:mm/s"),
            "detection_method": "capacitance",
            "detection_threshold": Unit(10, "picofarad"),
            "detection_duration": Unit(1, "millisecond"),
            "detection_fallback": LiquidHandle.builders.position_z(
                reference="well_top"
            ),
        }
        structured_position_z = {
            "reference": flat_position_z["reference"],
            "offset": flat_position_z["offset"],
            "move_rate": flat_position_z["move_rate"],
            "detection": {
                "method": flat_position_z["detection_method"],
                "threshold": flat_position_z["detection_threshold"],
                "duration": flat_position_z["detection_duration"],
                "fallback": flat_position_z["detection_fallback"],
            },
        }

        assert (
            LiquidHandle.builders.position_z(**structured_position_z)
            == LiquidHandle.builders.position_z(**flat_position_z)
            == structured_position_z
        )

        extra_detection_arguments_positions_z = {
            "reference": flat_position_z["reference"],
            "offset": flat_position_z["offset"],
            "move_rate": flat_position_z["move_rate"],
            "detection": {
                "method": flat_position_z["detection_method"],
                "threshold": flat_position_z["detection_threshold"],
                "duration": flat_position_z["detection_duration"],
                "fallback": flat_position_z["detection_fallback"],
                "sensitivity": 20,
                "offset": 20,
            },
        }

        assert (
            LiquidHandle.builders.position_z(**extra_detection_arguments_positions_z)
            == extra_detection_arguments_positions_z
        )

        with pytest.raises(ValueError):
            LiquidHandle.builders.position_z(
                reference="well_top", detection_method="capacitance"
            )

        with pytest.raises(ValueError):
            LiquidHandle.builders.position_z(
                detection={"method": flat_position_z["detection_method"]},
                **flat_position_z
            )

    def test_move_rate_builder(self):
        move_rate = {"target": Unit(50, "mm/s"), "acceleration": Unit(100, "mm/s/s")}

        assert LiquidHandle.builders.move_rate(**move_rate) == move_rate

    def test_instruction_mode_params(self):
        mode_params = {"tip_type": "test"}
        assert (
            LiquidHandle.builders.instruction_mode_params(**mode_params) == mode_params
        )

    def test_mix_builder(self):
        mix = {
            "volume": Unit(5, "ul"),
            "repetitions": 4,
            "initial_z": LiquidHandle.builders.position_z(offset="3:mm"),
            "asp_flowrate": LiquidHandle.builders.flowrate(target="1:uL/s"),
            "dsp_flowrate": LiquidHandle.builders.flowrate(target="2:uL/s"),
        }
        assert LiquidHandle.builders.mix(**mix) == mix

    def test_blowout_builder(self):
        blowout = {
            "volume": Unit(3, "ul"),
            "initial_z": LiquidHandle.builders.position_z(offset="2:mm"),
            "flowrate": LiquidHandle.builders.flowrate(target="1:uL/s"),
        }
        assert LiquidHandle.builders.blowout(**blowout) == blowout

    def test_desired_mode_builder(self):
        transports_air = [
            LiquidHandle.builders.transport(
                volume=Unit(1, "uL"),
                density=None,
                pump_override_volume=Unit(2, "uL"),
                flowrate=LiquidHandle.builders.flowrate(target=Unit(10, "uL/s")),
                delay_time=Unit(0.5, "s"),
                mode_params=LiquidHandle.builders.mode_params(
                    liquid_class="air",
                    position_z=LiquidHandle.builders.position_z(
                        reference="preceding_position"
                    ),
                ),
            ),
            LiquidHandle.builders.transport(
                volume=Unit(1, "uL"),
                density=None,
                pump_override_volume=Unit(2, "uL"),
                flowrate=LiquidHandle.builders.flowrate(target=Unit(10, "uL/s")),
                delay_time=Unit(0.5, "s"),
                mode_params=LiquidHandle.builders.mode_params(
                    liquid_class="air",
                    position_z=LiquidHandle.builders.position_z(
                        reference="preceding_position"
                    ),
                ),
            ),
        ]
        transports_viscous = [
            LiquidHandle.builders.transport(
                volume=Unit(1, "uL"),
                density=None,
                pump_override_volume=Unit(2, "uL"),
                flowrate=LiquidHandle.builders.flowrate(target=Unit(10, "uL/s")),
                delay_time=Unit(0.5, "s"),
                mode_params=LiquidHandle.builders.mode_params(
                    liquid_class="air",
                    position_z=LiquidHandle.builders.position_z(
                        reference="preceding_position"
                    ),
                ),
            ),
            LiquidHandle.builders.transport(
                volume=Unit(1, "uL"),
                density=None,
                pump_override_volume=Unit(2, "uL"),
                flowrate=LiquidHandle.builders.flowrate(target=Unit(10, "uL/s")),
                delay_time=Unit(0.5, "s"),
                mode_params=LiquidHandle.builders.mode_params(
                    liquid_class="viscous",
                    position_z=LiquidHandle.builders.position_z(
                        reference="preceding_position"
                    ),
                ),
            ),
        ]
        transports_none = [
            LiquidHandle.builders.transport(
                volume=Unit(1, "uL"),
                density=None,
                pump_override_volume=Unit(2, "uL"),
                flowrate=LiquidHandle.builders.flowrate(target=Unit(10, "uL/s")),
                delay_time=Unit(0.5, "s"),
                mode_params=LiquidHandle.builders.mode_params(
                    liquid_class=None,
                    position_z=LiquidHandle.builders.position_z(
                        reference="preceding_position"
                    ),
                ),
            ),
            LiquidHandle.builders.transport(
                volume=Unit(1, "uL"),
                density=None,
                pump_override_volume=Unit(2, "uL"),
                flowrate=LiquidHandle.builders.flowrate(target=Unit(10, "uL/s")),
                delay_time=Unit(0.5, "s"),
                mode_params=LiquidHandle.builders.mode_params(
                    liquid_class=None,
                    position_z=LiquidHandle.builders.position_z(
                        reference="preceding_position"
                    ),
                ),
            ),
        ]
        transports_no_mode_params = [
            LiquidHandle.builders.transport(
                volume=Unit(1, "uL"),
                density=None,
                pump_override_volume=Unit(2, "uL"),
                flowrate=LiquidHandle.builders.flowrate(target=Unit(10, "uL/s")),
                delay_time=Unit(0.5, "s"),
                mode_params=None,
            )
        ]
        transports_invalid = [
            LiquidHandle.builders.transport(
                volume=Unit(1, "uL"),
                density=None,
                pump_override_volume=Unit(2, "uL"),
                flowrate=LiquidHandle.builders.flowrate(target=Unit(10, "uL/s")),
                delay_time=Unit(0.5, "s"),
                mode_params=LiquidHandle.builders.mode_params(
                    liquid_class="viscous",
                    position_z=LiquidHandle.builders.position_z(
                        reference="preceding_position"
                    ),
                ),
            ),
            LiquidHandle.builders.transport(
                volume=Unit(1, "uL"),
                density=None,
                pump_override_volume=Unit(2, "uL"),
                flowrate=LiquidHandle.builders.flowrate(target=Unit(10, "uL/s")),
                delay_time=Unit(0.5, "s"),
                mode_params=LiquidHandle.builders.mode_params(
                    liquid_class="default",
                    position_z=LiquidHandle.builders.position_z(
                        reference="preceding_position"
                    ),
                ),
            ),
        ]
        mode_air = {"transports": transports_air, "mode": None}
        mode_viscous = {"transports": transports_viscous, "mode": None}
        mode_none = {"transports": transports_none, "mode": None}
        mode_viscous_air = {
            "transports": transports_viscous,
            "mode": "air_displacement",
        }
        mode_no_mode_params = {"transports": transports_no_mode_params, "mode": None}
        assert LiquidHandle.builders.desired_mode(**mode_air) == "air_displacement"
        assert (
            LiquidHandle.builders.desired_mode(**mode_viscous)
            == "positive_displacement"
        )
        assert LiquidHandle.builders.desired_mode(**mode_none) == "air_displacement"
        assert (
            LiquidHandle.builders.desired_mode(**mode_viscous_air) == "air_displacement"
        )
        assert (
            LiquidHandle.builders.desired_mode(**mode_no_mode_params)
            == "air_displacement"
        )
        # failure tests
        with pytest.raises(ValueError):
            LiquidHandle.builders.desired_mode(transports_air, "foo")
        with pytest.raises(ValueError):
            LiquidHandle.builders.desired_mode(transports_invalid, None)
