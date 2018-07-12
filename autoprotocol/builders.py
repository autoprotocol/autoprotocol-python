"""Builders
Module containing builders, which help build inputs for Instruction parameters

    :copyright: 2018 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

Summary
-------
These builder methods are used to generate and validate complex data
structures used in Autoprotocol specification. Each of them is capable of
using their own output as input. Therefore these builders are also used as
inline checks in Protocol methods.

Notes
-----
Generally these builders should not be called from this file directly.
They're more easily accessible by referencing a specific Instruction's
builders attribute (e.g. `Spectrophotometry.Builders.mode_params`).

See Also
--------
Instruction
    Instructions corresponding to each of the builders
"""

from collections import Iterable
from numbers import Number
from .constants import SBS_FORMAT_SHAPES
from .util import parse_unit, is_valid_well
from .container import WellGroup, Well
from .unit import Unit


class InstructionBuilders(object):  # pylint: disable=too-few-public-methods
    """General builders that apply to multiple instructions
    """
    def __init__(self):
        self.sbs_shapes = ["SBS96", "SBS384"]

    # pylint: disable=redefined-builtin
    def shape(self, rows=1, columns=1, format=None):
        """
        Helper function for building a shape dictionary

        Parameters
        ----------
        rows : int, optional
            Number of rows to be concurrently transferred
        columns : int, optional
            Number of columns to be concurrently transferred
        format : str, optional
            Plate format in String form. e.g. "SBS96" or "SBS384"

        Returns
        -------
        dict
            shape parameters

        Raises
        ------
        TypeError
            If rows/columns aren't ints
        ValueError
            If an invalid row/column count is given
        ValueError
            If an invalid shape is given
        ValueError
            If rows/columns are greater than what is allowed for the format
        """
        if not isinstance(rows, int) or not isinstance(columns, int):
            raise TypeError("Rows/columns have to be of type integer")

        if format is None:
            for shape in self.sbs_shapes:
                valid_rows = rows <= SBS_FORMAT_SHAPES[shape]["rows"]
                valid_columns = columns <= SBS_FORMAT_SHAPES[shape]["columns"]
                if valid_rows and valid_columns:
                    format = shape
                    break

            if not format:
                raise ValueError(
                    "Invalid number of rows and/or columns specified")

        if format not in self.sbs_shapes:
            raise ValueError(
                "Invalid shape format; format has to be in {}".format(
                    self.sbs_shapes
                )
            )

        valid_rows = rows <= SBS_FORMAT_SHAPES[format]["rows"]
        valid_columns = columns <= SBS_FORMAT_SHAPES[format]["columns"]
        if not (valid_rows and valid_columns):
            raise ValueError(
                "rows: {} and columns: {} are not possible with format: {}."
                "".format(rows, columns, format)
            )

        return {
            "rows": rows,
            "columns": columns,
            "format": format
        }


# pylint: disable=no-init
class ThermocycleBuilders(InstructionBuilders):
    """
    These builders are meant for helping to construct the `groups`
    argument in the `Protocol.thermocycle` method
    """
    def group(self, steps, cycles=1):
        """
        Helper function for creating a thermocycle group, which is a series of
        steps repeated for the number of cycles

        Parameters
        ----------
        steps: list(ThermocycleBuilders.step)
            Steps to be carried out. At least one step has to be specified.
            See `ThermocycleBuilders.step` for more information
        cycles: int, optional
            Number of cycles to repeat the specified steps. Defaults to 1

        Returns
        -------
        dict
            A thermocycling group

        Raises
        ------
        TypeError
            Invalid input types, i.e. `cycles` is not of type int and `steps`
            is not of type list
        ValueError
            `cycles` is not positive
        ValueError
            `steps` does not contain any elements
        """
        if not isinstance(cycles, int):
            raise TypeError("`cycles` {} has to be of type int".format(cycles))
        if not isinstance(steps, list):
            raise TypeError("`steps` {} has to be of type list".format(steps))

        if cycles <= 0:
            raise ValueError("`cycles` {} has to be positive".format(cycles))
        if len(steps) <= 0:
            raise ValueError("`steps` has to contain at least one element")

        # Reformatting to use temperature for gradient input
        def reformat_gradient(**kwargs):
            if 'gradient' in kwargs:
                kwargs['temperature'] = kwargs.pop('gradient')
            return kwargs

        group_dict = dict(
            cycles=cycles,
            steps=[self.step(**reformat_gradient(**_)) for _ in steps]
        )

        return group_dict

    @staticmethod
    def step(temperature, duration, read=None):
        """
        Helper function for creating a thermocycle step.

        Parameters
        ----------
        temperature: Unit or dict(str, Unit)
            Block temperature which the contents should be thermocycled at.

            If a gradient thermocycle is desired, specifying a dict with
            "top" and "bottom" keys will control the desired temperature
            at the top and bottom rows of the block, creating a gradient
            along the column.

            ..code-block:: python

              temperature = {"top": "50:celsius", "bottom": "45:celsius"}

        duration: str or Unit
            Duration where the specified temperature parameters will be applied
        read: Boolean, optional
            Determines if a read at wavelengths specified by the dyes in the
            parent `thermocycle` instruction will be enabled for this particular
            step. Useful for qPCR applications.

        Returns
        -------
        dict
            A thermocycling step

        Raises
        ------
        TypeError
            Invalid input types, e.g. `read` is not of type bool
        ValueError
            Invalid format specified for `temperature` dict
        ValueError
            Duration is not greater than 0 second

        """
        step_dict = dict()
        if isinstance(temperature, dict):
            if set(temperature.keys()) != {'top', 'bottom'}:
                raise ValueError("{} was specified, but only 'top' and 'bottom'"
                                 " keys are allowed for a temperature "
                                 "dictionary".format(temperature))
            step_dict['gradient'] = dict(
                top=parse_unit(temperature['top'], "celsius"),
                bottom=parse_unit(temperature['bottom'], "celsius")
            )
        else:
            step_dict['temperature'] = parse_unit(temperature, 'celsius')

        duration = parse_unit(duration, 'second')
        if duration <= Unit("0:second"):
            raise ValueError("Step `duration` has to be at least 1 second")
        step_dict['duration'] = duration

        if read is not None:
            if not isinstance(read, bool):
                raise TypeError("`read` {} has to be of type bool".format(read))
            step_dict['read'] = read

        return step_dict


