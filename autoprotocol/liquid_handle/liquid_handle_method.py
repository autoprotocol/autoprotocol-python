"""LiquidHandleMethod

Base class for generating complex liquid handling behavior.

    :copyright: 2021 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

Summary
-------
LiquidHandleMethods are passed as arguments to Protocol methods along with
LiquidClasses to specify complex series of liquid handling behaviors.

Notes
-----
Methods in this file should not be used directly, but are intended to be
extended by other methods depending on desired behavior.

When creating a vendor-specific library it's likely desirable to monkey patch
`LiquidHandleMethod._get_tip_types` to reference TipTypes that the vendor
supports.
"""
from ..instruction import LiquidHandle
from ..unit import Unit
from ..util import parse_unit
from .tip_type import TipType


# pylint: disable=too-many-public-methods,protected-access
class LiquidHandleMethod(object):
    """Base LiquidHandleMethod

    General framework for liquid handling abstractions and helpers for
    building a series of liquid_handle transports.

    Attributes
    ----------
    _shape : dict
        the SBS shape and number of rows and columns of the liquid_handle
    _transports : list
        tracks transports to be added to the LiquidHandle instruction

    Notes
    -----
    There is a hierarchy of logic to all LiquidHandleMethods that abstracts a
    complex set of liquid handling behavior into smaller, discrete steps.

    For step `x` (aspirate, dispense, mix) and parameter `y` (e.g. blowout):
        - Protocol method:
            - calls LiquidHandleMethod._`x`_transports
        - LiquidHandleMethod._`x`_transports method:
            - clears the _transports list
            - walks through all _transport methods including _transport_`y`
            - returns the _transports lists
        - LiquidHandleMethod._transport_`y` method:
            - checks parameter `y` in addition to the default_`y` method
            - possibly generates a series of transports based on the two values
            - calls lower level helper methods
        - LiquidHandleMethod lower level helper methods:
            - generate transports and append them to _transports

    Examples
    --------
    For specifying a single, global liquid handling behavior across all
    volumes the easiest way is to specify parameters when instantiating a
    LiquidHandleMethod.

    .. code-block:: python

        from autoprotocol import Unit
        from autoprotocol.instruction import LiquidHandle
        from autoprotocol.liquid_handle import LiquidHandleMethod

        lhm = LiquidHandleMethod(
            blowout=LiquidHandle.builders.blowout(volume=Unit(10, "uL"))
        )

    For behavior that relies on more liquid handling parameters or even defines
    new behavior you can define your own LiquidHandleMethod.

    .. code-block:: python

        from autoprotocol import Unit
        from autoprotocol.instruction import LiquidHandle
        from autoprotocol.liquid_handle import LiquidHandleMethod

        class NewLHM(LiquidHandleMethod):
            def default_blowout(self, volume):
                if volume < Unit(10, "uL"):
                    blowout_volume = Unit(1, "uL")
                else:
                    blowout_volume = Unit(10, "uL")
                return LiquidHandle.builders.blowout(
                    volume=blowout_volume
                )

    See Also
    --------
    Transfer : method for handling liquid between two locations
    Mix : method for handling liquid within locations
    LiquidClass : contain properties that are intrinsic to specific liquids
    Protocol : contains methods that accept LiquidHandleMethods as arguments
    """

    def __init__(self, tip_type=None, blowout=True):
        """
        Parameters
        ----------
        tip_type : str, optional
            tip_type to be used for the LiquidHandlingMethod
        blowout : bool or dict, optional
            whether to execute a blowout step or the parameters for one.
            this generates two operations, an initial air aspiration before
            entering any wells, and a corresponding final air dispense
            after the last operation that involves liquid
            See Also LiquidHandle.builders.blowout
        """
        self.tip_type = tip_type
        self.blowout = blowout

        # LiquidHandle parameters that are generated and modified at runtime
        self._shape = None
        self._transports = []

    def _get_tip_types(self):
        """Gets a list of TipTypes based on _shape

        Decides on the TipTypes that are compatible with the _shape of the
        liquid handling operation.

        Returns
        -------
        list
            list of valid TipTypes

        Notes
        -----
        This method exists to be monkey patched in vendor libraries to map
        shape parameters to actual tip types.

        Raises
        ------
        RuntimeError
            if there are no tips that support the _shape

        See Also
        --------
        _get_sorted_tip_types : the standard interface for this method
        """
        if self._is_single_channel():
            tip_types = [
                TipType("generic_1_50", Unit("50:ul")),
                TipType("generic_1_1000", Unit("1000:ul")),
            ]
        elif self._shape["format"] == "SBS96":
            tip_types = [TipType("generic_96_180", Unit("180:ul"))]
        elif self._shape["format"] == "SBS384":
            tip_types = [TipType("generic_384_30", Unit("30:ul"))]
        else:
            raise RuntimeError(f"No tip types supported for shape: {self._shape}")

        return tip_types

    def _get_sorted_tip_types(self):
        """Gets a list of valid TipTypes in ascending order of volume

        Returns
        -------
        list
            list of valid TipTypes sorted by their maximum capacity

        See Also
        --------
        _get_tip_types : vendor library-specific tip selection method
        """
        return sorted(self._get_tip_types(), key=lambda t: t.volume)

    def _rec_tip_type(self, volume):
        """For a given volume gets the smallest appropriate tip type

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        Unit
            the recommended tip type for a given volume

        Raises
        ------
        RuntimeError
            if there is no tip large enough for the specified volume
        """
        total_vol = volume + self._calculate_overage_volume(volume)
        tips = self._get_sorted_tip_types()
        valid_tips = list(filter(lambda t: t.volume >= total_vol, tips))
        if not valid_tips:
            raise RuntimeError(
                f"None of the TipTypes: {tips} allowed for this shape are "
                f"large enough to hold: {total_vol} (the target volume + "
                f"overage)."
            )
        return valid_tips[0].name

    def _tip_capacity(self):
        """Gets the best estimate of tip capacity with the given information

        Uses either the defined or a calculated tip_type to estimate the
        total usable volume for a given tip after accounting for overage volume.

        Returns
        -------
        Unit
            the maximum allowable volume for the method's tip_type

        See Also
        --------
        _calculate_overage_volume : calculates volume unusable for liquid
        """
        tip_types = self._get_sorted_tip_types()
        if self.tip_type is None:
            tip_capacity = tip_types[-1].volume
        else:
            tips_by_name = {_.name: _ for _ in tip_types}
            tip_capacity = tips_by_name[self.tip_type].volume

        overage_vol = self._calculate_overage_volume(tip_capacity).ceil()
        max_volume = tip_capacity - overage_vol

        return max_volume

    def _has_calibration(self):
        """Checks whether any specified LiquidClasses specify any calibrations

        Checks whether any of the LiquidClasses used by the
        LiquidHandleMethod have any volume or flowrate calibration.

        Returns
        -------
        bool
            whether there will be any calibration based on LiquidClasses

        See Also
        --------
        LiquidClass._has_calibration : checks for calibration parameters
        """
        raise NotImplementedError

    @staticmethod
    def _estimate_calibrated_volume(volume, liquid, tip_type):
        """Gives an estimation of calibrated volume

        If tip_type is specified then gets the actual calibrated volume,
        but if it is None then gets a rough estimate of the maximum volume
        calibration that might be experienced.

        This is used for estimates of calibrated volume used for calculating
        overage volume within the tip.

        Parameters
        ----------
        volume : Unit
            the uncalibrated volume
        liquid : LiquidClass
            the liquid class to be calibrated against
        tip_type : str or None
            the name of the TipType to be used

        Returns
        -------
        Unit
            an estimate of the calibrated volume

        See Also
        --------
        _calculate_overage_volume : uses this method
        LiquidClass._safe_volume_multiplier : used if no tip_type is specified
        """

        estimated = liquid._safe_volume_multiplier * volume
        if tip_type:
            calculated = liquid._get_calibrated_volume(volume, tip_type)
            cal_vol = calculated if calculated is not None else estimated
        else:
            cal_vol = estimated

        return cal_vol

    def _calculate_overage_volume(self, volume):
        """Calculates extra volume held in the tip besides the target volume

        Calculates how much extra volume is contained within the tip besides
        the target volume. This includes things like overage due to
        calibrated volumes being larger than the nominal volume.

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        Unit
            the extra volume taken up in the tip besides the transfer volume
        """
        raise NotImplementedError

    def _is_single_channel(self):
        """Determines whether _shape represents a single channel

        Returns
        -------
        bool
            whether or not the method's shape is single channel-compatible
        """
        return self._shape["rows"] == 1 and self._shape["columns"] == 1

    def _aspirate_simple(
        self,
        volume,
        initial_z,
        position_x=None,
        position_y=None,
        calibrated_vol=None,
        flowrate=None,
        delay_time=None,
        liquid_class=None,
        density=None,
    ):
        """Helper function for generating aspirate transports

        Parameters
        ----------
        volume : Unit
            volume of liquid to be aspirated
        initial_z : dict
            position that the tip will move to before pump movement
        position_x : dict, optional
            position that the tip will move to before pump movement
        position_y : dict, optional
            position that the tip will move to before pump movement
        calibrated_vol : Unit, optional
            calibrated volume, volume which the pump will move
        flowrate : dict, optional
            flowrate of liquid during aspiration
        delay_time : Unit, optional
            time to pause after aspirating to let pressure equilibrate
        liquid_class : str, optional
            the name of the liquid class being aspirated
        density : Unit, optional
            the density of liquid being aspirated
        """

        followup_z = self._move_to_initial_position(position_x, position_y, initial_z)

        mode_params = LiquidHandle.builders.mode_params(
            position_x=position_x,
            position_y=position_y,
            position_z=followup_z,
            liquid_class=liquid_class,
        )

        self._transports += [
            LiquidHandle.builders.transport(
                volume=-volume,
                density=density,
                # pylint: disable=invalid-unary-operand-type
                pump_override_volume=-calibrated_vol if calibrated_vol else None,
                flowrate=flowrate,
                mode_params=mode_params,
                delay_time=delay_time,
            )
        ]

    def _aspirate_with_prime(
        self,
        volume,
        prime_vol,
        initial_z,
        position_x=None,
        position_y=None,
        calibrated_vol=None,
        asp_flowrate=None,
        dsp_flowrate=None,
        delay_time=None,
        liquid_class=None,
        density=None,
    ):
        """Helper function for generating aspiration with priming

        Parameters
        ----------
        volume : Unit
            volume of liquid to be aspirated
        prime_vol : Unit
            volume of additional liquid to be aspirated along with volume
        initial_z : dict
            position that the tip will move to before pump movement
        position_x : dict, optional
            position that the tip will move to before pump movement
        position_y : dict, optional
            position that the tip will move to before pump movement
        calibrated_vol : Unit, optional
            calibrated volume, volume which the pump will move
        asp_flowrate : dict, optional
            flowrate of liquid during aspiration
        dsp_flowrate : dict, optional
            flowrate of liquid during aspiration
        delay_time : Unit, optional
            time to pause after aspirating to let pressure equilibrate
        liquid_class : str, optional
            the name of the liquid class being aspirated
        density : Unit, optional
            the density of liquid being aspirated
        """

        followup_z = self._move_to_initial_position(position_x, position_y, initial_z)

        mode_params = LiquidHandle.builders.mode_params(
            position_x=position_x,
            position_y=position_y,
            position_z=followup_z,
            liquid_class=liquid_class,
        )

        # Aspirate with priming volume
        self._transports += [
            LiquidHandle.builders.transport(
                volume=-prime_vol,
                density=density,
                pump_override_volume=-prime_vol,
                flowrate=asp_flowrate,
                mode_params=mode_params,
                delay_time=delay_time,
            ),
            LiquidHandle.builders.transport(
                volume=-volume,
                density=density,
                # pylint: disable=invalid-unary-operand-type
                pump_override_volume=(-calibrated_vol if calibrated_vol else None),
                flowrate=asp_flowrate,
                mode_params=mode_params,
                delay_time=delay_time,
            ),
            LiquidHandle.builders.transport(
                volume=prime_vol,
                density=density,
                pump_override_volume=prime_vol,
                flowrate=dsp_flowrate,
                mode_params=mode_params,
                delay_time=delay_time,
            ),
        ]

    def _dispense_simple(
        self,
        volume,
        initial_z,
        position_x=None,
        position_y=None,
        calibrated_vol=None,
        flowrate=None,
        delay_time=None,
        liquid_class=None,
        density=None,
    ):
        """Helper function for generating dispense transports

        Parameters
        ----------
        volume : Unit
            volume of liquid to be dispensed
        initial_z : dict
            position that the tip will move to before pump movement
        position_x : dict, optional
            position that the tip will move to before pump movement
        position_y : dict, optional
            position that the tip will move to before pump movement
        calibrated_vol : Unit, optional
            calibrated volume, volume which the pump will move
        flowrate : dict, optional
            flowrate of liquid during dispense
        delay_time : Unit, optional
            time to pause after dispensing to let pressure equilibrate
        liquid_class : str, optional
            the name of the liquid class being dispensed
        density : Unit, optional
            the density of liquid to be dispensed
        """

        followup_z = self._move_to_initial_position(position_x, position_y, initial_z)

        mode_params = LiquidHandle.builders.mode_params(
            position_x=position_x,
            position_y=position_y,
            position_z=followup_z,
            liquid_class=liquid_class,
        )

        self._transports += [
            LiquidHandle.builders.transport(
                volume=volume,
                density=density,
                pump_override_volume=calibrated_vol if calibrated_vol else None,
                flowrate=flowrate,
                mode_params=mode_params,
                delay_time=delay_time,
            )
        ]

    def _mix(
        self,
        volume,
        repetitions,
        position_x=None,
        position_y=None,
        initial_z=None,
        asp_flowrate=None,
        dsp_flowrate=None,
        delay_time=None,
        liquid_class=None,
    ):
        """Helper function for generating mix transports

        Parameters
        ----------
        volume : Unit
            volume of liquid to be aspirated and expelled during mixing
        repetitions : int
            number of times to aspirate and expel liquid during mixing
        initial_z : dict
            position_z of the tip during the move_before_mix transport that
            happens before mixing
        position_x : dict, optional
            position that the tip will move to before pump movement
        position_y : dict, optional
            position that the tip will move to before pump movement
        asp_flowrate : dict, optional
            flowrate of liquid aspiration during mixing
        dsp_flowrate : dict, optional
            flowrate of liquid dispensing during mixing
        delay_time : Unit, optional
            time to pause after dispensing to let pressure equilibrate
        liquid_class : str, optional
            the name of the liquid class being dispensed
        """

        followup_z = self._move_to_initial_position(position_x, position_y, initial_z)

        mode_params = LiquidHandle.builders.mode_params(
            position_x=position_x,
            position_y=position_y,
            position_z=followup_z,
            liquid_class=liquid_class,
        )

        self._transports += [
            LiquidHandle.builders.transport(
                volume=-volume,
                flowrate=asp_flowrate,
                mode_params=mode_params,
                delay_time=delay_time,
            ),
            LiquidHandle.builders.transport(
                volume=volume,
                flowrate=dsp_flowrate,
                mode_params=mode_params,
                delay_time=delay_time,
            ),
        ] * repetitions

    def _move_to_initial_position(
        self, position_x=None, position_y=None, position_z=None
    ):
        """Moves to a given position_z and then returns a followup one

        Takes an initial position_z and moves to it before returning a
        suitable followup.

        If sensing is specified, then moves to well top and senses before
        returning a suitable followup position.

        Parameters
        ----------
        position_x : dict, optional
            initial x position to move to before aspirating/dispensing
        position_y : dict, optional
            initial y position to move to before aspirating/dispensing
        position_z : dict, optional
            initial z position to move to before aspirating/dispensing

        Returns
        -------
        dict
            followup z position to pipette at after initial movement

        See Also
        --------
        _move_to_well_top_before_lld : helper method
        _get_followup_z : helper method
        """
        self._move_to_well_top_before_lld(position_z)

        if any([position_z, position_x, position_y]):
            self._transports += [
                LiquidHandle.builders.transport(
                    mode_params=LiquidHandle.builders.mode_params(
                        position_x=position_x,
                        position_y=position_y,
                        position_z=position_z,
                    )
                )
            ]

        followup_z = self._get_followup_z(position_z)

        return followup_z

    def _move_to_well_top_before_lld(self, position_z):
        """If position_z contains any liquid sensing moves to well top

        Parameters
        ----------
        position_z : dict
            position_z to be checked for lld events
        """
        well_top_z = LiquidHandle.builders.transport(
            mode_params=LiquidHandle.builders.mode_params(
                position_z=LiquidHandle.builders.position_z(reference="well_top")
            )
        )

        if position_z:
            if position_z.get("reference") == "liquid_surface":
                if position_z.get("detection", {}).get("method") != "tracked":
                    self._transports.append(well_top_z)

    @staticmethod
    def _get_followup_z(position_z):
        """Generates a position_z that references preceding position/tracked

        Generates a position_z to followup after the specified one. If the
        liquid surface is referenced, then returns a position that similarly
        tracks the surface. Otherwise, generates a reference to the preceding
        position.

        Parameters
        ----------
        position_z : dict
            position to be referenced when deciding on a followup position

        Returns
        -------
        dict
            position_z to follow up at a non-sensing position
        """
        preceding_z = LiquidHandle.builders.position_z(reference="preceding_position")
        if not position_z:
            followup_z = preceding_z
        elif position_z["reference"] == "liquid_surface":
            followup_z = LiquidHandle.builders.position_z(
                reference="liquid_surface",
                offset=position_z.get("offset"),
                detection_method="tracked",
            )
        else:
            followup_z = preceding_z

        return followup_z

    def _transport_pre_buffer(self, volume):
        """Aspirates a pre buffer of air volume above the source location

        Parameters
        ----------
        volume : Unit

        See Also
        --------
        _calculate_pre_buffer : determines pre_buffer volume to aspirate
        _transport_blowout : the corresponding air dispense step
        """
        pre_buffer = self._calculate_pre_buffer(volume)
        if pre_buffer:
            pre_buffer = parse_unit(pre_buffer, "uL")
            self._aspirate_simple(
                volume=pre_buffer,
                initial_z=LiquidHandle.builders.position_z(
                    reference="well_top", offset="1:mm"
                ),
                liquid_class="air",
            )

    def _calculate_pre_buffer(self, volume):
        """Calculates a recommended pre_buffer volume

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        Unit
            pre_buffer volume

        See Also
        --------
        _transport_pre_buffer : generates the actual pre_buffer transports
        """
        if self.blowout is True:
            blowout = self.default_blowout(volume)
        elif self.blowout is False:
            blowout = {}
        else:
            blowout = self.blowout

        return blowout.get("volume", Unit("0:uL"))

    def _transport_blowout(self, volume):
        """Blows out air volume above the destination location

        Parameters
        ----------
        volume : Unit
            liquid handling volume

        See Also
        --------
        blowout : holds any user specified blowout parameters
        default_blowout : specifies default blowout parameters
        _transport_pre_buffer : the corresponding air aspirate step
        """
        if self.blowout is True:
            blowout = self.default_blowout(volume)
        elif self.blowout is False:
            blowout = False
        else:
            blowout = self.blowout

        if blowout is not False:
            blowout_params = LiquidHandle.builders.blowout(**blowout)
            self._dispense_simple(liquid_class="air", **blowout_params)

    def default_blowout(self, volume):
        """Default blowout behavior

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        dict
            blowout_params

        See Also
        --------
        blowout : holds any user specified blowout parameters
        _transport_blowout : generates the actual blowout transports
        """
        raise NotImplementedError

    @staticmethod
    def default_lld_position_z(liquid):
        """Default lld position_z

        Returns
        -------
        dict
            position_z for sensing the liquid surface
        """
        # TODO: Select thresholds in some order
        return LiquidHandle.builders.position_z(
            reference="liquid_surface",
            offset="-1:mm",
            detection_method="capacitance",
            detection_threshold=liquid.clld_threshold,
        )

    @staticmethod
    def default_tracked_position_z():
        """Default tracked position_z

        Returns
        -------
        dict
            position_z for tracking the liquid surface
        """
        return LiquidHandle.builders.position_z(
            reference="liquid_surface", detection_method="tracked", offset="-1:mm"
        )

    @staticmethod
    def default_well_bottom_position_z():
        """Default well bottom position_z

        Returns
        -------
        dict
            position_z for the well bottom
        """
        return LiquidHandle.builders.position_z(reference="well_bottom")

    @staticmethod
    def default_well_top_position_z():
        """Default well top position_z

        Returns
        -------
        dict
            position_z for the well top
        """
        return LiquidHandle.builders.position_z(reference="well_top")
