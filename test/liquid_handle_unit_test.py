# pragma pylint: disable=missing-docstring, no-self-use, invalid-name
# pragma pylint: disable=too-few-public-methods, attribute-defined-outside-init
# pragma pylint: disable=protected-access
import pytest
from autoprotocol import Unit
from autoprotocol.liquid_handle.tip_type import TipType
from autoprotocol.liquid_handle import LiquidHandleMethod, Transfer, Mix
from autoprotocol.liquid_handle.liquid_class import (
    LiquidClass,
    VolumeCalibration,
    VolumeCalibrationBin,
)
from autoprotocol.instruction import LiquidHandle


class LiquidClassTester(object):
    tip_type = "generic_1_50"

    vol_bin_1 = VolumeCalibrationBin(3, "3:uL")
    vol_bin_5 = VolumeCalibrationBin(1, "1:uL")
    vol_calibration_curve = VolumeCalibration(
        (Unit("5:uL"), vol_bin_5), (Unit("1:uL"), vol_bin_1)
    )
    volume_calibration = {tip_type: vol_calibration_curve}

    flow_bin_5 = LiquidHandle.builders.flowrate(target="3:uL/s")
    flow_bin_1 = LiquidHandle.builders.flowrate(target="7:uL/s")
    flowrate_calibration = {
        tip_type: VolumeCalibration(
            (Unit("5:uL"), flow_bin_5), (Unit("1:uL"), flow_bin_1)
        )
    }

    @pytest.fixture(autouse=True)
    def setup(self):
        self.lc = LiquidClass()
        self.lc.volume_calibration_curve = self.volume_calibration
        self.lc.aspirate_flowrate_calibration_curve = self.flowrate_calibration
        self.lc.dispense_flowrate_calibration_curve = self.flowrate_calibration


class TestLiquidClass(LiquidClassTester):
    def test_volume_calibration_calibrates_volume(self):
        volume = Unit(1.23, "uL")
        slope = 3.14
        intercept = Unit(5, "uL")
        calibration = VolumeCalibrationBin(slope, intercept)
        assert calibration.calibrate_volume(volume) == slope * volume + intercept

    def test_calibration_curve_bins_values(self):
        curve = self.vol_calibration_curve
        assert curve.binned_calibration_for_volume("0.5:uL") == self.vol_bin_1
        assert curve.binned_calibration_for_volume("5.0:uL") == self.vol_bin_5

        with pytest.raises(RuntimeError):
            curve.binned_calibration_for_volume("7.0:uL")

    def test_liquid_class_volume_calibration(self):
        assert self.lc._get_calibrated_volume(Unit(1, "ul"), self.tip_type) == Unit(
            6, "ul"
        )

        with pytest.raises(KeyError):
            self.lc._get_calibrated_volume(Unit(1, "ul"), "fake_tip_type")

    def test_rec_flowrates(self):
        assert (
            self.lc._get_aspirate_flowrate(Unit(0.5, "ul"), "generic_1_50")
            == self.flow_bin_1
        )
        assert (
            self.lc._get_dispense_flowrate(Unit(4.5, "ul"), "generic_1_50")
            == self.flow_bin_5
        )

    def test_specified_point_params(self):
        test_vol = "vol"
        test_asp_flow = {"test": "asp"}
        test_dsp_flow = {"test": "dsp"}
        point_lc = LiquidClass(
            calibrated_volume=test_vol,
            aspirate_flowrate=test_asp_flow,
            dispense_flowrate=test_dsp_flow,
        )
        assert (
            point_lc._get_calibrated_volume(Unit(0.5, "ul"), "generic_1_50") == test_vol
        )
        assert (
            point_lc._get_aspirate_flowrate(Unit(0.5, "ul"), "generic_1_50")
            == test_asp_flow
        )
        assert (
            point_lc._get_dispense_flowrate(Unit(0.5, "ul"), "generic_1_50")
            == test_dsp_flow
        )