class DispenseBuilders(InstructionBuilders):
    """
    These builders are meant for helping to construct arguments in the
    `Protocol.dispense` method.
    """
    def __init__(self):
        super(DispenseBuilders, self).__init__()
        self.SHAKE_PATHS = [
            "landscape_linear"
        ]

    @staticmethod
    # pragma pylint: disable=unused-argument
    def nozzle_position(position_x=None, position_y=None, position_z=None):
        """
        Generates a validated nozzle_position parameter.

        Parameters
        ----------
        position_x : Unit, optional
        position_y : Unit, optional
        position_z : Unit, optional

        Returns
        -------
        dict
            Dictionary of nozzle position parameters
        """

        position_dict = {
            name: parse_unit(position, "mm")
            for name, position in locals().items() if position is not None
        }

        return position_dict
    # pragma pylint: enable=unused-argument

    @staticmethod
    def column(column, volume):
        """
        Generates a validated column parameter.

        Parameters
        ----------
        column : int
        volume : str, Unit

        Returns
        -------
        dict
            Column parameter of type {"column": int, "volume": Unit}

        """
        return {
            "column": int(column),
            "volume": parse_unit(volume, "uL")
        }

    def columns(self, columns):
        """
        Generates a validated columns parameter.

        Parameters
        ----------
        columns : list({"column": int, "volume": str, Unit})

        Returns
        -------
        list
            List of columns of type ({"column": int, "volume": str, Unit})

        Raises
        ------
        ValueError
            No `column` specified for columns
        ValueError
            Non-unique column indices
        """
        if not len(columns) > 0:
            raise ValueError(
                "There must be at least one column specified for columns.")

        column_list = [self.column(**_) for _ in columns]

        if len(column_list) != len(set([_["column"] for _ in column_list])):
            raise ValueError(
                "Column indices must be unique, but there were duplicates in "
                "{}.".format(column_list))

        return column_list

    def shake_after(self, duration, frequency=None, path=None, amplitude=None):
        """
        Generates a validated shake_after parameter.

        Parameters
        ----------
        duration : Unit, str
        frequency : Unit, str, optional
        path : str, optional
        amplitude : Unit, str, optional

        Returns
        -------
        dict
            Shake after dictionary of type {"duration": Unit,
            "frequency": Unit, "path": str, "amplitude": Unit}

        Raises
        ------
        ValueError
            Invalid shake path specified
        """

        if path and path not in self.SHAKE_PATHS:
            raise ValueError(
                "Invalid shake path {} specified, must be one of {}"
                "".format(path, self.SHAKE_PATHS)
            )

        shake_after = {
            "duration": parse_unit(duration, "seconds"),
            "frequency": parse_unit(frequency, "hertz") if frequency else None,
            "path": path,
            "amplitude": parse_unit(amplitude, "mm") if amplitude else None
        }

        return {k: v for k, v in shake_after.items() if v is not None}


