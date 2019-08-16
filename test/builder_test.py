# pragma pylint: disable=missing-docstring

import pytest
from autoprotocol.protocol import Protocol, Ref
from autoprotocol.instruction import Thermocycle, Dispense, Spectrophotometry, Agitate
from autoprotocol.builders import InstructionBuilders
from autoprotocol import Unit, Well
from autoprotocol.unit import UnitError


# pylint: disable=protected-access
class TestInstructionBuilders(object):
    builders = InstructionBuilders()

    def test_merge_param_dicts_without_overlap(self):
        left, right = {1: "a"}, {2: "b"}
        union = self.builders._merge_param_dicts(left, right)

        expected = left
        expected.update(right)

        assert union == expected

    def test_merge_param_dicts_with_none(self):
        left, right = {1: "a"}, {2: None}
        union = self.builders._merge_param_dicts(left, right)
        assert union == left

    def test_merge_param_dicts_with_overlap(self):
        left, right = {1: "a"}, {1: "b"}
        with pytest.raises(ValueError):
            self.builders._merge_param_dicts(left, right)

    def test_merge_param_dicts_with_missing_dict(self):
        left, right = {1: "a"}, None
        union = self.builders._merge_param_dicts(left, right)
        assert union == left


class TestDispenseBuilders(object):
    columns_reference = [
        {"column": 0, "volume": Unit("10:microliter")},
        {"column": 1, "volume": Unit("20:microliter")},
        {"column": 2, "volume": Unit("30:microliter")},
        {"column": 3, "volume": Unit("40:microliter")},
        {"column": 4, "volume": Unit("50:microliter")}
    ]

    def test_column(self):
        for column in self.columns_reference:
            assert(column == Dispense.builders.column(**column))

        with pytest.raises(TypeError):
            Dispense.builders.column(0, 5)

        with pytest.raises(ValueError):
            Dispense.builders.column("Zero", "5:uL")

    def test_columns(self):
        cols = Dispense.builders.columns(self.columns_reference)
        assert(cols == self.columns_reference)

        with pytest.raises(TypeError):
            Dispense.builders.columns([{"column": 0}])

        with pytest.raises(TypeError):
            Dispense.builders.columns([{"column": 0, "volume": 5}])

        with pytest.raises(ValueError):
            Dispense.builders.columns([{"column": "Zero", "volume": "5:uL"}])

        with pytest.raises(ValueError):
            Dispense.builders.columns([
                {"column": 0, "volume": "10:uL"},
                {"column": 0, "volume": "10:uL"}
            ])

        with pytest.raises(ValueError):
            Dispense.builders.columns([])

    def test_nozzle_position(self):
        assert(Dispense.builders.nozzle_position() == {})

        reference = {
            "position_x": Unit(-3, "mm"),
            "position_y": Unit(3, "mm"),
            "position_z": Unit(5, "mm")
        }
        pos = Dispense.builders.nozzle_position("-3:mm", "3:mm", "5:mm")
        assert(pos == reference)

    def test_shake_after(self):
        assert(
            Dispense.builders.shake_after(
                "5:second", "10:hertz", "landscape_linear", "1:mm"
            ) == {
                "duration": Unit(5, "second"),
                "frequency": Unit(10, "hertz"),
                "path": "landscape_linear",
                "amplitude": Unit(1, "millimeter")
            }
        )
        with pytest.raises(ValueError):
            Dispense.builders.shake_after("5:second", path="foo")

