"""Mix LiquidHandleMethod

Base LiquidHandleMethod used by Protocol.mix to generate a series of
movements within individual wells.

    :copyright: 2020 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details
"""
from .transfer import LiquidHandleMethod
from ..instruction import LiquidHandle
from ..unit import Unit
from ..util import parse_unit


# pylint: disable=protected-access
class Mix(LiquidHandleMethod):
    """LiquidHandleMethod for generating transfers within wells

    LiquidHandleMethod for moving volume within a single well.

    Attributes
    ----------
    _liquid : LiquidClass
        used to determine calibration, flowrates, and sensing thresholds

    Notes
    -----
    The primary entry points that for this class are:
        - _mix_transports : generates transports within a single location

    See Also
    --------
    LiquidHandleMethod : base LiquidHandleMethod with reused functionality
    Protocol.mix : the standard interface for interacting with Mix
    """

    def __init__(self, tip_type=None, blowout=True, repetitions=None, position_z=None):
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
        repetitions : int
            the number of times the mix should be repeated
        position_z : dict
            the position that the tip should move to prior to mixing, if the
            position references the `liquid_surface` then mix movements will
            track the surface with the defined offset.
            See Also LiquidHandle.builders.position_z
        """
        super(Mix, self).__init__(tip_type=tip_type, blowout=blowout)

        # parameters for required behavior
        self.repetitions = repetitions
        self.position_z = position_z

        # LiquidHandle parameters that are generated and modified at runtime
        self._liquid = None

    def _has_calibration(self):
        liquids = [self._liquid]
        return any(_ and _._has_calibration() for _ in liquids)

    def _calculate_overage_volume(self, volume):
        calibration_overage = (
            self._estimate_calibrated_volume(volume, self._liquid, self.tip_type)
            - volume
        )

        return calibration_overage

    def default_blowout(self, volume):
        return LiquidHandle.builders.blowout(
            volume=Unit("5:ul"),
            initial_z=self.default_well_top_position_z(),
            flowrate=None,
        )

    def _mix_transports(self, volume):
        """Generates mix transports

        Generates and returns all of the transports that should happen within
        the well of a mix operation.

        Calls a series of _transport_`y` helper methods that each query the `y`
        parameter and default_`y` method to decide on a set of behavior and use
        that to define transports that are appended to the _transports list.

        Parameters
        ----------
        volume : Unit

        Notes
        -----
        This method defines what lower level transport-generating methods are
        called and in what order. It can be overwritten when adding an
        entirely new set of transport-generating behavior.

        Return
        ------
        list
            transports corresponding to the mix operation
        """
        self._transports = []
        volume = parse_unit(volume, "ul")

        # No transports if no volume specified
        if volume == Unit("0:ul"):
            return []

        self._transport_pre_buffer(volume)
        self._transport_mix(volume)
        self._transport_blowout(volume)

        return self._transports

    def _transport_mix(self, volume):
        """Mixes the volume

        Parameters
        ----------
        volume : Unit

        Raises
        ------
        TypeError
            if mix repetitions is not an int

        See Also
        --------
        repetitions : holds any user defined repetition parameters
        default_repetitions : specifies default repetition parameters
        position_z : holds any user defined position_z parameters
        default_position_z : specifies default position_z parameters
        _mix : lower level helper that generates the mix transports
        """
        repetitions = self.repetitions or self.default_repetitions(volume)
        position_z = self.position_z or self.default_position_z(volume)

        if not isinstance(repetitions, int):
            raise TypeError(f"Mix repetitions {repetitions} was not an int.")
        position_z = LiquidHandle.builders.position_z(**position_z)
        self._mix(
            volume=volume,
            repetitions=repetitions,
            initial_z=position_z,
            asp_flowrate=self._liquid._get_aspirate_flowrate(volume, self.tip_type),
            dsp_flowrate=self._liquid._get_dispense_flowrate(volume, self.tip_type),
            delay_time=self._liquid.delay_time,
            liquid_class=self._liquid.name,
        )

    # pylint: disable=unused-argument
    def default_repetitions(self, volume):
        """Default mix repetitions

        Parameters
        ----------
        volume: Unit

        Returns
        -------
        int
            number of mix repetitions

        See Also
        --------
        repetitions : holds any user defined repetition parameters
        _transport_mix : generates the actual mix transports
        """
        return 10

    # pylint: disable=unused-argument
    def default_position_z(self, volume):
        """Default position_z

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        dict
            mix position_z

        See Also
        --------
        position_z : holds any user defined position_z parameters
        _transport_mix : generates the actual mix transports
        """
        if self._is_single_channel():
            position_z = self.default_lld_position_z(self._liquid)
        else:
            position_z = self.default_well_bottom_position_z()
        return position_z