class SpectrophotometryBuilders(InstructionBuilders):
    """
    These builders are meant for helping to construct arguments for the
    `Spectrophotometry` instruction.
    """
    def __init__(self):
        super(SpectrophotometryBuilders, self).__init__()
        self.MODES = {
            "absorbance": self.absorbance_mode_params,
            "fluorescence": self.fluorescence_mode_params,
            "luminescence": self.luminescence_mode_params,
            "shake": self.shake_mode_params
        }

        self.READ_POSITIONS = ["top", "bottom"]

        self.SHAKE_PATHS = [
            "portrait_linear", "landscape_linear",
            "cw_orbital", "ccw_orbital",
            "portrait_down_double_orbital", "landscape_down_double_orbital",
            "portrait_up_double_orbital", "landscape_up_double_orbital",
            "cw_diamond", "ccw_diamond"
        ]

    @staticmethod
    def wavelength_selection(shortpass=None, longpass=None, ideal=None):
        """
        Generates a representation of a wavelength selection by either
        filters (using shortpass/longpass) or monochromators (using ideal)

        Parameters
        ----------
        shortpass : Unit, str, optional
        longpass : Unit, str, optional
        ideal : Unit, str, optional

        Returns
        -------
        dict
            Wavelength selection parameters.
        """

        selection = {
            "shortpass":
                parse_unit(shortpass, "nanometer") if shortpass else None,
            "longpass":
                parse_unit(longpass, "nanometer") if longpass else None,
            "ideal":
                parse_unit(ideal, "nanometer") if ideal else None,
        }

        selection = {k: v for k, v in selection.items() if v is not None}

        return selection

    def groups(self, groups):
        """
        Parameters
        ----------
        groups : list(dict)
            A list of spectrophotometry groups.

        Returns
        -------
        list(dict)
            A list of spectrophotometry groups.
        """
        return [self.group(_["mode"], _["mode_params"]) for _ in groups]

    def group(self, mode, mode_params):
        """
        Parameters
        ----------
        mode : str
            A string representation of a valid spectrophotometry mode.
        mode_params : dict
            A dict of mode_params corresponding to the mode.

        Returns
        -------
        dict
            A spectrophotometry group.

        Raises
        ------
        ValueError
            Invalid mode specified
        """
        if mode not in self.MODES.keys():
            raise ValueError(
                "Invalid mode {}, must be in valid modes {}."
                "".format(mode, self.MODES.keys())
            )

        return {
            "mode": mode,
            "mode_params": self.MODES[mode](**mode_params)
        }

    @staticmethod
    def absorbance_mode_params(wells, wavelength, num_flashes=None,
                               settle_time=None):
        """
        Parameters
        ----------
        wells : iterable(Well) or WellGroup
            Wells to be read.
        wavelength : Unit or str
            The wavelengths at which to make absorbance measurements.
        num_flashes : int, optional
            The number of discrete reads to be taken and then averaged.
        settle_time : Unit or str, optional
            The time to wait between moving to a well and reading it.

        Returns
        -------
        dict
            Formatted mode_params for an absorbance mode.

        Raises
        ------
        TypeError
            Invalid type specified for input parameters, e.g. `num_flashes`
            not of type int
        ValueError
            Invalid wells specified
        """
        if not is_valid_well(wells):
            raise ValueError(
                "Invalid wells {}, must be an iterable of wells or a WellGroup."
                "".format(wells)
            )

        if isinstance(wells, Well):
            wells = WellGroup([wells])

        if not isinstance(wavelength, list):
            wavelength = [wavelength]

        wavelength = [
            parse_unit(_, "nanometer") for _ in wavelength
        ]

        if num_flashes is not None and not isinstance(num_flashes, int):
            raise TypeError(
                "Invalid num_flashes {}, must be an int".format(num_flashes)
            )

        if settle_time is not None:
            settle_time = parse_unit(settle_time, "second")

        mode_params = {
            "wells": wells,
            "wavelength": wavelength,
            "num_flashes": num_flashes,
            "settle_time": settle_time
        }

        mode_params = {k: v for k, v in mode_params.items() if v is not None}

        return mode_params

    def fluorescence_mode_params(self, wells, excitation, emission,
                                 num_flashes=None, settle_time=None,
                                 lag_time=None, integration_time=None,
                                 gain=None, read_position=None):
        """
        Parameters
        ----------
        wells : iterable(Well) or WellGroup
            Wells to be read.
        excitation : list(dict)
            A list of SpectrophotometryBuilders.wavelength_selection to
            determine the wavelegnth(s) of excitation light used.
        emission : list(dict)
            A list of SpectrophotometryBuilders.wavelength_selection to
            determine the wavelegnth(s) of emission light used.
        num_flashes : int, optional
            The number of discrete reads to be taken and then combined.
        settle_time : Unit or str, optional
            The time to wait between moving to a well and reading it.
        lag_time : Unit or str, optional
            The time to wait between excitation and reading.
        integration_time : Unit or str, optional
            Time over which the data should be collected and integrated.
        gain : int, optional
            The amount of gain to be applied to the readings.
        read_position : str, optional
            The position from which the wells should be read.

        Returns
        -------
        dict
            Formatted mode_params for a fluorescence mode.

        Raises
        ------
        TypeError
            Invalid input types, e.g. settle_time is not of type Unit(second)
        ValueError
            Invalid wells specified
        ValueError
            Gain is not between 0 and 1
        """
        if not is_valid_well(wells):
            raise ValueError(
                "Invalid wells {}, must be an iterable of wells or a WellGroup."
                "".format(wells)
            )

        if isinstance(wells, Well):
            wells = WellGroup([wells])

        if not isinstance(excitation, list):
            raise ValueError("Excitation {} must be a list")
        if not isinstance(emission, list):
            raise ValueError("Emission {} must be a list")

        excitation = [self.wavelength_selection(**_) for _ in excitation]
        emission = [self.wavelength_selection(**_) for _ in emission]

        if num_flashes is not None and not isinstance(num_flashes, int):
            raise ValueError(
                "Invalid num_flashes {}, must be an int".format(num_flashes)
            )

        if settle_time is not None:
            settle_time = parse_unit(settle_time, "second")

        if lag_time is not None:
            lag_time = parse_unit(lag_time, "second")

        if integration_time is not None:
            integration_time = parse_unit(integration_time, "second")

        if gain is not None:
            if not isinstance(gain, (int, float)):
                raise TypeError(
                    "Invalid gain {}, must be an int".format(gain)
                )
            gain = float(gain)
            if not 0 <= gain <= 1:
                raise ValueError(
                    "Invalid gain {}, must be between 0 and 1 (inclusive)."
                    "".format(gain)
                )

        if read_position is not None and read_position \
                not in self.READ_POSITIONS:
            raise ValueError(
                "Invalid read_position {}, must be in {}."
                "".format(read_position, self.READ_POSITIONS)
            )

        mode_params = {
            "wells": wells,
            "excitation": excitation,
            "emission": emission,
            "num_flashes": num_flashes,
            "settle_time": settle_time,
            "lag_time": lag_time,
            "integration_time": integration_time,
            "gain": gain,
            "read_position": read_position
        }

        mode_params = {k: v for k, v in mode_params.items() if v is not None}

        return mode_params

    @staticmethod
    def luminescence_mode_params(wells, num_flashes=None,
                                 settle_time=None, integration_time=None,
                                 gain=None):
        """
        Parameters
        ----------
        wells : iterable(Well) or WellGroup
            Wells to be read.
        num_flashes : int, optional
            The number of discrete reads to be taken and then combined.
        settle_time : Unit or str, optional
            The time to wait between moving to a well and reading it.
        integration_time : Unit or str, optional
            Time over which the data should be collected and integrated.
        gain : int, optional
            The amount of gain to be applied to the readings.

        Returns
        -------
        dict
            Formatted mode_params for a luminescence mode.

        Raises
        ------
        TypeError
            Invalid input types, e.g. settle_time is not of type Unit(second)
        ValueError
            Gain is not between 0 and 1

        """
        if not is_valid_well(wells):
            raise ValueError(
                "Invalid wells {}, must be an iterable of wells or a WellGroup."
                "".format(wells)
            )

        if isinstance(wells, Well):
            wells = WellGroup([wells])

        if num_flashes is not None and not isinstance(num_flashes, int):
            raise TypeError(
                "Invalid num_flashes {}, must be an int".format(num_flashes)
            )

        if settle_time is not None:
            settle_time = parse_unit(settle_time, "second")

        if integration_time is not None:
            integration_time = parse_unit(integration_time, "second")

        if gain is not None:
            if not isinstance(gain, (int, float)):
                raise TypeError(
                    "Invalid gain {}, must be an int".format(gain)
                )
            gain = float(gain)
            if not 0 <= gain <= 1:
                raise ValueError(
                    "Invalid gain {}, must be between 0 and 1 (inclusive)."
                    "".format(gain)
                )

        mode_params = {
            "wells": wells,
            "num_flashes": num_flashes,
            "settle_time": settle_time,
            "integration_time": integration_time,
            "gain": gain
        }

        mode_params = {k: v for k, v in mode_params.items() if v is not None}

        return mode_params

    def shake_mode_params(self, duration=None, frequency=None, path=None,
                          amplitude=None):
        """
        Parameters
        ----------
        duration : Unit or str, optional
            The duration of the shaking incubation, if not specified then the
            incubate will last until the end of read interval.
        frequency : Unit or str, optional
            The frequency of the shaking motion.
        path : str, optional
            The name of a shake path. See the spectrophotometry ASC for
            diagrams of different shake paths.
        amplitude : Unit or str, optional
            The amplitude of the shaking motion.

        Returns
        -------
        dict
            Formatted mode_params for a shake mode.
        """
        return self._shake(
            duration=duration,
            frequency=frequency,
            path=path,
            amplitude=amplitude
        )

    def shake_before(self, duration, frequency=None, path=None, amplitude=None):
        """
        Parameters
        ----------
        duration : Unit or str
            The duration of the shaking incubation.
        frequency : Unit or str, optional
            The frequency of the shaking motion.
        path : str, optional
            The name of a shake path. See the spectrophotometry ASC for
            diagrams of different shake paths.
        amplitude : Unit or str, optional
            The amplitude of the shaking motion.

        Returns
        -------
        dict
            Formatted mode_params for a shake mode.
        """
        duration = parse_unit(duration, "second")

        return self._shake(
            duration=duration,
            frequency=frequency,
            path=path,
            amplitude=amplitude
        )

    def _shake(self, duration=None, frequency=None, path=None, amplitude=None):
        """
        Helper method for validating shake params.
        """
        if duration is not None:
            duration = parse_unit(duration, "second")

        if frequency is not None:
            frequency = parse_unit(frequency, "hertz")

        if path and path not in self.SHAKE_PATHS:
            raise ValueError(
                "Invalid read_position {}, must be in {}."
                "".format(path, self.SHAKE_PATHS)
            )

        if amplitude is not None:
            amplitude = parse_unit(amplitude, "millimeter")

        params = {
            "duration": duration,
            "frequency": frequency,
            "path": path,
            "amplitude": amplitude
        }

        params = {k: v for k, v in params.items() if v is not None}

        return params


