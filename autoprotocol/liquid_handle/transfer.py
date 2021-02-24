"""Transfer LiquidHandleMethod

    :copyright: 2021 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

Base LiquidHandleMethod used by Protocol.transfer to generate a series of
movements between pairs of wells.
"""
from ..instruction import LiquidHandle
from ..unit import Unit
from ..util import parse_unit
from .liquid_handle_method import LiquidHandleMethod


# pylint: disable=unused-argument,too-many-instance-attributes,protected-access
class Transfer(LiquidHandleMethod):
    """LiquidHandleMethod for generating transfers between pairs of wells

    LiquidHandleMethod for transferring volume from one well to another.

    Attributes
    ----------
    _source_liquid : LiquidClass
        used to determine calibration, flowrates, and sensing thresholds
    _destination_liquid : LiquidClass
        used to determine calibration, flowrates, and sensing thresholds

    Notes
    -----
    The primary entry points that for this class are:
        - _aspirate_transports : generates transports for a source location
        - _dispense_transports : generates transports for a destination location


    See Also
    --------
    LiquidHandleMethod : base LiquidHandleMethod with reused functionality
    Protocol.transfer : the standard interface for interacting with Transfer
    """

    def __init__(
        self,
        tip_type=None,
        blowout=True,
        prime=True,
        transit=True,
        mix_before=False,
        mix_after=True,
        aspirate_z=None,
        dispense_z=None,
    ):
        """
        Parameters
        ----------
        tip_type : str, optional
            tip_type to be used for the LiquidHandlingMethod
        blowout : bool or dict, optional
            whether to execute a blowout step or the parameters for one.
            this generates a pair of operations: an initial air aspiration
            before entering any wells and a corresponding air dispense after the
            last operation that involves liquid
            See Also LiquidHandle.builders.blowout
        prime : bool or Unit, optional
            whether to execute a prime step or the parameters for one.
            this generates a pair of aspirate/dispense operations around the
            aspiration step in the sequence:
            aspirate_prime -> aspirate_target_volume -> dispense_prime
        transit : bool or Unit, optional
            whether to execute a transit step or the parameters for one.
            this generates a pair of operations wherein air is aspirated just
            before leaving the source location and dispensed immediately
            after reaching the destination location
        mix_before : bool or dict, optional
            whether to execute a mix_before step or the parameters for one.
            this generates a series of aspirate and dispense steps within the
            source location before aspirating the target volume
            See Also LiquidHandle.builders.mix
        mix_after : bool or dict, optional
            whether to execute a mix_after step or the parameters for one.
            this generates a series of aspirate and dispense steps within the
            destination location after dispensing the target volume
            See Also LiquidHandle.builders.mix
        aspirate_z : dict, optional
            the position that the tip should move to prior to aspirating, if the
            position references the `liquid_surface` then aspirate movements
            will track the surface with the defined offset.
            See Also LiquidHandle.builders.position_z
        dispense_z : dict, optional
            the position that the tip should move to prior to dispensing, if the
            position references the `liquid_surface` then dispense
            will track the surface with the defined offset.
            See Also LiquidHandle.builders.position_z
        """
        super(Transfer, self).__init__(tip_type=tip_type, blowout=blowout)

        # parameters for required behavior
        self.aspirate_z = aspirate_z
        self.dispense_z = dispense_z

        # parameters for optional behavior
        self.prime = prime
        self.transit = transit
        self.mix_before = mix_before
        self.mix_after = mix_after

        # LiquidHandle parameters that are generated and modified at runtime
        self._source_liquid = None
        self._destination_liquid = None

    def _has_calibration(self):
        liquids = [self._source_liquid, self._destination_liquid]
        return any(_ and _._has_calibration() for _ in liquids)

    def _calculate_overage_volume(self, volume):
        calibration_overage = (
            self._estimate_calibrated_volume(volume, self._source_liquid, self.tip_type)
            - volume
        )

        # handle whichever is larger, prime or transit volume
        if self.prime is True:
            prime = self.default_prime(volume)
        elif self.prime is False:
            prime = Unit(0, "uL")
        else:
            prime = self.prime

        if self.transit is True:
            transit = self.default_transit(volume)
        elif self.transit is False:
            transit = Unit(0, "uL")
        else:
            transit = self.transit

        prime_or_transit = max([prime, transit])

        return calibration_overage + prime_or_transit

    def default_blowout(self, volume):
        if self._is_single_channel():
            if volume < Unit("10:ul"):
                blowout_vol = Unit("5:ul")
            elif volume < Unit("25:ul"):
                blowout_vol = Unit("10:ul")
            elif volume < Unit("75:ul"):
                blowout_vol = Unit("15:ul")
            elif volume < Unit("100:ul"):
                blowout_vol = Unit("20:ul")
            else:
                blowout_vol = Unit("25:ul")
        else:
            blowout_vol = Unit("5:ul")

        return LiquidHandle.builders.blowout(
            volume=blowout_vol,
            initial_z=self.default_well_top_position_z(),
            flowrate=None,
        )

    def _aspirate_transports(self, volume, density):
        """Generates source well transports

        Generates and returns all of the transports that should happen within
        the source well of a transfer operation.

        Calls a series of _transport_`y` helper methods that each query the `y`
        parameter and default_`y` method to decide on a set of behavior and use
        that to define transports that are appended to the _transports list.

        Parameters
        ----------
        volume : Unit

        Return
        ------
        list
            source well transports corresponding to the aspirate operation

        Notes
        -----
        This method defines what lower level transport-generating methods are
        called and in what order. It can be overwritten when adding an
        entirely new set of transport-generating behavior.

        See Also
        --------
        _dispense_transports : corresponding destination well method
        """
        self._transports = []
        volume = parse_unit(Unit(volume), "ul")

        # No transports if no volume specified
        if volume == Unit("0:ul"):
            return []

        self._transport_pre_buffer(volume)
        self._transport_mix_before(volume)
        self._transport_aspirate_target_volume(volume, density)
        self._transport_aspirate_transit(volume)

        return self._transports

    def _dispense_transports(self, volume, density):
        """Generates destination well transports

        Generates and returns all of the transports that should happen within
        the destination well of a transfer operation.

        Calls a series of _transport_`y` helper methods that each query the `y`
        parameter and default_`y` method to decide on a set of behavior and use
        that to define transports that are appended to the _transports list.

        Parameters
        ----------
        volume : Unit

        Return
        ------
        list
            destination well transports corresponding to the dispense operation

        Notes
        -----
        This method defines what lower level transport-generating methods are
        called and in what order. It can be overwritten when adding an
        entirely new set of transport-generating behavior.

        See Also
        --------
        _aspirate_transports : corresponding source well method
        """
        self._transports = []
        volume = parse_unit(volume, "ul")

        # No transports if no volume specified
        if volume == Unit("0:ul"):
            return []

        self._transport_dispense_transit(volume)
        self._transport_dispense_target_volume(volume, density)
        self._transport_mix_after(volume)
        self._transport_blowout(volume)

        return self._transports

    def _transport_mix_before(self, volume):
        """Mixes volume in the source well before aspirating

        Parameters
        ----------
        volume : Unit

        See Also
        --------
        mix_before : holds any user defined mix_before parameters
        default_mix_before : specifies default mix_before parameters
        _mix : lower level helper that generates the mix_before transports
        """
        if self.mix_before is True:
            mix_before = self.default_mix_before(volume)
        elif self.mix_before is False:
            mix_before = False
        else:
            mix_before = self.mix_before

        if mix_before is not False:
            mix_before = LiquidHandle.builders.mix(**mix_before)
            self._mix(
                delay_time=self._source_liquid.delay_time,
                liquid_class=self._source_liquid.name,
                **mix_before
            )

    def default_mix_before(self, volume):
        """Default mix_before parameters

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        dict
            mix_before params

        See Also
        --------
        mix_before : holds any user defined mix_before parameters
        _transport_mix : generates the actual mix_before transports
        """
        if self._is_single_channel():
            mix_z = self.default_lld_position_z(liquid=self._source_liquid)
        else:
            mix_z = self.default_well_bottom_position_z()

        return LiquidHandle.builders.mix(
            volume=volume,
            repetitions=10,
            initial_z=mix_z,
            asp_flowrate=self._source_liquid._get_aspirate_flowrate(
                volume, self.tip_type
            ),
            dsp_flowrate=self._source_liquid._get_dispense_flowrate(
                volume, self.tip_type
            ),
        )

    def _transport_aspirate_target_volume(self, volume, density):
        """Aspirates the target volume from the source location

        Parameters
        ----------
        volume : Unit
        density : Unit

        See Also
        --------
        aspirate_z : holds any user defined aspirate_z parameters
        default_aspirate_z : specifies default aspirate_z parameters
        prime : holds any user defined prime volume
        default_prime : specifies default prime volume
        _aspirate_simple : lower level helper that generates aspirate transports
        _aspirate_with_prime : lower level helper for aspirating with priming
        """
        aspirate_z = self.aspirate_z or self.default_aspirate_z(volume)

        if self.prime is True:
            prime = self.default_prime(volume)
        elif self.prime is False:
            prime = False
        else:
            prime = self.prime

        aspirate_z = LiquidHandle.builders.position_z(**aspirate_z)
        if prime is not False:
            prime = parse_unit(prime, "uL")
            self._aspirate_with_prime(
                volume=volume,
                prime_vol=prime,
                calibrated_vol=self._source_liquid._get_calibrated_volume(
                    volume, self.tip_type
                ),
                initial_z=aspirate_z,
                asp_flowrate=self._source_liquid._get_aspirate_flowrate(
                    volume, self.tip_type
                ),
                dsp_flowrate=self._source_liquid._get_dispense_flowrate(
                    volume, self.tip_type
                ),
                delay_time=self._source_liquid.delay_time,
                liquid_class=self._source_liquid.name,
                density=density,
            )
        else:
            self._aspirate_simple(
                volume=volume,
                calibrated_vol=self._source_liquid._get_calibrated_volume(
                    volume, self.tip_type
                ),
                initial_z=aspirate_z,
                flowrate=self._source_liquid._get_aspirate_flowrate(
                    volume, self.tip_type
                ),
                delay_time=self._source_liquid.delay_time,
                liquid_class=self._source_liquid.name,
                density=density,
            )

    def default_aspirate_z(self, volume):
        """Default aspirate_z parameters

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        dict
            aspirate position_z

        See Also
        --------
        aspirate_z : holds any user defined aspirate_z parameters
        _transport_aspirate_target_volume : generates actual aspirate transports
        """
        if self._is_single_channel():
            aspirate_z = self.default_lld_position_z(liquid=self._source_liquid)
        else:
            aspirate_z = self.default_well_bottom_position_z()
        return aspirate_z

    # pylint: disable=no-self-use
    def default_prime(self, volume):
        """Default prime volume

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        Unit
            priming volume

        See Also
        --------
        prime : holds any user defined prime volume
        _transport_aspirate_target_volume : generates actual aspirate transports
        """
        return Unit(5, "ul")

    def _transport_aspirate_transit(self, volume):
        """Aspirates air above the source before moving to the destination

        Parameters
        ----------
        volume : Unit

        See Also
        --------
        transit : holds any user defined transit volume
        default_transit : specifies default transit volume
        _transport_dispense_transit : the corresponding air dispense step
        """
        if self.transit is True:
            transit = self.default_transit(volume)
        elif self.transit is False:
            transit = False
        else:
            transit = self.transit

        if transit is not False:
            transit_vol = parse_unit(transit, "uL")
            self._aspirate_simple(
                volume=transit_vol,
                initial_z=self.default_well_top_position_z(),
                liquid_class="air",
            )

    def _transport_dispense_transit(self, volume):
        """Dispenses air above the destination after moving from the source

        Parameters
        ----------
        volume : Unit

        See Also
        --------
        transit : holds any user defined transit volume
        default_transit : specifies default transit volume
        _transport_aspirate_transit : the corresponding air aspirate step
        """
        if self.transit is True:
            transit = self.default_transit(volume)
        elif self.transit is False:
            transit = False
        else:
            transit = self.transit

        if transit is not False:
            transit_vol = parse_unit(transit, "uL")
            self._dispense_simple(
                volume=transit_vol,
                initial_z=self.default_well_top_position_z(),
                liquid_class="air",
            )

    def default_transit(self, volume):
        """Default transit volume

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        Unit
            transit volume

        See Also
        --------
        transit : holds any user defined transit volume
        _transport_aspirate_transit : generates the actual transit transports
        _transport_dispense_transit : generates the actual transit transports
        """
        if self._is_single_channel():
            transit_vol = Unit("2:ul")
        else:
            transit_vol = Unit("1:ul")

        return transit_vol

    def _transport_dispense_target_volume(self, volume, density):
        """Dispenses the target volume into the destination location

        Parameters
        ----------
        volume : Unit
        density : Unit

        See Also
        --------
        dispense_z : holds any user defined dispense_z parameters
        default_dispense_z : specifies default dispense_z parameters
        _dispense_simple : lower level helper that generates dispense transports
        """
        dispense_z = self.dispense_z or self.default_dispense_z(volume)

        dispense_z = LiquidHandle.builders.position_z(**dispense_z)
        self._dispense_simple(
            volume=volume,
            calibrated_vol=self._source_liquid._get_calibrated_volume(
                volume, self.tip_type
            ),
            initial_z=dispense_z,
            flowrate=self._source_liquid._get_dispense_flowrate(volume, self.tip_type),
            delay_time=self._source_liquid.delay_time,
            liquid_class=self._source_liquid.name,
            density=density,
        )

    def default_dispense_z(self, volume):
        """Default aspirate_z parameters

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        dict
            dispense position_z

        See Also
        --------
        dispense_z : holds any user defined dispense_z parameters
        _transport_dispense_target_volume : generates actual dispense transports
        """
        if self._is_single_channel():
            dispense_z = self.default_lld_position_z(liquid=self._destination_liquid)
        else:
            dispense_z = self.default_tracked_position_z()

        return dispense_z

    def _transport_mix_after(self, volume):
        """Mixes volume in the destination well after dispensing

        Parameters
        ----------
        volume : Unit

        See Also
        --------
        mix_after : holds any user defined mix_after parameters
        default_mix_after : specifies default mix_after parameters
        _mix : lower level helper that generates the mix_after transports
        """
        if self.mix_after is True:
            mix_after = self.default_mix_after(volume)
        elif self.mix_after is False:
            mix_after = False
        else:
            mix_after = self.mix_after

        if mix_after is not False:
            mix_after = LiquidHandle.builders.mix(**mix_after)
            self._mix(
                delay_time=self._source_liquid.delay_time,
                liquid_class=self._source_liquid.name,
                **mix_after
            )

    def default_mix_after(self, volume):
        """Default mix_after parameters

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        dict
            mix_after params

        See Also
        --------
        mix_after : holds any user defined mix_after parameters
        _transport_mix : generates the actual mix_after transports
        """
        if self._is_single_channel():
            mix_z = self.default_lld_position_z(liquid=self._destination_liquid)
        else:
            mix_z = self.default_well_bottom_position_z()

        return LiquidHandle.builders.mix(
            volume=volume,
            repetitions=10,
            initial_z=mix_z,
            asp_flowrate=self._source_liquid._get_aspirate_flowrate(
                volume, self.tip_type
            ),
            dsp_flowrate=self._source_liquid._get_dispense_flowrate(
                volume, self.tip_type
            ),
        )