class TestThermocycleBuilders(object):
    def test_group_input(self):
        step = Thermocycle.builders.step('1:celsius', '1:s')
        with pytest.raises(TypeError):
            Thermocycle.builders.group(1, 1)
        with pytest.raises(TypeError):
            Thermocycle.builders.group([step], "1")

        with pytest.raises(ValueError):
            Thermocycle.builders.group([])
        with pytest.raises(ValueError):
            Thermocycle.builders.group([step], 0)

        with pytest.raises(TypeError):
            Thermocycle.builders.group([{}], 1)

    def test_group_output(self):
        step = Thermocycle.builders.step('1:celsius', '1:s')
        g = Thermocycle.builders.group(
            [step],
            1
        )
        assert (g['cycles'] == 1)
        assert (g['steps'] == [step])

    def test_step_input(self):
        with pytest.raises(TypeError):
            Thermocycle.builders.step('1:s', '1:celsius')
        with pytest.raises(TypeError):
            Thermocycle.builders.step('1:celsius', '1:s', "yes")
        # Test gradient format
        with pytest.raises(ValueError):
            Thermocycle.builders.step({'top': '1:celsius'}, '1:s')
        with pytest.raises(ValueError):
            Thermocycle.builders.step({'bottom': '1:celsius'}, '1:s')
        with pytest.raises(ValueError):
            Thermocycle.builders.step({'top': '1:celsius',
                                       'bottom': '1:celsius',
                                       'middle': '1:celsius'},
                                      '1:s')

    def test_step_output(self):
        s = Thermocycle.builders.step('1:celsius', '1:s', True)
        assert(s == {
            'temperature': Unit('1:celsius'),
            'duration': Unit('1:s'),
            'read': True
        })
        # Test Gradient
        s = Thermocycle.builders.step({'top': '1:celsius',
                                       'bottom': '0:celsius'},
                                      '1:s', True)
        assert (s == {
            'gradient': {'top': Unit('1:celsius'),
                         'bottom': Unit('0:celsius')},
            'duration': Unit('1:s'),
            'read': True
        })

    def test_dyes_valid(self):
        dye_builder = Thermocycle.builders.dyes(
            FRET=1,
            FAM=[1, 2]
        )
        assert dye_builder == {"FRET": [1], "FAM": [1, 2]}

    def test_dyes_invalid_dye(self):
        with pytest.raises(ValueError):
            Thermocycle.builders.dyes(
                FOO=1
            )

    def test_dyes_invalid_well(self):
        with pytest.raises(ValueError):
            Thermocycle.builders.dyes(
                FRET={}
            )


def cast_values_as_units(params):
    def to_unit(item):
        try:
            if isinstance(item, str):
                item = Unit(item)
        except UnitError:
            pass
        return item
    return {k: to_unit(v) for k, v in params.items()}


def merge_dicts(*dicts):
    merged_dict = dict()
    for _ in dicts:
        merged_dict.update(_)
    return merged_dict