class LiquidHandleBuilders(InstructionBuilders):
    """Builders for LiquidHandle Instructions
    """
    def __init__(self):
        super(LiquidHandleBuilders, self).__init__()
        self.liquid_classes = ["air", "default"]
        self.xy_max = 1
        self.z_references = [
            "well_top", "well_bottom", "liquid_surface", "preceding_position"
        ]
        self.z_detection_methods = ["capacitance", "pressure", "tracked"]

    def location(self, location=None, transports=None):
        """Helper for building locations

        Parameters
        ----------
        location : Well or str, optional
            Location refers to the well location where the transports will be
            carried out
        transports : list(dict), optional
            Transports refer to the list of transports that will be carried out
            in the specified location
            See Also LiquidHandle.builders.transport

        Returns
        -------
        dict
            location parameters for a LiquidHandle instruction

        Raises
        ------
        TypeError
            If locations aren't str/well
        ValueError
            If transports are specified, but empty
        """
        if not (location is None or isinstance(location, (Well, str))):
            raise TypeError(
                "Location {} is not of type str or Well".format(location)
            )

        if transports is not None:
            if not isinstance(transports, Iterable):
                raise ValueError(
                    "Transports: {} is not iterable".format(transports)
                )
            transports = [self.transport(**_) for _ in transports]
            if len(transports) < 1:
                raise ValueError(
                    "transports {} must be nonempty if specified"
                    "".format(transports)
                )

        return {
            "location": location,
            "transports": transports
        }

    def transport(self, volume=None, pump_override_volume=None,
                  flowrate=None, delay_time=None, mode_params=None):
        """Helper for building transports

        Parameters
        ----------
        volume : Unit or str, optional
            Volume to be aspirated/dispensed. Positive volume -> Dispense.
            Negative -> Aspirate
        pump_override_volume : Unit or str, optional
            Calibrated volume, volume which the pump will move
        flowrate : dict, optional
            Flowrate parameters
            See Also LiquidHandle.builders.flowrate
        delay_time : Unit or str, optional
            Time spent waiting after executing mandrel and pump movement
        mode_params : dict, optional
            Mode parameters
            See Also LiquidHandle.builders.mode_params


        Returns
        -------
        dict
            transport parameters for a LiquidHandle instruction
        """
        if volume is not None:
            volume = parse_unit(volume, "ul")
        if pump_override_volume is not None:
            pump_override_volume = parse_unit(pump_override_volume, "ul")
        if flowrate is not None:
            flowrate = self.flowrate(**flowrate)
        if delay_time is not None:
            delay_time = parse_unit(delay_time, "s")
        if mode_params is not None:
            mode_params = self.mode_params(**mode_params)

        return {
            "volume": volume,
            "pump_override_volume": pump_override_volume,
            "flowrate": flowrate,
            "delay_time": delay_time,
            "mode_params": mode_params
        }

    @staticmethod
    def flowrate(target, initial=None, cutoff=None, acceleration=None,
                 deceleration=None):
        """Helper for building flowrates

        Parameters
        ----------
        target : Unit or str
            Target flowrate
        initial : Unit or str, optional
            Initial flowrate
        cutoff : Unit or str, optional
            Cutoff flowrate
        acceleration : Unit or str, optional
            Volumetric acceleration for initial to target (in ul/s^2)
        deceleration : Unit or str, optional
            Volumetric deceleration for target to cutoff (in ul/s^2)

        Returns
        -------
        dict
            flowrate parameters for a LiquidHandle instruction
        """
        target = parse_unit(target, "ul/s")
        if initial is not None:
            initial = parse_unit(initial, "ul/s")
        if cutoff is not None:
            cutoff = parse_unit(cutoff, "ul/s")
        if acceleration is not None:
            acceleration = parse_unit(acceleration, "ul/s/s")
        if deceleration is not None:
            deceleration = parse_unit(deceleration, "ul/s/s")

        return {
            "target": target,
            "initial": initial,
            "cutoff": cutoff,
            "acceleration": acceleration,
            "deceleration": deceleration
        }

    def mode_params(self, liquid_class=None, position_x=None, position_y=None,
                    position_z=None, tip_position=None):
        """Helper for building transport mode_params

        Mode params contain information about tip positioning and the
        liquid being manipulated

        Parameters
        ----------
        liquid_class : Enum({"default", "air"}), optional
            The name of the liquid class to be handled. This affects how
            vendors handle populating liquid handling defaults.
        position_x : dict, optional
            Target relative x-position of tip in well.
            See Also LiquidHandle.builders.position_xy
        position_y : dict, optional
            Target relative y-position of tip in well.
            See Also LiquidHandle.builders.position_xy
        position_z : dict, optional
            Target relative z-position of tip in well.
            See Also LiquidHandle.builders.position_z
        tip_position : dict, optional
            A dict of positions x, y, and z. Should only be specified if none of
            the other tip position parameters have been specified.

        Returns
        -------
        dict
            mode_params for a LiquidHandle instruction

        Raises
        ------
        ValueError
            If liquid_class is not in the allowed list
        ValueError
            If both position_x|y|z and tip_position are specified
        """
        if liquid_class is not None and liquid_class not in self.liquid_classes:
            raise ValueError(
                "liquid_class must be one of {} but {} was specified"
                "".format(self.liquid_classes, liquid_class)
            )

        xyz_specified = any(
            [_ is not None for _ in (position_x, position_y, position_z)]
        )

        if xyz_specified and tip_position is not None:
            raise ValueError(
                "tip_position {} was specified in addition to at least one "
                "of position_(x/y/z). Only one of the two methods of "
                "specifying tip position is allowed".format(tip_position)
            )

        if tip_position is not None:
            position_x = tip_position.get("position_x")
            position_y = tip_position.get("position_y")
            position_z = tip_position.get("position_z")

        if position_x is not None:
            position_x = self.position_xy(**position_x)
        if position_y is not None:
            position_y = self.position_xy(**position_y)
        if position_z is not None:
            position_z = self.position_z(**position_z)

        return {
            "liquid_class": liquid_class,
            "tip_position": {
                "position_x": position_x,
                "position_y": position_y,
                "position_z": position_z
            }
        }

    @staticmethod
    def move_rate(target=None, acceleration=None):
        """Helper for building move_rates

        Parameters
        ----------
        target : Unit or str, optional
            Target velocity. Must be in units of
        acceleration : Unit or str, optional
            Acceleration. Must be in units of

        Returns
        -------
        dict
            move_rate parameters for a LiquidHandle instruction
        """
        if target is not None:
            target = parse_unit(target, "mm/s")
        if acceleration is not None:
            acceleration = parse_unit(acceleration, "mm/s/s")

        return {
            "target": target,
            "acceleration": acceleration
        }

    def position_xy(self, position=None, move_rate=None):
        """Helper for building position_x and position_y parameters

        Parameters
        ----------
        position : Numeric, optional
            Target relative x/y-position of tip in well in unit square
            coordinates.
        move_rate : dict, optional
            The rate at which the tip moves in the well
            See Also LiquidHandle.builders.move_rate

        Returns
        -------
        dict
            position_xy parameters for a LiquidHandle instruction

        Raises
        ------
        TypeError
            If position is non-numeric
        ValueError
            If position is not in range
        """
        if not (position is None or isinstance(position, (float, int))):
            raise TypeError(
                "position {} is not of type float/int".format(position)
            )
        if not (position is None or -self.xy_max <= position <= self.xy_max):
            raise ValueError(
                "position {} was not in range {} - {}"
                "".format(position, -self.xy_max, self.xy_max)
            )

        if move_rate is not None:
            move_rate = self.move_rate(**move_rate)

        return {
            "position": position,
            "move_rate": move_rate
        }

    def position_z(self, reference=None, offset=None, move_rate=None,
                   detection_method=None, detection_threshold=None,
                   detection_duration=None, detection_fallback=None,
                   detection=None):
        """Helper for building position_z parameters

        Parameters
        ----------
        reference : str, optional
            Must be one of "well_top", "well_bottom", "liquid_surface",
             "preceding_position"
        offset : Unit or str, optional
            Offset from reference position
        move_rate : dict, optional
            Controls the rate at which the tip moves in the well
            See Also LiquidHandle.builders.move_rate
        detection_method : str, optional
            Must be one of "tracked", "pressure", "capacitance"
        detection_threshold : Unit or str, optional
            The threshold which must be crossed before a positive reading is
            registered. This is applicable for capacitance and pressure
            detection methods
        detection_duration : Unit or str, optional
            The contiguous duration where the threshold must be crossed before a
            positive reading is registered.
            This is applicable for pressure detection methods
        detection_fallback : dict, optional
            Fallback option which will be used if sensing fails
            See Also LiquidHandle.builders.position_z
        detection : dict, optional
            A dict of detection parameters. Should only be specified if none of
            the other detection parameters have been specified.

        Returns
        -------
        dict
            position_z parameters for a LiquidHandle instruction

        Raises
        ------
        ValueError
            If reference was not in the allowed list
        ValueError
            If both detection_method|duration|threshold|fallback and
            detection are specified
        ValueError
            If detection_method is not in the allowed list
        ValueError
            If detection parameters were specified, but the reference
            position doesn't support detection
        """
        if reference is not None and reference not in self.z_references:
            raise ValueError(
                "reference must be one of {} but {} was specified"
                "".format(self.z_references, reference)
            )
        if offset is not None:
            offset = parse_unit(offset, "mm")
        if move_rate is not None:
            move_rate = self.move_rate(**move_rate)

        detection_params_specified = any(
            [
                _ is not None for _
                in (detection_method, detection_duration,
                    detection_threshold, detection_fallback)
            ]
        )

        if detection_params_specified and detection is not None:
            raise ValueError(
                "tip_position {} was specified in addition to at least one "
                "of position_(x/y/z). Only one of the two methods of "
                "specifying tip position is allowed".format(detection)
            )

        if detection is not None:
            detection_method = detection.get("method")
            detection_duration = detection.get("duration")
            detection_threshold = detection.get("threshold")
            detection_fallback = detection.get("fallback")

        if (detection_method is not None and
                detection_method not in self.z_detection_methods):
            raise ValueError(
                "detection_method must be one of {} but {} was specified"
                "".format(self.z_detection_methods, detection_method)
            )

        if detection_duration is not None:
            detection_duration = parse_unit(detection_duration, "s")

        if detection_threshold is not None:
            detection_threshold = parse_unit(
                detection_threshold, ["pascal", "farad"]
            )

        if detection_fallback is not None:
            detection_fallback = self.position_z(**detection_fallback)

        detection_params = {
            "method": detection_method,
            "threshold": detection_threshold,
            "duration": detection_duration,
            "fallback": detection_fallback
        }

        # ensure that detection params are only allowed for surface references
        detection_specified = any(
            _ is not None
            for _ in detection_params.values()
        )
        detectable_reference = reference == "liquid_surface"
        if detection_specified and not detectable_reference:
            raise ValueError(
                "detection parameters were specified, but reference {} does "
                "not support detection".format(reference)
            )

        return {
            "reference": reference,
            "offset": offset,
            "move_rate": move_rate,
            "detection": detection_params
        }

    @staticmethod
    def instruction_mode_params(tip_type=None):
        """Helper for building instruction mode_params

        Parameters
        ----------
        tip_type : str, optional
            the string representation ofa tip_type
            See Also tip_type.py

        Returns
        -------
        dict
            mode_params for a LiquidHandle instruction
        """

        return {
            "tip_type": tip_type
        }

    def mix(self, volume, repetitions, initial_z,
            asp_flowrate=None, dsp_flowrate=None):
        """Helper for building mix params for Transfer LiquidHandleMethods

        Parameters
        ----------
        volume : Unit or str
            the volume of the mix step
        repetitions : int
            the number of times that the mix should be repeated
        initial_z : dict
            the position that the tip should move to prior to mixing
            See Also LiquidHandle.builders.position_z
        asp_flowrate : dict, optional
            the flowrate of the aspiration portions of the mix
            See Also LiquidHandle.builders.flowrate
        dsp_flowrate : dict, optional
            the flowrate of the dispense portions of the mix
            See Also LiquidHandle.builders.flowrate

        Returns
        -------
        dict
            mix parameters for a LiquidHandleMethod

        Raises
        ------
        TypeError
            If repetitions is not an int
        """
        volume = parse_unit(volume, "ul")
        if not isinstance(repetitions, int):
            raise TypeError("repetitions {} is not an int".format(repetitions))
        initial_z = self.position_z(**initial_z)
        if asp_flowrate is not None:
            asp_flowrate = self.flowrate(**asp_flowrate)
        if dsp_flowrate is not None:
            dsp_flowrate = self.flowrate(**dsp_flowrate)

        return {
            "volume": volume,
            "repetitions": repetitions,
            "initial_z": initial_z,
            "asp_flowrate": asp_flowrate,
            "dsp_flowrate": dsp_flowrate
        }

    def blowout(self, volume, initial_z, flowrate=None):
        """Helper for building blowout params for LiquidHandleMethods

        Parameters
        ----------
        volume : Unit or str
            the volume of the blowout step
        initial_z : dict
            the position that the tip should move to prior to blowing out
            See Also LiquidHandle.builders.position_z
        flowrate : dict, optional
            the flowrate of the blowout
            See Also LiquidHandle.builders.flowrate

        Returns
        -------
        dict
            blowout params for a LiquidHandleMethod
        """
        volume = parse_unit(volume, "ul")
        initial_z = self.position_z(**initial_z)
        if flowrate is not None:
            flowrate = self.flowrate(**flowrate)

        return {
            "volume": volume,
            "initial_z": initial_z,
            "flowrate": flowrate
        }