class DryWellTransfer(Transfer):
    """Dispenses while tracking liquid without mix_after"""

    def __init__(
        self,
        tip_type=None,
        blowout=True,
        prime=True,
        transit=True,
        mix_before=False,
        mix_after=False,
        aspirate_z=None,
        dispense_z=None,
    ):
        super(DryWellTransfer, self).__init__(
            tip_type=tip_type,
            blowout=blowout,
            prime=prime,
            transit=transit,
            mix_before=mix_before,
            mix_after=mix_after,
            aspirate_z=aspirate_z,
            dispense_z=dispense_z,
        )

    def default_dispense_z(self, volume):
        return self.default_tracked_position_z()


class PreMixBlowoutTransfer(Transfer):
    """Adds an additional blowout before the mix_after step"""

    def __init__(
        self,
        tip_type=None,
        blowout=True,
        prime=True,
        transit=True,
        mix_before=False,
        mix_after=True,
        aspirate_z=None,
        dispense_z=None,
        pre_mix_blowout=True,
    ):
        super(PreMixBlowoutTransfer, self).__init__(
            tip_type=tip_type,
            blowout=blowout,
            prime=prime,
            transit=transit,
            mix_before=mix_before,
            mix_after=mix_after,
            aspirate_z=aspirate_z,
            dispense_z=dispense_z,
        )
        self.pre_mix_blowout = pre_mix_blowout

    def _dispense_transports(self, volume=None, density=None):
        self._transports = []
        volume = parse_unit(volume, "ul")

        # No transports if no volume specified
        if volume == Unit("0:ul"):
            return []

        self._transport_dispense_transit(volume)
        self._transport_dispense_target_volume(volume, density)
        self._transport_pre_mix_blowout(volume)
        self._transport_mix_after(volume)
        self._transport_blowout(volume)

        return self._transports

    def _calculate_pre_buffer(self, volume):
        if self.blowout is True:
            blowout = self.default_blowout(volume)
        elif self.blowout is False:
            blowout = {}
        else:
            blowout = self.blowout

        if self.pre_mix_blowout is True:
            secondary_blowout = self.default_pre_mix_blowout(volume)
        elif self.pre_mix_blowout is False:
            secondary_blowout = {}
        else:
            secondary_blowout = self.pre_mix_blowout

        blowout_vol = parse_unit(blowout.get("volume", Unit("0:uL")), "uL")
        secondary_blowout_vol = parse_unit(
            secondary_blowout.get("volume", Unit("0:uL")), "uL"
        )

        return blowout_vol + secondary_blowout_vol

    def _transport_pre_mix_blowout(self, volume):
        """Dispenses a secondary air volume befiore the mix_after step

        Notes
        -----
        For some liquid classes this has resulted in more complete dispensing of
        the target volume than just a single blowout.

        Parameters
        ----------
        volume : Unit

        See Also
        --------
        pre_mix_blowout : holds any user defined pre_mix_blowout parameters
        default_pre_mix_blowout : specifies default pre_mix_blowout parameters
        """
        if self.pre_mix_blowout is True:
            pre_mix_blowout = self.default_pre_mix_blowout(volume)
        elif self.pre_mix_blowout is False:
            pre_mix_blowout = False
        else:
            pre_mix_blowout = self.pre_mix_blowout

        if pre_mix_blowout is not False:
            pre_mix_blowout = LiquidHandle.builders.blowout(**pre_mix_blowout)
            self._dispense_simple(liquid_class="air", **pre_mix_blowout)

    def default_pre_mix_blowout(self, volume):
        """Default pre_mix_blowout parameters

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        dict
            pre_mix_blowout params

        See Also
        --------
        pre_mix_blowout : holds any user defined pre_mix_blowout parameters
        _transport_pre_mix_blowout : generates the actual blowout transports
        """
        return LiquidHandle.builders.blowout(
            volume=Unit(5, "ul"),
            initial_z=self.default_well_top_position_z(),
            flowrate=None,
        )