class LiquidHandleMethodTester(object):
    single_shape = LiquidHandle.builders.shape(1, 1, "SBS96")
    preceding_z = LiquidHandle.builders.position_z(reference="preceding_position")
    empty_z = LiquidHandle.builders.position_z()
    well_top_z = LiquidHandle.builders.position_z(reference="well_top")
    well_top_transport = LiquidHandle.builders.transport(
        mode_params=LiquidHandle.builders.mode_params(position_z=well_top_z)
    )
    surface_z = LiquidHandle.builders.position_z(reference="liquid_surface")
    surface_transport = LiquidHandle.builders.transport(
        mode_params=LiquidHandle.builders.mode_params(position_z=surface_z)
    )
    surface_tracked_z = LiquidHandle.builders.position_z(
        reference="liquid_surface", detection_method="tracked"
    )
    surface_sensing_z = LiquidHandle.builders.position_z(
        reference="liquid_surface", detection_method="capacitance"
    )
    asp_transport = LiquidHandle.builders.transport(
        volume=Unit(1, "uL"),
        pump_override_volume=Unit(2, "uL"),
        flowrate=LiquidHandle.builders.flowrate(target=Unit(10, "uL/s")),
        delay_time=Unit(0.5, "s"),
        mode_params=LiquidHandle.builders.mode_params(
            liquid_class="air",
            position_z=LiquidHandle.builders.position_z(reference="preceding_position"),
        ),
    )

    @pytest.fixture(autouse=True)
    def setup(self):
        self.lhm = LiquidHandleMethod()
        self.lhm._shape = self.single_shape