class FlowCytometryBuilders(InstructionBuilders):
    """
    Builders for FlowCytometry instructions.

    """
    def __init__(self):
        super(FlowCytometryBuilders, self).__init__()

    def laser(self, excitation, channels, power=None, area_scaling_factor=None):
        """
        Generates a dict of laser parameters.

        Parameters
        ----------
        excitation : Unit or str
            Excitation wavelength.
        channels : list(dict)
            See FlowCytometryBuilders.channel.
        power : Unit or str, optional
            Laser power.
        area_scaling_factor : Number, optional
            Value to scale height and area equivalently.

        Raises
        ------
        TypeError
            If channels is not a list of dict.
        TypeError
            If channels is not a list of dict.
        TypeError
            If area_scaling_factor is not a number.

        Returns
        -------
        dict
            A dict of laser parameters.
        """
        if not isinstance(channels, list):
            raise TypeError("channels must be a list of dict.")

        if any([not isinstance(_, dict) for _ in channels]):
            raise TypeError("channels must be a list of dict.")

        if area_scaling_factor is not None and not isinstance(
                area_scaling_factor, Number):
            raise TypeError("area_scaling_factor must be a number.")

        if power is not None:
            power = parse_unit(power, "milliwatts")

        excitation = parse_unit(excitation, "nanometers")
        channels = [self.channel(**_) for _ in channels]

        return {
            "excitation": excitation,
            "power": power,
            "area_scaling_factor": area_scaling_factor,
            "channels": channels,
        }

    def channel(self, emission_filter, detector_gain, measurements=None,
                trigger_threshold=None, trigger_logic="and"):
        """
        Generates a dict of channel parameters.

        Parameters
        ----------
        emission_filter : dict
            See FlowCytometryBuilders.emission_filter.
        detector_gain : Unit or str
            Detector gain.
        measurements : dict, optional
            Pulse properties to record. See FlowCytometryBuilders.measurements.
        trigger_threshold : int, optional
            Channel intensity threshold. Events below this threshold.
        trigger_logic : Enum(str), optional
            Operator used to combine threshold. One of {"and", "or"}.
            Defaults to "and".

        Raises
        ------
        TypeError
            If trigger_threshold is not of type int.
        ValueError
            If trigger_logic is not one of {"and", "or"}.

        Returns
        -------
        dict
            A dict of channel parameters.
        """
        if trigger_threshold is not None and not isinstance(
                trigger_threshold, int):
            raise TypeError("trigger_threshold must be of type int.")

        trigger_modes = ("and", "or")
        if trigger_logic is not None and trigger_logic not in trigger_modes:
            raise ValueError("trigger_logic must be one of {}."
                             .format(trigger_modes))

        if measurements is None:
            measurements = self.measurements()
        else:
            measurements = self.measurements(**measurements)

        emission_filter = self.emission_filter(**emission_filter)
        detector_gain = parse_unit(detector_gain, "millivolts")

        return {
            "emission_filter": emission_filter,
            "detector_gain": detector_gain,
            "measurements": measurements,
            "trigger_threshold": trigger_threshold,
            "trigger_logic": trigger_logic
        }

    def emission_filter(self, channel_name, shortpass=None, longpass=None):
        """
        Generates a dict of emission_filter parameters.

        Parameters
        ----------
        channel_name : str
            Specifies the channel name.
        shortpass : Unit or str
            Shortpass filter wavelength.
        longpass : Unit or str
            Longpass filter wavelength.

        Raises
        ------
        ValueError
            If values for longpass or shortpass are provided and
            channel_name is "FSC" or "SSC".

        Returns
        -------
        dict
            A dict of emission_filter params.
        """
        gating_modes = ("FSC", "SSC")
        if channel_name in gating_modes and shortpass or longpass:
            raise ValueError("Cannot specify shortpass/longpass parameters if"
                             "if channel_name is one {}"
                             .format(gating_modes))

        return {
            "channel_name": channel_name,
            "shortpass": shortpass,
            "longpass": longpass
        }

    @staticmethod
    def measurements(area=True, height=True, width=True):
        """
        Generates a dict of measurements parameters.

        Parameters
        ----------
        area : bool, optional
            Area measurement. Default true.
        height : bool, optional
            Height measurement. Default true.
        width : bool, optional
            Width measurement. Default true.

        Raises
        ------
        ValueError
            If any of `area` | `height` | `width` are not of type bool.

        Returns
        -------
        dict
            A dict of measurements params.
        """
        if any([not isinstance(_, bool) for _ in [area, height, width]]):
            raise TypeError("area, height, and width must be of type bool.")

        return {
            "area": area,
            "height": height,
            "width": width
        }

    def collection_conditions(self, acquisition_volume, flowrate, wait_time,
                              mix_cycles, mix_volume, rinse_cycles,
                              stop_criteria=None):
        """
        Generates a dict of collection_conditions parameters.

        Parameters
        ----------
        acquisition_volume : Unit or str
            Acquisition volume.
        flowrate : Unit or str
            Flowrate.
        wait_time : Unit or str
            Waiting time.
        mix_cycles : int
            Number of mixing cycles before acquisition.
        mix_volume : Unit or str
            Mixing volume.
        rinse_cycles : int
            Number of rinsing cycles.
        stop_criteria : dict
            See FlowCytometryBuilders.stop_criteria.

        Raises
        ------
        TypeError
            If `rinse_cycles` is not of type int.
        TypeError
            If `mix_cycles` is not of type int.

        Returns
        -------
        dict
            A dict of collection_condition parameters.
        """
        if rinse_cycles is not None and not isinstance(rinse_cycles, int):
            raise TypeError("rinse_cycles must be of type int.")

        if mix_cycles is not None and not isinstance(mix_cycles, int):
            raise TypeError("mix_cycles must be of type int.")

        acquisition_volume = parse_unit(acquisition_volume, "ul")
        wait_time = parse_unit(wait_time, "s")
        mix_volume = parse_unit(mix_volume, "ul")
        flowrate = parse_unit(flowrate, "ul/min")

        if stop_criteria is None:
            stop_criteria = self.stop_criteria(volume=acquisition_volume)
        else:
            stop_criteria = self.stop_criteria(**stop_criteria)

        return {
            "acquisition_volume": acquisition_volume,
            "flowrate": flowrate,
            "stop_criteria": stop_criteria,
            "wait_time": wait_time,
            "mix_cycles": mix_cycles,
            "mix_volume": mix_volume,
            "rinse_cycles": rinse_cycles
        }

    @staticmethod
    def stop_criteria(volume=None, events=None, time=None):
        """
        Generates a dict of stop_criteria parameters.

        Parameters
        ----------
        volume : Unit or str, optional
            Stopping volume.
        events : int, optional
            Number of events to trigger stop.
        time
            Stopping time.

        Raises
        ------
        TypeError
            If `events` is not of type int.

        Returns
        -------
        dict
            A dict of stop_criteria params.
        """
        if events is not None and not isinstance(events, int):
            raise TypeError("events must be of type int.")

        if volume is not None:
            volume = parse_unit(volume, "ul")

        if time is not None:
            time = parse_unit(time, "s")

        return {
            "volume": volume,
            "events": events,
            "time": time
        }