class TestSpectrophotometryBuilders(object):
    wells = [Well("foo", 0)]
    filter_selection = {
        "shortpass": "500:nanometer",
        "longpass": "600:nanometer"
    }
    monochromator_selection = {
        "ideal": "550:nanometer"
    }
    shake = {
        "duration": "10:minute",
        "frequency": "3:hertz",
        "path": "ccw_orbital",
        "amplitude": "4:millimeter"
    }
    position_z_manual = {
        "manual": {
            "reference": "plate_bottom",
            "displacement": Unit("15:mm")
        }
    }
    position_z_calculated = {
        "calculated_from_wells": {
            "wells": wells,
            "heuristic": "max_mean_read_without_saturation"
        }
    }

    luminescence_req = {
        "wells": wells
    }
    luminescence_opt = {
        "num_flashes": 9,
        "settle_time": "1:seconds",
        "integration_time": "4:seconds",
        "gain": 0.2,
        "read_position": "top",
        "position_z": position_z_manual
    }
    luminescence = merge_dicts(luminescence_req, luminescence_opt)

    fluorescence_req = {
        "wells": wells,
        "excitation": [cast_values_as_units(filter_selection)],
        "emission": [cast_values_as_units(monochromator_selection)]
    }
    fluorescence_opt = {
        "num_flashes": 9,
        "settle_time": "1:seconds",
        "lag_time": "6:seconds",
        "integration_time": "4:seconds",
        "gain": 0.2,
        "read_position": "top",
        "position_z": position_z_calculated
    }
    fluorescence = merge_dicts(fluorescence_req, fluorescence_opt)

    absorbance_req = {
        "wells": wells,
        "wavelength": [Unit("600:nanometer")]
    }
    absorbance_opt = {
        "num_flashes": 6,
        "settle_time": "100:seconds",
        "read_position": "top",
        "position_z": position_z_manual
    }
    absorbance = merge_dicts(absorbance_req, absorbance_opt)

    def test_groups(self):
        absorbance = Spectrophotometry.builders.group(
            "absorbance",
            self.absorbance
        )

        fluorescence = Spectrophotometry.builders.group(
            "fluorescence",
            self.fluorescence
        )

        luminescence = Spectrophotometry.builders.group(
            "luminescence",
            self.luminescence
        )

        shake = Spectrophotometry.builders.group(
            "shake",
            self.shake
        )
        Spectrophotometry.builders.groups(
            [absorbance, fluorescence, luminescence, shake]
        )

    def test_absorbance_mode_params(self):
        assert(
            Spectrophotometry.builders.absorbance_mode_params(
                **self.absorbance) ==
            cast_values_as_units(self.absorbance)
        )

    def test_fluorescence_mode_params(self):
        assert(
            Spectrophotometry.builders.fluorescence_mode_params(
                **self.fluorescence) ==
            cast_values_as_units(self.fluorescence)
        )

    def test_luminescence_mode_params(self):
        assert(
            Spectrophotometry.builders.luminescence_mode_params(
                **self.luminescence) ==
            cast_values_as_units(self.luminescence)
        )

    def test_shake_params(self):
        # pylint: disable=protected-access
        assert(
            Spectrophotometry.builders._shake(**self.shake) ==
            cast_values_as_units(self.shake)
        )
        assert(
            Spectrophotometry.builders.shake_mode_params(**self.shake) ==
            cast_values_as_units(self.shake)
        )
        assert(
            Spectrophotometry.builders.shake_before(**self.shake) ==
            cast_values_as_units(self.shake)
        )

    def test_position_z_params(self):
        assert(
            Spectrophotometry.builders._position_z(self.position_z_manual) ==
            cast_values_as_units(self.position_z_manual)
        )
        assert(
            Spectrophotometry.builders._position_z(self.position_z_calculated)
            == cast_values_as_units(self.position_z_calculated)
        )

    def test_wavelength_selection(self):
        assert(
            Spectrophotometry.builders.wavelength_selection(
                **self.filter_selection) ==
            cast_values_as_units(self.filter_selection)
        )
        assert(
            Spectrophotometry.builders.wavelength_selection(
                **self.monochromator_selection) ==
            cast_values_as_units(self.monochromator_selection)
        )

    def test_optional_params(self):
        Spectrophotometry.builders.fluorescence_mode_params(
            **self.fluorescence_req
        )
        Spectrophotometry.builders.luminescence_mode_params(
            **self.luminescence_req
        )
        Spectrophotometry.builders.absorbance_mode_params(
            **self.absorbance_req
        )

class TestAgitateBuilders(object):
    p = Protocol()
    c1 = p.ref("c1", id=None, cont_type="96-pcr", discard=True)
    def test_mode_errors(self):
        with pytest.raises(TypeError):
            Agitate.builders.check_mode(self.c1, "invert")
        with pytest.raises(TypeError):
            Agitate.builders.check_mode(self.c1, "roll")
    def test_check_mode(self):
        assert(
            Agitate.builders.check_mode(self.c1, "vortex") ==
            "vortex"
        )
    def test_bar_params_errors(self):
        with pytest.raises(ValueError):
            Agitate.builders.bar_params(self.c1, "invert", bar_params=
            {"wells": Well(self.c1,0), "bar_shape": "cross",
             "bar_length": "234:micrometer"})
        with pytest.raises(ValueError):
            Agitate.builders.bar_params(self.c1, "stir_bar")
        with pytest.raises(TypeError):
            Agitate.builders.bar_params(self.c1, "stir_bar", bar_params=
            {"wells": Well(self.c1,0), "bar_shape": "fake",
             "bar_length": "234:micrometer"})
        with pytest.raises(ValueError):
            Agitate.builders.bar_params(self.c1, "stir_bar", bar_params=
            {"wells": Well(self.c1,0), "bar_shape": "bar"})
        with pytest.raises(TypeError):
            Agitate.builders.bar_params(self.c1, "stir_bar", bar_params=
            {"wells": Well(self.c1,0), "bar_shape": "fake",
             "bar_length": "234:milligram"})
        with pytest.raises(ValueError):
            Agitate.builders.bar_params(self.c1, "stir_bar", bar_params=
            {"wells": "fake wells", "bar_shape": "fake",
             "bar_length": "234:milligram"})
    def test_bar_params(self):
        assert(
            Agitate.builders.bar_params(self.c1, "stir_bar", bar_params=
            {"wells": Well(self.c1,0), "bar_shape": "bar",
             "bar_length": "20:millimeter"})
        )