# pragma pylint: disable=C0111

import pytest
from autoprotocol.instruction import Thermocycle, Dispense, Spectrophotometry
from autoprotocol import Unit, Well


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


class TestThermocycleBuilders:
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


def cast_values_as_units(params):
    def to_unit(item):
        try:
            if isinstance(item, str):
                item = Unit(item)
        except:
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

    luminescence_req = {
        "wells": wells
    }
    luminescence_opt = {
        "num_flashes": 9,
        "settle_time": "1:seconds",
        "integration_time": "4:seconds",
        "gain": 0.2
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
        "read_position": "top"
    }
    fluorescence = merge_dicts(fluorescence_req, fluorescence_opt)

    absorbance_req = {
        "wells": wells,
        "wavelength": [Unit("600:nanometer")]
    }
    absorbance_opt = {
        "num_flashes": 6,
        "settle_time": "100:seconds"
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
