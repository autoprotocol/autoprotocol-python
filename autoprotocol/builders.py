"""Builders
Module containing builders, which help build inputs for Instruction parameters

    :copyright: 2021 by The Autoprotocol Development Team, see AUTHORS
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

from collections import defaultdict
from collections.abc import Iterable  # pylint: disable=no-name-in-module
from functools import reduce
from numbers import Number

from .constants import SBS_FORMAT_SHAPES
from .container import Container, Well, WellGroup
from .unit import Unit
from .util import is_valid_well, parse_unit


class InstructionBuilders(object):  # pylint: disable=too-few-public-methods
    """General builders that apply to multiple instructions"""

    def __init__(self):
        self.sbs_shapes = ["SBS96", "SBS384"]

    @staticmethod
    def _merge_param_dicts(left=None, right=None):
        """Finds the union of two dicts of params and checks for duplicates

        Parameters
        ----------
        left : dict or None
            Parameters to be merged
        right : dict or None
            Parameters to be merged

        Returns
        -------
        dict
            A merged set of parameters from the left and right dicts

        Raises
        ------
        ValueError
            if multiple values are specified for the same parameter

        """
        left = left or dict()
        right = right or dict()

        union = defaultdict(list)
        for params in (left, right):
            for key, value in params.items():
                if value is not None:
                    union[key].append(value)

        unique = dict()
        for key, value in union.items():
            if len(value) == 1:
                unique[key] = value[0]
            else:
                raise ValueError(
                    f"Parameter: {key} had multiple values: {value} specified."
                )

        return unique

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
                raise ValueError("Invalid number of rows and/or columns specified")

        if format not in self.sbs_shapes:
            raise ValueError(
                f"Invalid shape format; format has to be in {self.sbs_shapes}"
            )

        valid_rows = rows <= SBS_FORMAT_SHAPES[format]["rows"]
        valid_columns = columns <= SBS_FORMAT_SHAPES[format]["columns"]
        if not (valid_rows and valid_columns):
            raise ValueError(
                f"rows: {rows} and columns: {columns} are not possible with "
                f"format: {format}."
            )

        return {"rows": rows, "columns": columns, "format": format}


class ThermocycleBuilders(InstructionBuilders):
    """
    These builders are meant for helping to construct the `groups`
    argument in the `Protocol.thermocycle` method
    """

    def __init__(self):
        super(ThermocycleBuilders, self).__init__()
        self.valid_dyes = {
            "FAM",
            "SYBR",  # channel 1
            "VIC",
            "HEX",
            "TET",
            "CALGOLD540",  # channel 2
            "ROX",
            "TXR",
            "CALRED610",  # channel 3
            "CY5",
            "QUASAR670",  # channel 4
            "QUASAR705",  # channel 5
            "FRET",  # channel 6
        }

    def dyes(self, **kwargs):
        """Helper function for creating a dye parameter

        Parameters
        ----------
        **kwargs : dict(str: int or list(int))
            A mapping from a dye (str) to the index of a well

        Returns
        -------
        dict
            A thermocycling dye to well mapping

        Raises
        ------
        ValueError
            If any of the specified dyes are not valid
        ValueError
            If wells is not an int, str, list(int), or list(str)
        """
        dyes = {}
        for dye, wells in kwargs.items():
            if dye not in self.valid_dyes:
                raise ValueError(
                    f"dye {dye} is not in the set of valid dyes " f"{self.valid_dyes}"
                )
            if not isinstance(wells, list):
                wells = [wells]
            if not all(isinstance(_, (int, str)) for _ in wells):
                raise ValueError(
                    f"dye {dye} had wells {wells} that were not an int, str " "or list"
                )
            dyes[dye] = wells

        return dyes

    def dyes_from_well_map(self, well_map):
        """Helper function for creating a dye parameter from a well_map

        Take a map of wells to the dyes it contains and returns a map of dyes to
        the list of wells that contain it.

        Parameters
        ----------
        well_map : dict(well, str)
            A thermocycling well to dye mapping

        Returns
        -------
        dict
            A thermocycling dye to well mapping

        See Also
        --------
        Thermocycle.Builders.dyes : standard constructor for the dyes parameter

        """
        dyes = reduce(lambda x, y: x.union(y), [set(well_map[k]) for k in well_map])

        dye_map = {dye: [] for dye in dyes}
        for well in well_map:
            dyes = well_map[well]
            for dye in dyes:
                dye_map[dye] += [well]

        return self.dyes(**dyes)

    @staticmethod
    def melting(start=None, end=None, increment=None, rate=None):
        """Helper function for creating melting parameters

        Generates melt curve parameters for Thermocycle Instructions.

        Parameters
        ----------
        start : str or Unit
            The starting temperature for the melt curve
        end : str or Unit
            The ending temperature for the melt curve
        increment : str or Unit
            The temperature increment of the melt curve
        rate : str or Unit
            The duration the individual increments

        Returns
        -------
        dict
            A thermocycling melt curve specification

        Raises
        ------
        ValueError
            If some, but not all melt curve parameters are specified

        """
        melting_params = [start, end, increment, rate]

        if any(melting_params) and not all(melting_params):
            raise ValueError(
                "To specify a melt curve, you must specify values for "
                "start, end, increment, and rate"
            )

        if start:
            start = parse_unit(start, "celsius")
        if end:
            end = parse_unit(end, "celsius")
        if increment:
            increment = parse_unit(increment, "celsius")
        if rate:
            rate = parse_unit(rate, "second")

        return {"start": start, "end": end, "increment": increment, "rate": rate}

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
            raise TypeError(f"`cycles` {cycles} has to be of type int")
        if not isinstance(steps, list):
            raise TypeError(f"`steps` {steps} has to be of type list")

        if cycles <= 0:
            raise ValueError(f"`cycles` {cycles} has to be positive")
        if not steps:
            raise ValueError("`steps` has to contain at least one element")

        # Reformatting to use temperature for gradient input
        def reformat_gradient(**kwargs):
            if "gradient" in kwargs:
                kwargs["temperature"] = kwargs.pop("gradient")
            return kwargs

        group_dict = dict(
            cycles=cycles, steps=[self.step(**reformat_gradient(**_)) for _ in steps]
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
            if set(temperature.keys()) != {"top", "bottom"}:
                raise ValueError(
                    f"{temperature} was specified, but only 'top' and 'bottom' "
                    f"keys are allowed for a temperature dictionary"
                )
            step_dict["gradient"] = dict(
                top=parse_unit(temperature["top"], "celsius"),
                bottom=parse_unit(temperature["bottom"], "celsius"),
            )
        else:
            step_dict["temperature"] = parse_unit(temperature, "celsius")

        duration = parse_unit(duration, "second")
        if duration <= Unit("0:second"):
            raise ValueError("Step `duration` has to be at least 1 second")
        step_dict["duration"] = duration

        if read is not None:
            if not isinstance(read, bool):
                raise TypeError(f"`read` {read} has to be of type bool")
            step_dict["read"] = read

        return step_dict


class SPEBuilders(InstructionBuilders):
    """
    These builders are meant for helping to construct arguments for the
    `SPE` instruction.
    """

    def spe_params(self, params, is_elute=False):
        if not isinstance(params, list):
            raise ValueError("SPE mobile phase parameters {} must be a list.")
        parsed_params = []
        for param in params:
            parsed_params.append(self.mobile_phase_params(is_elute=is_elute, **param))
        return parsed_params

    def mobile_phase_params(
        self,
        volume,
        loading_flowrate,
        settle_time,
        processing_time,
        flow_pressure,
        resource_id=None,
        is_sample=False,
        destination_well=None,
        is_elute=False,
    ):
        """
        Create a dictionary with mobile phase parameters which can be
        used as input for instructions.

        Parameters
        ----------
        volume: str or Unit
            the duration to shake the plate for
        loading_flowrate: str or Unit, optional
            amplitude of shaking between 1 and 6:millimeter
        settle_time: bool, optional
            True for orbital and False for linear shaking
        processing_time: str or Unit
            Duration for which pressure is applied to the cartridge
            after `settle_time` has elapsed.
        flow_pressure: str or Unit
            Pressure applied to the column.
        resource_id: str
            Resource ID of desired solvent.
        is_sample: bool
            If a sample is processed.
        destination_well: Well
            Destination well for eluate.  Required parameter for
            each `elute` mobile phase parameter
        is_elute: bool
            If an elute is processed.

        Returns
        -------
        dict
            spe mobile_phase_params

        Raises
        ------
        ValueError
            if shake `flow_pressure` is not positive
        ValueError
            if mobile phase solvent and resource_id not included
        TypeError
            if `resource_id` is not a string
        ValueError
            if `settle_time` is not positive
        ValueError
            if `processing_time` is not positive

        """
        volume = parse_unit(volume, "milliliter")
        settle_time = parse_unit(settle_time, "second")
        if settle_time <= Unit(0, "second"):
            raise ValueError(f"settle_time: {settle_time} is not positive")

        processing_time = parse_unit(processing_time, "second")
        if processing_time <= Unit(0, "second"):
            raise ValueError(f"processing_time: {processing_time} is not " "positive")

        flow_pressure = parse_unit(flow_pressure, "bar")
        if flow_pressure <= Unit(0, "bar"):
            raise ValueError(f"flow_pressure: {flow_pressure} must be " f"positive.")
        loading_flowrate = parse_unit(loading_flowrate, "ul/s")

        if not is_sample:
            if not resource_id:
                raise ValueError(
                    "A 'resource_id' must be included " "for mobile_phase_params."
                )
            if not isinstance(resource_id, str):
                raise TypeError("'resource_id' {} must be a string")
        if is_elute:
            if not destination_well:
                raise ValueError(
                    "A 'destination_well' must be included " "for elute parameter."
                )
            if not isinstance(destination_well, Well):
                raise TypeError("'destination_well' {} must be of type Well")

        mode_params = {
            "volume": volume,
            "settle_time": settle_time,
            "processing_time": processing_time,
            "flow_pressure": flow_pressure,
            "loading_flowrate": loading_flowrate,
            "resource_id": resource_id,
            "destination_well": destination_well,
        }

        mode_params = {k: v for k, v in mode_params.items() if v is not None}

        return mode_params


class DispenseBuilders(InstructionBuilders):
    """
    These builders are meant for helping to construct arguments in the
    `Protocol.dispense` method.
    """

    def __init__(self):
        super(DispenseBuilders, self).__init__()
        self.SHAKE_PATHS = ["landscape_linear"]

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
            for name, position in locals().items()
            if position is not None
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
        return {"column": int(column), "volume": parse_unit(volume, "uL")}

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
            raise ValueError("There must be at least one column specified for columns.")

        column_list = [self.column(**_) for _ in columns]

        if len(column_list) != len(set([_["column"] for _ in column_list])):
            raise ValueError(
                f"Column indices must be unique, but there were duplicates "
                f"in {column_list}."
            )

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
                f"Invalid shake path {path} specified, must be one of "
                f"{self.SHAKE_PATHS}"
            )

        shake_after = {
            "duration": parse_unit(duration, "seconds"),
            "frequency": parse_unit(frequency, "hertz") if frequency else None,
            "path": path,
            "amplitude": parse_unit(amplitude, "mm") if amplitude else None,
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
            "shake": self.shake_mode_params,
        }

        self.READ_POSITIONS = ["top", "bottom"]

        self.SHAKE_PATHS = [
            "portrait_linear",
            "landscape_linear",
            "cw_orbital",
            "ccw_orbital",
            "portrait_down_double_orbital",
            "landscape_down_double_orbital",
            "portrait_up_double_orbital",
            "landscape_up_double_orbital",
            "cw_diamond",
            "ccw_diamond",
        ]

        self.Z_REFERENCES = ["plate_bottom", "plate_top", "well_bottom", "well_top"]

        self.Z_HEURISTICS = [
            "max_mean_read_without_saturation",
            "closest_distance_without_saturation",
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
            "shortpass": parse_unit(shortpass, "nanometer") if shortpass else None,
            "longpass": parse_unit(longpass, "nanometer") if longpass else None,
            "ideal": parse_unit(ideal, "nanometer") if ideal else None,
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
                f"Invalid mode {mode}, must be in valid modes " f"{self.MODES.keys()}."
            )

        return {"mode": mode, "mode_params": self.MODES[mode](**mode_params)}

    def absorbance_mode_params(
        self,
        wells,
        wavelength,
        num_flashes=None,
        settle_time=None,
        read_position=None,
        position_z=None,
    ):
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
        read_position: Enum("top", "bottom"), optional
            The position of the probe relative to the plate for the read
        position_z: dict, optional
            This should be specified with either `position_z_manual` or
            `position_z_calculated`

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
                f"Invalid wells {wells}, must be an iterable of wells or a "
                f"WellGroup."
            )

        if isinstance(wells, Well):
            wells = WellGroup([wells])

        if not isinstance(wavelength, list):
            wavelength = [wavelength]

        wavelength = [parse_unit(_, "nanometer") for _ in wavelength]

        if num_flashes is not None and not isinstance(num_flashes, int):
            raise TypeError(f"Invalid num_flashes {num_flashes}, must be an int")

        if settle_time is not None:
            settle_time = parse_unit(settle_time, "second")

        if read_position is not None and read_position not in self.READ_POSITIONS:
            raise ValueError(
                f"Invalid read_position {read_position}, must be in "
                f"{self.READ_POSITIONS}."
            )

        if position_z is not None:
            position_z = self._position_z(position_z)

        mode_params = {
            "wells": wells,
            "wavelength": wavelength,
            "num_flashes": num_flashes,
            "settle_time": settle_time,
            "read_position": read_position,
            "position_z": position_z,
        }

        mode_params = {k: v for k, v in mode_params.items() if v is not None}

        return mode_params

    def fluorescence_mode_params(
        self,
        wells,
        excitation,
        emission,
        num_flashes=None,
        settle_time=None,
        lag_time=None,
        integration_time=None,
        gain=None,
        read_position=None,
        position_z=None,
    ):
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
        position_z: dict, optional
            This should be specified with either `position_z_manual` or
            `position_z_calculated`

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
                f"Invalid wells {wells}, must be an iterable of wells or a "
                f"WellGroup."
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
            raise ValueError(f"Invalid num_flashes {num_flashes}, must be an int")

        if settle_time is not None:
            settle_time = parse_unit(settle_time, "second")

        if lag_time is not None:
            lag_time = parse_unit(lag_time, "second")

        if integration_time is not None:
            integration_time = parse_unit(integration_time, "second")

        if gain is not None:
            if not isinstance(gain, (int, float)):
                raise TypeError(f"Invalid gain {gain}, must be an int")
            gain = float(gain)
            if not 0 <= gain <= 1:
                raise ValueError(
                    f"Invalid gain {gain}, must be between 0 and 1 (inclusive)."
                )

        if read_position is not None and read_position not in self.READ_POSITIONS:
            raise ValueError(
                f"Invalid read_position {read_position}, must be in "
                f"{self.READ_POSITIONS}."
            )

        if position_z is not None:
            position_z = self._position_z(position_z)

        mode_params = {
            "wells": wells,
            "excitation": excitation,
            "emission": emission,
            "num_flashes": num_flashes,
            "settle_time": settle_time,
            "lag_time": lag_time,
            "integration_time": integration_time,
            "gain": gain,
            "read_position": read_position,
            "position_z": position_z,
        }

        mode_params = {k: v for k, v in mode_params.items() if v is not None}

        return mode_params

    def luminescence_mode_params(
        self,
        wells,
        num_flashes=None,
        settle_time=None,
        integration_time=None,
        gain=None,
        read_position=None,
        position_z=None,
    ):
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
        read_position: Enum("top", "bottom"), optional
            The position of the probe relative to the plate for the read
        position_z: dict, optional
            This should be specified with either `position_z_manual` or
            `position_z_calculated`

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
                f"Invalid wells {wells}, must be an iterable of wells or a "
                f"WellGroup."
            )

        if isinstance(wells, Well):
            wells = WellGroup([wells])

        if num_flashes is not None and not isinstance(num_flashes, int):
            raise TypeError(f"Invalid num_flashes {num_flashes}, must be an int")

        if settle_time is not None:
            settle_time = parse_unit(settle_time, "second")

        if integration_time is not None:
            integration_time = parse_unit(integration_time, "second")

        if gain is not None:
            if not isinstance(gain, (int, float)):
                raise TypeError(f"Invalid gain {gain}, must be an int")
            gain = float(gain)
            if not 0 <= gain <= 1:
                raise ValueError(
                    f"Invalid gain {gain}, must be between 0 and 1 (inclusive)."
                )

        if read_position is not None and read_position not in self.READ_POSITIONS:
            raise ValueError(
                f"Invalid read_position {read_position}, must be in "
                f"{self.READ_POSITIONS}."
            )

        if position_z is not None:
            position_z = self._position_z(position_z)

        mode_params = {
            "wells": wells,
            "num_flashes": num_flashes,
            "settle_time": settle_time,
            "integration_time": integration_time,
            "gain": gain,
            "read_position": read_position,
            "position_z": position_z,
        }

        mode_params = {k: v for k, v in mode_params.items() if v is not None}

        return mode_params

    def shake_mode_params(
        self, duration=None, frequency=None, path=None, amplitude=None
    ):
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
            duration=duration, frequency=frequency, path=path, amplitude=amplitude
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
            duration=duration, frequency=frequency, path=path, amplitude=amplitude
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
                f"Invalid read_position {path}, must be in {self.SHAKE_PATHS}."
            )

        if amplitude is not None:
            amplitude = parse_unit(amplitude, "millimeter")

        params = {
            "duration": duration,
            "frequency": frequency,
            "path": path,
            "amplitude": amplitude,
        }

        params = {k: v for k, v in params.items() if v is not None}

        return params

    def position_z_manual(self, reference=None, displacement=None):
        """Helper for building position_z parameters for a manual position_z
        configuration

        Parameters
        ----------
        reference : str, optional
            Must be one of "plate_top", "plate_bottom", "well_top",
            "well_bottom"
        displacement: Unit or str, optional
            Displacement from reference position.
            Negative would refer to the `well_top` to `well_bottom` direction,
            while positive would refer to the opposite direction.

        Returns
        -------
        dict
            position_z parameters for a Spectrophotometry instruction

        Raises
        ------
        ValueError
            If reference was not in the allowed list
        ValueError
            If invalid displacement was provided
        """
        if reference is not None and reference not in self.Z_REFERENCES:
            raise ValueError(
                f"reference must be one of {self.Z_REFERENCES} but {reference} "
                f"was specified"
            )
        if displacement is not None:
            displacement = parse_unit(displacement, "mm")

        return {"manual": {"reference": reference, "displacement": displacement}}

    def position_z_calculated(self, wells, heuristic=None):
        """Helper for building position_z parameters for a calculated
        position_z configuration

        Parameters
        ----------
        wells : list(Well)
            List of wells to calculate the z-position from
        heuristic: str, optional
            Must be one of "max_mean_read_without_saturation" or
            "closest_distance_without_saturation".
            Please refer to `ASC-041 <http://autoprotocol.org/ascs/#ASC-040>`_
            for the full explanation

        Returns
        -------
        dict
            position_z parameters for a Spectrophotometry instruction

        Raises
        ------
        ValueError
            If a list of wells is not provided
        ValueError
            If an invalid heuristic is specified

        """
        if any([not is_valid_well(well) for well in wells]):
            raise ValueError("Only an iterable of wells is allowed")

        if heuristic is not None and heuristic not in self.Z_HEURISTICS:
            raise ValueError(
                f"heuristic must be one of {self.Z_HEURISTICS} but {heuristic} "
                f"was specified"
            )

        return {"calculated_from_wells": {"wells": wells, "heuristic": heuristic}}

    def _position_z(self, position_z):
        """
        Helper method for validating position_z params
        """
        suggested_msg = (
            "Please use either `position_z_manual` or "
            "`position_z_calculated` functions to construct "
            "the appropriate z-position."
        )

        if not isinstance(position_z, dict):
            raise TypeError(
                f"Invalid position_z {position_z}, must be a dict. " f"{suggested_msg}"
            )

        if "calculated_from_wells" in position_z:
            return self.position_z_calculated(**position_z["calculated_from_wells"])
        elif "manual" in position_z:
            return self.position_z_manual(**position_z["manual"])
        else:
            raise ValueError(
                f"Invalid position_z {position_z} specified. {suggested_msg}"
            )


class LiquidHandleBuilders(InstructionBuilders):
    """Builders for LiquidHandle Instructions"""

    def __init__(self):
        super(LiquidHandleBuilders, self).__init__()
        self.liquid_classes = ["air", "default", "viscous", "protein_buffer"]
        self.xy_max = 1
        self.z_references = [
            "well_top",
            "well_bottom",
            "liquid_surface",
            "preceding_position",
        ]
        self.z_detection_methods = ["capacitance", "pressure", "tracked"]
        self.dispense_modes = ["air_displacement", "positive_displacement"]

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
            raise TypeError(f"Location {location} is not of type str or Well")

        if transports is not None:
            if not isinstance(transports, Iterable):
                raise ValueError(f"Transports: {transports} is not iterable")
            transports = [self.transport(**_) for _ in transports]
            if len(transports) < 1:
                raise ValueError(
                    f"transports {transports} must be nonempty if specified"
                )

        return {"location": location, "transports": transports}

    def transport(
        self,
        volume=None,
        pump_override_volume=None,
        flowrate=None,
        delay_time=None,
        mode_params=None,
        density=None,
    ):
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
        density : Unit or str, optional
            Density of the liquid to be aspirated/dispensed in mg/ml.


        Returns
        -------
        dict
            transport parameters for a LiquidHandle instruction
        """
        if volume is not None:
            volume = parse_unit(volume, "ul")
        if density is not None:
            density = parse_unit(density, "mg/ml")
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
            "density": density,
            "pump_override_volume": pump_override_volume,
            "flowrate": flowrate,
            "delay_time": delay_time,
            "mode_params": mode_params,
        }

    @staticmethod
    def flowrate(
        target, initial=None, cutoff=None, acceleration=None, deceleration=None
    ):
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
            "deceleration": deceleration,
        }

    def mode_params(
        self,
        liquid_class=None,
        position_x=None,
        position_y=None,
        position_z=None,
        tip_position=None,
        volume_resolution=None,
    ):
        """Helper for building transport mode_params

        Mode params contain information about tip positioning and the
        liquid being manipulated

        Parameters
        ----------
        liquid_class : str, optional
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
        volume_resolution : Unit, optional
            LiquidHandle dispense mode volume resolution specifies the droplet size to dispense.
            A specified resolution will exclude machines that are not configured for the given droplet size.
            By default, None means any droplet size will suffice. Check default droplet size on your machine configuration.


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
                f"liquid_class must be one of {self.liquid_classes} but "
                f"{liquid_class} was specified"
            )

        tip_position = self._merge_param_dicts(
            dict(position_x=position_x, position_y=position_y, position_z=position_z),
            tip_position,
        )
        position_x = tip_position.get("position_x")
        position_y = tip_position.get("position_y")
        position_z = tip_position.get("position_z")

        if position_x is not None:
            position_x = self.position_xy(**position_x)

        if position_y is not None:
            position_y = self.position_xy(**position_y)

        if position_z is not None:
            position_z = self.position_z(**position_z)

        if volume_resolution is not None:
            volume_resolution = parse_unit(volume_resolution, "uL")

        return {
            "liquid_class": liquid_class,
            "tip_position": {
                "position_x": position_x,
                "position_y": position_y,
                "position_z": position_z,
            },
            "volume_resolution": volume_resolution,
        }

    @staticmethod
    def device_mode_params(
        model=None,
        chip_material=None,
        nozzle=None,
    ):
        """Helper for building device level mode_params

        Mode params contain information about desired device hardware to
        be used

        Parameters
        ----------
        model : string, optional
            Tempest chip model.
        chip_material : string, optional
            Material that the tempest chip is made of.
        nozzle : string, optional
            Type of chip nozzle.

        Returns
        -------
        dict
            device_mode_params for a LiquidHandle instruction

        Raises
        ------
        ValueError
            If model is not None or "high_volume"
        ValueError
            If nozzle is not None or "standard"
        ValueError
            If chip_material is not None or in the allowable list of tempest chip materials
        """
        # tempest chip specification
        if (model != "high_volume") and (model is not None):
            raise ValueError(f"Tempest chip model is {model}. It must be: high_volume.")
        if (nozzle != "standard") and (nozzle is not None):
            raise ValueError(f"Tempest nozzle is {nozzle}. It must be: standard.")
        if (chip_material not in ["silicone", "pfe"]) and (chip_material is not None):
            raise ValueError(
                f"Tempest chip material is {chip_material}. It must be either: silicone or pfe."
            )

        device_mode_params = {}
        if any([model, chip_material, nozzle]):
            if model is None:
                model = "high_volume"
            if chip_material is None:
                chip_material = "pfe"
            if nozzle is None:
                nozzle = "standard"
            x_tempest_chip = {
                "model": model,
                "material": chip_material,
                "nozzle": nozzle,
            }
            device_mode_params["x_tempest_chip"] = x_tempest_chip

        return device_mode_params

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

        return {"target": target, "acceleration": acceleration}

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
            raise TypeError(f"position {position} is not of type float/int")
        if not (position is None or -self.xy_max <= position <= self.xy_max):
            raise ValueError(
                f"position {position} was not in range {-self.xy_max} - "
                f"{self.xy_max}"
            )

        if move_rate is not None:
            move_rate = self.move_rate(**move_rate)

        return {"position": position, "move_rate": move_rate}

    def position_z(
        self,
        reference=None,
        offset=None,
        move_rate=None,
        detection_method=None,
        detection_threshold=None,
        detection_duration=None,
        detection_fallback=None,
        detection=None,
    ):
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
                f"reference must be one of {self.z_references} but "
                f"{reference} was specified"
            )
        if offset is not None:
            offset = parse_unit(offset, "mm")
        if move_rate is not None:
            move_rate = self.move_rate(**move_rate)

        detection = self._merge_param_dicts(
            dict(
                method=detection_method,
                threshold=detection_threshold,
                duration=detection_duration,
                fallback=detection_fallback,
            ),
            detection,
        )

        if any(detection.values()) and not reference == "liquid_surface":
            raise ValueError(
                f"detection parameters were specified, but reference "
                f"{reference} does not support detection"
            )

        method = detection.get("method")
        duration = detection.get("duration")
        threshold = detection.get("threshold")
        fallback = detection.get("fallback")

        if method is not None and method not in self.z_detection_methods:
            raise ValueError(
                f"detection_method must be one of {self.z_detection_methods} "
                f"but {method} was specified"
            )

        if duration is not None:
            duration = parse_unit(duration, "s")

        if threshold is not None:
            threshold = parse_unit(threshold, ["pascal", "farad"])

        if fallback is not None:
            fallback = self.position_z(**fallback)

        detection["method"] = method
        detection["duration"] = duration
        detection["threshold"] = threshold
        detection["fallback"] = fallback

        return {
            "reference": reference,
            "offset": offset,
            "move_rate": move_rate,
            "detection": detection,
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

        return {"tip_type": tip_type}

    def mix(self, volume, repetitions, initial_z, asp_flowrate=None, dsp_flowrate=None):
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
            raise TypeError(f"repetitions {repetitions} is not an int")
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
            "dsp_flowrate": dsp_flowrate,
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

        return {"volume": volume, "initial_z": initial_z, "flowrate": flowrate}

    def desired_mode(self, transports=None, mode=None):
        """Helper for selecting dispense mode based on liquid_class name
        For non-viscous, water-like liquid and air, the method will default
        to "air_displacement". To allow for more accurate aspirate and
        dispense volumes, 'viscous' liquid where air pressure alone is
        sometimes not sufficient to overcome the surface tension to pull
        or push the liquid sufficiently through transfer tip, it will
        default to "positive_displacement" unless otherwise specified.

        Examples
        --------

        .. code-block:: python

            example_transports = [
                LiquidHandle.builders.transport(
                    volume=Unit(1, "uL"),
                    density=None,
                    pump_override_volume=Unit(2, "uL"),
                    flowrate=LiquidHandle.builders.flowrate(
                        target=Unit(10, "uL/s")
                    ),
                    delay_time=Unit(0.5, "s"),
                    mode_params=LiquidHandle.builders.mode_params(
                        liquid_class="air",
                        position_z=LiquidHandle.builders.position_z(
                            reference="preceding_position"
                        )
                    )
                ),
                LiquidHandle.builders.transport(
                    volume=Unit(1, "uL"),
                    density=None,
                    pump_override_volume=Unit(2, "uL"),
                    flowrate=LiquidHandle.builders.flowrate(
                        target=Unit(10, "uL/s")
                    ),
                    delay_time=Unit(0.5, "s"),
                    mode_params=LiquidHandle.builders.mode_params(
                        liquid_class="viscous",
                        position_z=LiquidHandle.builders.position_z(
                            reference="preceding_position"
                        )
                    )
                )
            ]

        LiquidHandle.builders.desired_mode(example_transports, None)

        This will return "positive_displacement" based on the "viscous" liquid
        class. Note that "air" (which defaults to "air_displacement") does not
        cause a conflict since "air" is often applied in additional transfers
        of air (such as blowout) for any liquid class, and is disregarded.

        Parameters
        ----------
        transports : dict, optional
            Dictionary of the transport parameters
        mode : str, optional
            Mode of dispense type

        Returns
        -------
        str
            Mode of dispense type

        Raises
        ------
        TypeError
            mode is not in str
        ValueError
            mode does not contain valid mode value
        TypeError
            liquid is not of str
        ValueError
            liquid_class is not a valid value
        ValueError
            liquid_class did not resolve to a mode
        ValueError
            multiple liquid_class exists in one LiquidHandle
        """
        # dict for default dispense mode for each liquid_class
        liquid_class_to_dispense_mode = {
            "air": "air_displacement",
            "default": "air_displacement",
            "viscous": "positive_displacement",
        }
        if mode:
            if mode not in self.dispense_modes:
                raise ValueError(
                    f"mode: {mode} must be one of the valid modes: "
                    f"{self.dispense_modes}"
                )
            return mode

        # get liquid_classes from transport input
        mode_params = [transport["mode_params"] for transport in transports]
        if all(mode_param is None for mode_param in mode_params):
            liquid_classes = {None}
        else:
            liquid_classes = set(
                [mode_param["liquid_class"] for mode_param in mode_params]
            )
        # remove automatically added 'air' (e.g. from blowout steps) and None
        # classes.
        other_classes = liquid_classes - {"air", None}
        if not other_classes:
            return liquid_class_to_dispense_mode["air"]

        modes = set()
        for other_class in other_classes:
            # resolve mode for different other_class classes (except for None).
            if not isinstance(other_class, str):
                raise TypeError(f"liquid_class: {other_class} is not of type str")
            if other_class not in self.liquid_classes:
                raise ValueError(
                    f"liquid_class: {other_class} must be one of the "
                    f"valid flasses: {self.liquid_classes} "
                )
            if other_class not in liquid_class_to_dispense_mode.keys():
                raise ValueError(
                    f"liquid_class: {other_class} did not resolve accordingly. "
                    f"If there is a new liquid_class, make sure dictionary:"
                    f"{liquid_class_to_dispense_mode} is updated."
                )
            modes.add(liquid_class_to_dispense_mode[other_class])
        # return error if modes is empty.
        if not modes:
            raise ValueError(
                f"modes: {modes} resulted in an empty set. Make sure valid "
                f"mode is added for each liquid class."
            )
        # return error if there are incompatible liquid_class a set of
        # transports.
        if len(set(modes)) > 1:
            raise ValueError(
                f"There are multiple liquid_class types which could "
                f"potentially have different modes: {set(modes)}. Please "
                f"specify the mode to be used from: {self.dispense_modes}. "
                f"Only one mode is allowed per transfer."
            )
        return list(modes)[0]


class PlateReaderBuilders(InstructionBuilders):
    """Helpers for building parameters for plate reading instructions"""

    def incubate_params(
        self, duration, shake_amplitude=None, shake_orbital=None, shaking=None
    ):
        """
        Create a dictionary with incubation parameters which can be used as
        input for instructions. Currently supports plate reader instructions and
        could be extended for use with other instructions.

        Parameters
        ----------
        duration: str or Unit
            the duration to shake the plate for
        shake_amplitude: str or Unit, optional
            amplitude of shaking between 1 and 6:millimeter
        shake_orbital: bool, optional
            True for orbital and False for linear shaking
        shaking : dict, optional
            A dict of amplitude and orbital: should only be specified if none of
            the other tip shake parameters have been specified.
            Dictionary of incubate parameters

        Returns
        -------
        dict
            plate reader incubate_params

        Raises
        ------
        ValueError
            if shake `duration` is not positive
        ValueError
            if only one of shake_amplitude or shake_orbital is set
        TypeError
            if `shake_orbital` is not a bool
        ValueError
            if `shake_amplitude` is not positive

        """
        duration = parse_unit(duration, "second")
        if duration <= Unit(0, "second"):
            raise ValueError(f"duration: {duration} is not positive")

        shaking = self._merge_param_dicts(
            dict(amplitude=shake_amplitude, orbital=shake_orbital), shaking
        )
        amplitude = shaking.get("amplitude")
        orbital = shaking.get("orbital")

        if (amplitude is not None) and (orbital is not None):
            amplitude = parse_unit(amplitude, "millimeter")
            if amplitude <= Unit(0, "millimeter"):
                raise ValueError(f"shake_amplitude: {amplitude} is not positive")
            if not isinstance(orbital, bool):
                raise TypeError(f"shake_orbital: {orbital} is not a bool")
        elif (amplitude is not None) ^ (orbital is not None):
            raise ValueError(
                f"shake_amplitude: {amplitude} and shake_orbital: {orbital} "
                f"must both be specified to shake"
            )

        return {
            "duration": duration,
            "shaking": {"amplitude": amplitude, "orbital": orbital},
        }


class EvaporateBuilders(InstructionBuilders):
    """
    Helpers for building Evaporate instructions
    """

    def __init__(self):
        super(EvaporateBuilders, self).__init__()
        self.valid_modes = ["rotate", "centrifuge", "vortex", "blowdown"]
        self.valid_gases = ["nitrogen", "argon", "helium"]
        self.rotary_params = [
            "flask_volume",
            "rotation_speed",
            "vacuum_pressure",
            "condenser_temperature",
        ]
        self.centrifugal_params = [
            "spin_acceleration",
            "vacuum_pressure",
            "condenser_temperature",
        ]
        self.vortex_params = [
            "vortex_speed",
            "vacuum_pressure",
            "condenser_temperature",
        ]
        self.blowdown_params = ["gas", "blow_rate", "vortex_speed"]

    def get_mode_params(self, mode, mode_params):
        """
        Checks on the validity of mode and mode_params, and
        creates a dictionary for mode_params

        Parameters
        ----------
        mode : Str
            Mode of the evaporate method.
        mode_params : Dict
            Method parameters for each mode.

        Returns
        -------
        Dict
            Dictionary of mode_params

        Raises
        ------
        ValueError
            If mode is not specified.
        ValueError
            If specified mode is not a valid mode.
        ValueError
            If mode_params contain key(s) that are not
            applicable for the specified mode.
        TypeError
            If there are multiple speed parameters.
        ValueError
            If container agitation speed is less than 0.
        ValueError
            If vacuum_pressure is less than 0 torr.

        """
        mode_to_param_dict = {
            "rotary": self.rotary_params,
            "centrifugal": self.centrifugal_params,
            "vortex": self.vortex_params,
            "blowdown": self.blowdown_params,
        }
        if mode not in self.valid_modes:
            raise ValueError(
                f"Specified mode: {mode} is not valid. Make sure it is one "
                f"of {self.valid_modes}"
            )

        mode_param_keys = mode_to_param_dict[mode]

        if set(mode_params.keys()) != set(mode_param_keys):
            raise ValueError(
                f"Specified mode_params: {mode_params.keys()} do not contain "
                f"appropriate key(s) applicable to the mode: {mode}, which "
                f"include {mode_param_keys}"
            )
        speed_unit_dict = {
            "rotation_speed": "rpm",
            "vortex_speed": "rpm",
            "spin_acceleration": "g",
        }
        mode_param_output = {}
        speed_param = [(k) for k in mode_params.keys() if k in speed_unit_dict.keys()]
        if len(speed_param) > 1:
            raise TypeError(f"There are multiple speed parameters: {speed_param}.")

        for s in speed_param:
            if Unit(mode_params[s]).magnitude <= 0:
                raise ValueError(f"{s} is less than or equal to 0.")
            else:
                mode_param_output[s] = parse_unit(mode_params[s], speed_unit_dict[s])

        if "vacuum_pressure" in mode_params.keys():
            pressure = mode_params["vacuum_pressure"]
            if pressure is not None:
                pressure = parse_unit(pressure, "torr")
                if pressure <= Unit("0: torr"):
                    raise ValueError("vacuum_pressure cannot be lower than 0 torr.")
                else:
                    mode_param_output["vacuum_pressure"] = pressure

        if "condenser_temperature" in mode_params.keys():
            temp = mode_params["condenser_temperature"]
            if temp is not None:
                temp = parse_unit(temp, "celsius")
                mode_param_output["condenser_temperature"] = temp

        if "gas" in mode_params.keys():
            if not mode_params["gas"] in self.valid_gases:
                raise TypeError(
                    f"Specified gas: {mode_params['gas']} is not included in "
                    f"valid gases: {self.valid_gases}"
                )
            mode_param_output["gas"] = mode_params["gas"]

        if "blow_rate" in mode_params.keys():
            blow_rate = mode_params["blow_rate"]
            if not blow_rate is None:
                blow_rate = parse_unit(blow_rate, "mL/min")
                mode_param_output["blow_rate"] = blow_rate

        return mode_param_output


class GelPurifyBuilders(InstructionBuilders):
    """Helpers for building GelPurify instructions"""

    def extract(self, source, band_list, lane=None, gel=None):
        """Helper for building extract params for gel_purify

        Parameters
        ----------
        source : Well
            The Well that contains the sample be purified
        band_list : list(dict)
            A list of bands to be extracted from the source sample
        lane : int, optional
            The gel lane for the source sample to be run on
        gel : int, optional
            The number of the gel if using multiple gels

        Returns
        -------
        dict
            gel_purify extract parameters

        Raises
        ------
        TypeError
            If source is not a Well

        """
        if not isinstance(source, Well):
            raise TypeError(f"source: {source} is not a Well")

        if not isinstance(band_list, list):
            band_list = [band_list]

        band_list = [self.band(**_) for _ in band_list]

        return {"source": source, "band_list": band_list, "lane": lane, "gel": gel}

    def band(
        self,
        elution_buffer,
        elution_volume,
        destination,
        min_bp=None,
        max_bp=None,
        band_size_range=None,
    ):
        """Helper for building band params for gel_purify

        Parameters
        ----------
        elution_buffer : str
            The type of elution buffer to be used
        elution_volume : str or Unit
            The volume of sample to be eluted
        destination : Well
            The Well the extracted samples should be eluted into
        min_bp : int, optional
            The minimum size sample to be removed.
        max_bp : int, optional
            The maximum size sample to be removed.
        band_size_range : dict, optional
            A dict of band size parameters. Should only be specified if none of
            the other band size parameters have been specified.

        Returns
        -------
        dict
            gel_purify band parameters

        Raises
        ------
        TypeError
            If destination is not a Well
        TypeError
            If `min_bp` is not an int
        TypeError
            If `max_bp` is not an int
        ValueError
            If `min_bp` is not less than `max_bp`

        """
        elution_buffer = str(elution_buffer)
        elution_volume = parse_unit(elution_volume, "microliter")
        if not isinstance(destination, Well):
            raise TypeError(f"destination: {destination} is not a Well")

        band_size_range = self._merge_param_dicts(
            dict(min_bp=min_bp, max_bp=max_bp), band_size_range
        )
        min_bp = band_size_range.get("min_bp")
        max_bp = band_size_range.get("max_bp")

        if not isinstance(min_bp, int):
            raise TypeError(f"min_bp {min_bp} was not an int")

        if not isinstance(max_bp, int):
            raise TypeError(f"max_bp {max_bp} was not an int")

        if not min_bp < max_bp:
            raise ValueError(f"min_bp: {min_bp} is not less than max_bp: {max_bp}")

        return {
            "destination": destination,
            "elution_volume": elution_volume,
            "elution_buffer": elution_buffer,
            "band_size_range": {"min_bp": min_bp, "max_bp": max_bp},
        }


# pylint: disable=redefined-builtin
class MagneticTransferBuilders(InstructionBuilders):
    """Helpers for building MagneticTransfer instruction parameters"""

    @staticmethod
    def mag_dry(object, duration):
        """Helper for building mag_dry sub operations for MagneticTransfer

        Parameters
        ----------
        object : Container
            The Container to be operated on
        duration : str or Unit
            The duration of the operation

        Returns
        -------
        dict
            mag_dry parameters

        Raises
        ------
        TypeError
            If `object` is not a Container

        See Also
        --------
        Protocol.mag_dry

        """
        if not isinstance(object, Container):
            raise TypeError(f"object: {object} is not a Container")
        duration = parse_unit(duration, "seconds")
        return {"object": object, "duration": duration}

    @staticmethod
    def mag_incubate(object, duration, magnetize, tip_position, temperature=None):
        """Helper for building mag_incubate sub operations for MagneticTransfer

        Parameters
        ----------
        object : Container
            The Container to be operated on
        duration : str or Unit
            The duration of the operation
        magnetize : bool
            Whether the magnetic head should be engaged during the operation
        tip_position : float
            Position relative to well height that magnetic head is held
        temperature : str or Unit, optional
            The temperature of the operation

        Returns
        -------
        dict
            mag_incubate parameters

        Raises
        ------
        TypeError
            If `object` is not a Container
        TypeError
            If `magnetize` is not a bool
        ValueError
            If `tip_position` is not a positive number

        See Also
        --------
        Protocol.mag_incubate

        """
        if not isinstance(object, Container):
            raise TypeError(f"object: {object} is not a Container")
        duration = parse_unit(duration, "seconds")
        if not isinstance(magnetize, bool):
            raise TypeError(f"magnetize: {magnetize} is not a bool")
        tip_position = float(tip_position)
        if tip_position < 0:
            raise ValueError(f"tip_position: {tip_position} must be >= 0")
        if temperature is not None:
            parse_unit(temperature, "celsius")
        return {
            "object": object,
            "duration": duration,
            "magnetize": magnetize,
            "tip_position": tip_position,
            "temperature": temperature,
        }

    @staticmethod
    def mag_collect(
        object, cycles, pause_duration, bottom_position=None, temperature=None
    ):
        """Helper for building mag_collect sub operations for MagneticTransfer

        Parameters
        ----------
        object : Container
            The Container to be operated on
        cycles : int
            The number of times the operation should be repeated
        pause_duration : str or Unit
            The delay time between each repetition of the operation
        bottom_position : float, optional
            Position relative to well height where the magnetic head pauses
        temperature : str or Unit, optional
            The temperature of the operation

        Returns
        -------
        dict
            mag_collect parameters

        Raises
        ------
        TypeError
            If `object` is not a Container
        TypeError
            If `cycles` is not an int
        ValueError
            If `bottom_position` is not a positive number

        See Also
        --------
        Protocol.mag_collect

        """
        if not isinstance(object, Container):
            raise TypeError(f"object: {object} is not a Container")
        if not isinstance(cycles, int):
            raise TypeError(f"cycles: {cycles} is not an int")
        pause_duration = parse_unit(pause_duration, "seconds")
        bottom_position = float(bottom_position)
        if bottom_position < 0:
            raise ValueError(f"bottom_position: {bottom_position} must be >= 0")
        if temperature is not None:
            parse_unit(temperature, "celsius")
        return {
            "object": object,
            "cycles": cycles,
            "pause_duration": pause_duration,
            "bottom_position": bottom_position,
            "temperature": temperature,
        }

    @staticmethod
    def mag_release(
        object, duration, frequency, center=None, amplitude=None, temperature=None
    ):
        """Helper for building mag_release sub operations for MagneticTransfer

        Parameters
        ----------
        object : Container
            The Container to be operated on
        duration : str or Unit
            The duration of the operation
        frequency : str or Unit
            The frequency of the magnetic head during the operation
        center : float, optional
            Position relative to well height where oscillation is centered
        amplitude : float, optional
            Distance relative to well height to oscillate around `center`
        temperature : str or Unit, optional
            The temperature of the operation

        Returns
        -------
        dict
            mag_release parameters

        Raises
        ------
        TypeError
            If `object` is not a Container
        ValueError
            If `center` is less than 0
        ValueError
            If `amplitude` is greater than center

        See Also
        --------
        Protocol.mag_release

        """
        if not isinstance(object, Container):
            raise TypeError(f"object: {object} is not a Container")
        duration = parse_unit(duration, "seconds")
        frequency = parse_unit(frequency, "hertz")
        if center is not None:
            center = float(center)
            if center < 0:
                raise ValueError(f"center: {center} must be >= 0")
        if amplitude is not None:
            amplitude = float(amplitude)
        if center is not None and amplitude is not None and amplitude > center:
            raise ValueError(
                f"center: {center} must be greater than or equal to amplitude: "
                f"{amplitude}"
            )
        if temperature is not None:
            parse_unit(temperature, "celsius")
        return {
            "object": object,
            "duration": duration,
            "frequency": frequency,
            "center": center,
            "amplitude": amplitude,
            "temperature": temperature,
        }

    @staticmethod
    def mag_mix(
        object,
        duration,
        frequency,
        center=None,
        amplitude=None,
        magnetize=None,
        temperature=None,
    ):
        """Helper for building mag_mix sub operations for MagneticTransfer

        Parameters
        ----------
        object : Container
            The Container to be operated on
        duration : str or Unit
            The duration of the operation
        frequency : str or Unit, optional
            The frequency of the magnetic head during the operation
        center : float, optional
            Position relative to well height where oscillation is centered
        amplitude : float, optional
            Distance relative to well height to oscillate around `center`
        magnetize : bool, optional
            Whether the magnetic head should be engaged during the operation
        temperature : str or Unit, optional
            The temperature of the operation

        Returns
        -------
        dict
            mag_mix parameters

        Raises
        ------
        TypeError
            If `object` is not a Container
        ValueError
            If `center` is less than 0
        ValueError
            If `amplitude` is greater than center
        TypeError
            If `magnetize` is not a bool


        See Also
        --------
        Protocol.mag_mix

        """
        if not isinstance(object, Container):
            raise TypeError(f"object: {object} is not a Container")
        duration = parse_unit(duration, "seconds")
        frequency = parse_unit(frequency, "hertz")
        if center is not None:
            center = float(center)
            if center < 0:
                raise ValueError(f"center: {center} must be >= 0")
        if amplitude is not None:
            amplitude = float(amplitude)
        if center is not None and amplitude is not None and amplitude > center:
            raise ValueError(
                f"center: {center} must be greater than or equal to amplitude: "
                f"{amplitude}"
            )
        if magnetize is not None and not isinstance(magnetize, bool):
            raise TypeError(f"magnetize: {magnetize} is not a bool")
        if temperature is not None:
            parse_unit(temperature, "celsius")

        return {
            "object": object,
            "duration": duration,
            "frequency": frequency,
            "center": center,
            "amplitude": amplitude,
            "magnetize": magnetize,
            "temperature": temperature,
        }


class FlowCytometryBuilders(InstructionBuilders):
    """
    Builders for FlowCytometry instructions.
    """

    def __init__(self):
        super(FlowCytometryBuilders, self).__init__()
        self.gating_modes = ("FSC", "SSC")

    def laser(self, channels, excitation=None, power=None, area_scaling_factor=None):
        """
        Generates a dict of laser parameters.

        Parameters
        ----------
        channels : list(dict)
            See :meth:`FlowCytometryBuilders.channel`.
        excitation : Unit or str, optional
            Excitation wavelength.
        power : Unit or str, optional
            Laser power.
        area_scaling_factor : Number, optional
            Value to scale height and area equivalently.

        Raises
        ------
        TypeError
            If `channels` is not a list of dict.
        TypeError
            If `channels` is not a list of dict.
        TypeError
            If `area_scaling_factor` is not a number.
        ValueError
            If a gating channel (e.g. SSC) is specified and excitation is also specified.

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
            area_scaling_factor, Number
        ):
            raise TypeError("area_scaling_factor must be a number.")

        if power is not None:
            power = parse_unit(power, "milliwatts")

        if excitation is not None:
            excitation = parse_unit(excitation, "nanometers")

        channels = [self.channel(**_) for _ in channels]

        # Gating modes do not allow specification of excitation parameter
        channel_names = set(
            [chn["emission_filter"]["channel_name"] for chn in channels]
        )
        if channel_names.intersection(self.gating_modes) and excitation is not None:
            raise ValueError(
                f"Cannot specify excitation if channel_name is one of {self.gating_modes}"
            )

        return {
            "excitation": excitation,
            "power": power,
            "area_scaling_factor": area_scaling_factor,
            "channels": channels,
        }

    def channel(
        self,
        emission_filter,
        detector_gain,
        measurements=None,
        trigger_threshold=None,
        trigger_logic=None,
    ):
        """
        Generates a dict of channel parameters.

        Parameters
        ----------
        emission_filter : dict
            See :meth:`FlowCytometryBuilders.emission_filter`.
        detector_gain : Unit or str
            Detector gain.
        measurements : dict, optional
            Pulse properties to record. See
            :meth:`FlowCytometryBuilders.measurements`.
        trigger_threshold : int, optional
            Channel intensity threshold. Events below this threshold.
        trigger_logic : Enum({"and", "or"}), optional
            Operator used to combine threshold.

        Raises
        ------
        TypeError
            If `trigger_threshold` is not of type int.
        ValueError
            If `trigger_logic` is not one of {"and", "or"}.

        Returns
        -------
        dict
            A dict of channel parameters.
        """
        if trigger_threshold is not None and not isinstance(trigger_threshold, int):
            raise TypeError("trigger_threshold must be of type int.")

        trigger_modes = ("and", "or")
        if trigger_logic is not None and trigger_logic not in trigger_modes:
            raise ValueError(f"trigger_logic must be one of {trigger_modes}.")

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
            "trigger_logic": trigger_logic,
        }

    def emission_filter(self, channel_name, shortpass=None, longpass=None):
        """
        Generates a dict of emission filter parameters.

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

        if channel_name in self.gating_modes and (shortpass or longpass):
            raise ValueError(
                f"Cannot specify shortpass/longpass "
                f"parameters if channel_name is one of "
                f"{self.gating_modes}"
            )

        if shortpass is not None:
            shortpass = parse_unit(shortpass, "nanometers")

        if longpass is not None:
            longpass = parse_unit(longpass, "nanometers")

        return {
            "channel_name": channel_name,
            "shortpass": shortpass,
            "longpass": longpass,
        }

    @staticmethod
    def measurements(area=None, height=None, width=None):
        """
        Generates a dict of measurements parameters.

        Parameters
        ----------
        area : bool, optional
            Area measurement.
        height : bool, optional
            Height measurement.
        width : bool, optional
            Width measurement.

        Raises
        ------
        TypeError
            If any of `area` | `height` | `width` are not of type bool.

        Returns
        -------
        dict
            A dict of measurements params.
        """

        if any(not isinstance(_, (bool, type(None))) for _ in (area, height, width)):
            raise TypeError("area, height, and width must be of type bool.")

        return {"area": area, "height": height, "width": width}

    def collection_conditions(
        self,
        acquisition_volume,
        flowrate,
        wait_time,
        mix_cycles,
        mix_volume,
        rinse_cycles,
        stop_criteria=None,
    ):
        """
        Generates a dict of collection_conditions parameters.

        Parameters
        ----------
        acquisition_volume : Unit or str
            Acquisition volume.
        flowrate : Unit or str
            Flow rate.
        wait_time : Unit or str
            Waiting time.
        mix_cycles : int
            Number of mixing cycles before acquisition.
        mix_volume : Unit or str
            Mixing volume.
        rinse_cycles : int
            Number of rinsing cycles.
        stop_criteria : dict, optional
            See :meth:`FlowCytometryBuilders.stop_criteria`.

        Raises
        ------
        TypeError
            If `rinse_cycles` is not of type int.
        TypeError
            If `mix_cycles` is not of type int.

        Returns
        -------
        dict
            A dict of `collection_condition` parameters.
        """
        if not isinstance(rinse_cycles, int):
            raise TypeError("rinse_cycles must be of type int.")

        if not isinstance(mix_cycles, int):
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
            "rinse_cycles": rinse_cycles,
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
        time : Unit or str, optional
            Stopping time.

        Raises
        ------
        TypeError
            If `events` is not of type int.

        Returns
        -------
        dict
            A dict of `stop_criteria` params.
        """
        if events is not None and not isinstance(events, int):
            raise TypeError("events must be of type int.")

        if volume is not None:
            volume = parse_unit(volume, "ul")

        if time is not None:
            time = parse_unit(time, "s")

        return {"volume": volume, "events": events, "time": time}