class TestLiquidHandleMethod(LiquidHandleMethodTester):
    def test_get_tip_types(self):
        expected = ["generic_1_50", "generic_1_1000"]
        actual = [_.name for _ in self.lhm._get_tip_types()]
        assert actual == expected

    def test_get_sorted_tip_types(self):
        tip_types = [
            TipType("generic_1_1000", Unit("1000:ul")),
            TipType("generic_1_50", Unit("50:ul")),
        ]
        self.lhm._get_tip_types = lambda: tip_types

        assert self.lhm._get_sorted_tip_types() == tip_types[::-1]

    def test_is_single_channel(self):
        assert self.lhm._is_single_channel() is True
        self.lhm._shape = LiquidHandle.builders.shape(2)
        assert self.lhm._is_single_channel() is False

    def test_move_to_top_before_lld_with_surface_lld(self):
        self.lhm._move_to_well_top_before_lld(self.surface_z)
        assert self.lhm._transports[0] == self.well_top_transport

    def test_move_to_top_before_lld_with_surface_tracked(self):
        self.lhm._move_to_well_top_before_lld(self.surface_tracked_z)
        assert not self.lhm._transports

    def test_move_to_top_before_lld_without_lld(self):
        self.lhm._move_to_well_top_before_lld(self.empty_z)
        assert not self.lhm._transports

    def test_move_to_initial_position_with_no_positions(self):
        self.lhm._move_to_initial_position(None, None, None)
        assert not self.lhm._transports

    def test_move_to_initial_position_with_position_xy(self):
        position_x = LiquidHandle.builders.position_xy(1)
        position_y = LiquidHandle.builders.position_xy(-1)
        followup_position = self.lhm._move_to_initial_position(
            position_x=position_x, position_y=position_y
        )
        actual_position = self.lhm._transports[0]["mode_params"]
        reference_position = LiquidHandle.builders.mode_params(
            position_x=position_x, position_y=position_y
        )
        assert actual_position == reference_position
        assert followup_position == self.preceding_z
        assert len(self.lhm._transports) == 1

    def test_move_to_initial_position_with_surface_position_z(self):
        followup_position = self.lhm._move_to_initial_position(
            position_z=self.surface_z
        )
        well_top_transport = self.lhm._transports[0]
        lld_transport = self.lhm._transports[1]
        assert well_top_transport == self.well_top_transport
        assert lld_transport == self.surface_transport
        assert followup_position == self.surface_tracked_z
        assert len(self.lhm._transports) == 2

    def test_get_followup_z_with_no_position(self):
        assert self.lhm._get_followup_z(None) == self.preceding_z

    def test_get_followup_z_with_non_surface_position(self):
        followup = self.lhm._get_followup_z(self.well_top_z)
        assert followup == self.preceding_z

    def test_get_followup_z_with_surface_tracked_position(self):
        followup = self.lhm._get_followup_z(self.surface_sensing_z)
        assert followup == self.surface_tracked_z

    def test_aspirate_simple(self):
        tip_position = self.asp_transport["mode_params"]["tip_position"]
        self.lhm._aspirate_simple(
            # pylint: disable=invalid-unary-operand-type
            volume=-self.asp_transport["volume"],
            # pylint: disable=invalid-unary-operand-type
            calibrated_vol=-self.asp_transport["pump_override_volume"],
            initial_z=self.well_top_z,
            position_x=tip_position["position_x"],
            position_y=tip_position["position_y"],
            flowrate=self.asp_transport["flowrate"],
            delay_time=self.asp_transport["delay_time"],
            liquid_class=self.asp_transport["mode_params"]["liquid_class"],
        )
        assert self.lhm._transports[0] == self.well_top_transport
        assert self.lhm._transports[1] == self.asp_transport

    def test_aspirate_with_prime(self):
        prime_vol = Unit(5, "microliter")
        tip_position = self.asp_transport["mode_params"]["tip_position"]
        self.lhm._aspirate_with_prime(
            # pylint: disable=invalid-unary-operand-type
            volume=-self.asp_transport["volume"],
            prime_vol=prime_vol,
            # pylint: disable=invalid-unary-operand-type
            calibrated_vol=-self.asp_transport["pump_override_volume"],
            initial_z=self.well_top_z,
            position_x=tip_position["position_x"],
            position_y=tip_position["position_y"],
            asp_flowrate=self.asp_transport["flowrate"],
            dsp_flowrate=self.asp_transport["flowrate"],
            delay_time=self.asp_transport["delay_time"],
            liquid_class=self.asp_transport["mode_params"]["liquid_class"],
        )
        assert self.lhm._transports[0] == self.well_top_transport
        assert self.lhm._transports[2] == self.asp_transport

        prime_aspirate = self.asp_transport.copy()
        prime_dispense = self.asp_transport.copy()
        prime_aspirate["volume"] = -prime_vol
        prime_aspirate["pump_override_volume"] = -prime_vol
        prime_dispense["volume"] = prime_vol
        prime_dispense["pump_override_volume"] = prime_vol
        assert self.lhm._transports[1] == prime_aspirate
        assert self.lhm._transports[3] == prime_dispense

    def test_aspirate_simple_with_density(self):
        tip_position = self.asp_transport["mode_params"]["tip_position"]
        self.lhm._aspirate_simple(
            # pylint: disable=invalid-unary-operand-type
            volume=-self.asp_transport["volume"],
            # pylint: disable=invalid-unary-operand-type
            calibrated_vol=-self.asp_transport["pump_override_volume"],
            initial_z=self.well_top_z,
            position_x=tip_position["position_x"],
            position_y=tip_position["position_y"],
            flowrate=self.asp_transport["flowrate"],
            delay_time=self.asp_transport["delay_time"],
            liquid_class=self.asp_transport["mode_params"]["liquid_class"],
            density=Unit(1, "mg/ml"),
        )
        assert self.lhm._transports[0] == self.well_top_transport
        assert self.lhm._transports[1]["density"] == Unit(1, "mg/ml")

    def test_dispense_simple(self):
        tip_position = self.asp_transport["mode_params"]["tip_position"]
        self.lhm._dispense_simple(
            volume=self.asp_transport["volume"],
            calibrated_vol=self.asp_transport["pump_override_volume"],
            initial_z=self.well_top_z,
            position_x=tip_position["position_x"],
            position_y=tip_position["position_y"],
            flowrate=self.asp_transport["flowrate"],
            delay_time=self.asp_transport["delay_time"],
            liquid_class=self.asp_transport["mode_params"]["liquid_class"],
        )
        assert self.lhm._transports[0] == self.well_top_transport
        assert self.lhm._transports[1] == self.asp_transport

    def test_dispense_simple_with_density(self):
        tip_position = self.asp_transport["mode_params"]["tip_position"]
        self.lhm._dispense_simple(
            volume=self.asp_transport["volume"],
            calibrated_vol=self.asp_transport["pump_override_volume"],
            initial_z=self.well_top_z,
            position_x=tip_position["position_x"],
            position_y=tip_position["position_y"],
            flowrate=self.asp_transport["flowrate"],
            delay_time=self.asp_transport["delay_time"],
            liquid_class=self.asp_transport["mode_params"]["liquid_class"],
            density=Unit(1, "mg/ml"),
        )
        assert self.lhm._transports[0] == self.well_top_transport
        assert self.lhm._transports[1]["density"] == Unit(1, "mg/ml")

    def test_mix(self):
        mix_reps = 4
        mix_asp_transport = self.asp_transport.copy()
        mix_asp_transport["pump_override_volume"] = None
        mix_dsp_transport = self.asp_transport.copy()
        mix_dsp_transport["volume"] = -mix_dsp_transport["volume"]
        mix_dsp_transport["pump_override_volume"] = None

        tip_position = self.asp_transport["mode_params"]["tip_position"]
        self.lhm._mix(
            # pylint: disable=invalid-unary-operand-type
            volume=-self.asp_transport["volume"],
            repetitions=mix_reps,
            position_x=tip_position["position_x"],
            position_y=tip_position["position_y"],
            initial_z=self.well_top_z,
            asp_flowrate=self.asp_transport["flowrate"],
            dsp_flowrate=self.asp_transport["flowrate"],
            delay_time=self.asp_transport["delay_time"],
            liquid_class=self.asp_transport["mode_params"]["liquid_class"],
        )
        assert self.lhm._transports[0] == self.well_top_transport
        asp_transports = [self.lhm._transports[_] for _ in range(1, mix_reps, 2)]
        dsp_transports = [self.lhm._transports[_] for _ in range(2, mix_reps, 2)]
        assert all(_ == mix_asp_transport for _ in asp_transports)
        assert all(_ == mix_dsp_transport for _ in dsp_transports)

    def test_estimate_calibrated_volume_with_tip(self):
        calibrated_volume = Unit(5, "uL")
        calibrated_lc = LiquidClass(calibrated_volume=calibrated_volume)
        estimated_calibrated_volume = self.lhm._estimate_calibrated_volume(
            volume=Unit(1, "uL"), liquid=calibrated_lc, tip_type="test"
        )
        assert estimated_calibrated_volume == calibrated_volume

    def test_estimate_calibrated_volume_without_tip(self):
        target_volume = Unit(1, "uL")
        volume_multiplier = LiquidClass()._safe_volume_multiplier
        estimated_calibrated_volume = self.lhm._estimate_calibrated_volume(
            volume=target_volume, liquid=LiquidClass(), tip_type=None
        )
        assert estimated_calibrated_volume == target_volume * volume_multiplier

    def test_estimate_calibrated_volume_with_tip_but_not_calibration(self):
        target_volume = Unit(1, "uL")
        volume_multiplier = LiquidClass()._safe_volume_multiplier
        estimated_calibrated_volume = self.lhm._estimate_calibrated_volume(
            volume=target_volume, liquid=LiquidClass(), tip_type="generic_96_180"
        )
        assert estimated_calibrated_volume == target_volume * volume_multiplier


