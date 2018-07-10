"""
Module containing builders, which help build inputs for Instruction parameters

    :copyright: 2018 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""

from .util import parse_unit, is_valid_well
from .container import WellGroup, Well
from .unit import Unit


# pylint: disable=no-init
class ThermocycleBuilders:
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


class DispenseBuilders(object):
    """
    These builders are meant for helping to construct arguments in the
    `Protocol.dispense` method.
    """
    def __init__(self):
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


class SpectrophotometryBuilders(object):
    def __init__(self):
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

    def absorbance_mode_params(self, wells, wavelength, num_flashes=None,
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

    def luminescence_mode_params(self, wells, num_flashes=None,
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
