"""Dispense LiquidHandleMethod

Base LiquidHandleMethod used by Protocol.liquid_handle_dispense to generate a
series of movements that define a dispense from a source into a destination
"""

from ..instruction import LiquidHandle
from ..unit import Unit
from ..util import parse_unit
from .liquid_handle_method import LiquidHandleMethod


# pylint: disable=protected-access
class Dispense(LiquidHandleMethod):
    """LiquidHandleMethod for generating dispense transports

    LiquidHandleMethod for moving volume from a source well to destination wells

    Attributes
    ----------
    _liquid : LiquidClass
        used to determine parameters specific to a given type of liquid

    Notes
    -----
    The primary entry points that for this class are:
        - _aspirate_transports : generates transports from a source location
        - _prime_transports : generates transports into the priming location
                              (back into the source location or into waste)
                              for the purpose of moving the liquid-air interface
                              to the dispensing head
        - _predispense_transports : generates transports to a disposal location
        - _dispense_transports : generates transports for a destination location

    See Also
    --------
    LiquidHandleMethod : base LiquidHandleMethod with reused functionality
    """

    def __init__(self, volume_resolution=None, prime=True, predispense=True):
        super(Dispense, self).__init__()

        # parameters for required behavior
        self.volume_resolution = volume_resolution

        # parameters for optional behavior
        self.prime = prime
        self.predispense = predispense

        # LiquidHandle parameters that are generated and modified at runtime
        self._liquid = None

    def _transport_aspirate_target_volume(self, volume):
        volume_resolution = self.volume_resolution or self.default_volume_resolution(
            volume
        )

        self._transports.append(
            LiquidHandle.builders.transport(
                volume=-volume,
                mode_params=LiquidHandle.builders.mode_params(
                    volume_resolution=volume_resolution, liquid_class=self._liquid.name
                ),
            )
        )

    def _transport_dispense_target_volume(self, volume):
        volume_resolution = self.volume_resolution or self.default_volume_resolution(
            volume
        )

        self._transports.append(
            LiquidHandle.builders.transport(
                volume=volume,
                mode_params=LiquidHandle.builders.mode_params(
                    volume_resolution=volume_resolution, liquid_class=self._liquid.name
                ),
            )
        )

    def _aspirate_transports(self, volume):
        """Generates source well transports

        Generates all the transports that should happen to aspirate volume from
        the source aliquot

        Parameters
        ----------
        volume: Unit

        Returns
        -------
        list
            source well transports corresponding to the aspirate operation
        """
        self._transports = []
        volume = parse_unit(Unit(volume), "ul")
        self._transport_aspirate_target_volume(volume)
        return self._transports

    def _dispense_transports(self, volume):
        """Generates destination well transports

        Generates all the transports that should happen to dispense volume into
        the destination aliquot

        Parameters
        ----------
        volume: Unit

        Returns
        -------
        list
            destination well transports corresponding to the dispense operation
        """
        self._transports = []
        volume = parse_unit(Unit(volume), "ul")
        self._transport_dispense_target_volume(volume)
        return self._transports

    def _prime_transports(self, volume):
        """Generates transports for priming volume back into the source location

        Generates all the transports that should happen to recirculate volume
        from the source aliquot back into itself

        Parameters
        ----------
        volume: Unit

        Returns
        -------
        list
            priming transports
        """
        self._transports = []
        volume = parse_unit(Unit(volume), "ul")

        # No transports if no volume specified
        if volume == Unit("0:ul"):
            return []

        self._transport_dispense_target_volume(volume)

        return self._transports

    def _predispense_transports(self, volume):
        """Generates transports for predispensing volume back into waste

        Generates all the transports that should happen to dispense volume into
        waste before dispensing into the destination aliquots.
        This is used to clear any residual air gaps out of the dispenser.

        Parameters
        ----------
        volume: Unit

        Returns
        -------
        list
            predispense transports
        """
        self._transports = []
        volume = parse_unit(Unit(volume), "ul")

        # No transports if no volume specified
        if volume == Unit("0:ul"):
            return []

        self._transport_dispense_target_volume(volume)

        return self._transports

    # pylint: disable=unused-argument, redundant-returns-doc
    @staticmethod
    def default_volume_resolution(volume):
        """Default volume_resolution parameters

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        Unit or None
            volume_resolution

        See Also
        --------
        volume_resolution : holds any user defined volume resolution parameters
        _transport_aspirate_target_volume : generates aspirate transports
        _transport_dispense_target_volume : generates dispense transports
        """
        return None

    # pylint: disable=unused-argument
    @staticmethod
    def default_prime(volume):
        """Default priming volume

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        Unit
            prime volume
        """
        return Unit(600, "uL")

    # pylint: disable=unused-argument
    @staticmethod
    def default_predispense(volume):
        """Default predispense volume

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        Unit
            predispense volume
        """
        return Unit(10, "uL")

    def default_blowout(self, volume):
        pass

    def _calculate_overage_volume(self, volume):
        pass

    def _has_calibration(self):
        pass