class TransferMethodTester(object):
    single_shape = LiquidHandle.builders.shape(1, 1, "SBS96")

    @pytest.fixture(autouse=True)
    def setup(self):
        self.transfer = Transfer()
        self.transfer._shape = self.single_shape
        self.transfer._source_liquid = LiquidClass()
        self.transfer._destination_liquid = LiquidClass()


class TestTransfer(TransferMethodTester):
    def test_rec_tip_type(self):
        assert self.transfer._rec_tip_type(Unit(20, "uL")) == "generic_1_50"
        # 24uL is the largest transfer vol that should use the 50ul tip
        assert self.transfer._rec_tip_type(Unit(24, "uL")) == "generic_1_50"
        # 50uL transfer uses larger tip because of overage_volume
        assert self.transfer._rec_tip_type(Unit(50, "uL")) == "generic_1_1000"

        with pytest.raises(RuntimeError):
            self.transfer._rec_tip_type(Unit(2000, "uL"))

    def test_calculate_overage_volume(self):
        transfer_vol = Unit(10, "uL")
        expected_overage = transfer_vol * 0.1 + Unit(5, "uL")
        overage_vol = self.transfer._calculate_overage_volume(transfer_vol)
        assert overage_vol == expected_overage

    def test_tip_capacity(self):
        total_capacity = Unit(1000, "uL")
        expected_capacity = total_capacity - (total_capacity * 0.1 + Unit(5, "uL"))
        assert self.transfer._tip_capacity() == expected_capacity

    def test_has_calibration_with_calibration(self):
        calibrated_lc = LiquidClass(calibrated_volume="5:uL")
        self.transfer._source_liquid = calibrated_lc
        assert self.transfer._has_calibration() is True

    def test_has_calibration_with_no_calibration(self):
        assert self.transfer._has_calibration() is False


class MixMethodTester(object):
    single_shape = LiquidHandle.builders.shape(1, 1, "SBS96")

    @pytest.fixture(autouse=True)
    def setup(self):
        self.mix = Mix()
        self.mix._shape = self.single_shape
        self.mix._liquid = LiquidClass()


class TestMix(MixMethodTester):
    def test_calculate_overage_volume(self):
        transfer_vol = Unit(10, "uL")
        expected_overage = transfer_vol * 0.1
        overage_vol = self.mix._calculate_overage_volume(transfer_vol)
        assert overage_vol == expected_overage

    def test_tip_capacity(self):
        total_capacity = Unit(1000, "uL")
        expected_capacity = total_capacity - (total_capacity * 0.1)
        assert self.mix._tip_capacity() == expected_capacity

    def test_has_calibration_with_calibration(self):
        calibrated_lc = LiquidClass(
            aspirate_flowrate=LiquidHandle.builders.flowrate(target="5:uL/s")
        )
        self.mix._liquid = calibrated_lc
        assert self.mix._has_calibration() is True
