"""Dispense LiquidHandleMethod

Base LiquidHandleMethod used by Protocol.liquid_handle_dispense to generate a
series of movements that define a dispense from a source into a destination
"""
from typing import List, Optional, Union

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
        self._set_prime(prime)
        self._set_predispense(predispense)

        # LiquidHandle parameters that are generated and modified at runtime
        self._liquid = None

    def _set_predispense(self, predispense: Union[Unit, str, bool]) -> None:
        if isinstance(predispense, Unit):
            self.predispense = predispense
        elif isinstance(predispense, str):
            self.predispense = parse_unit(predispense, "ul")
        else:
            if predispense:
                self.predispense = Dispense.default_predispense()
            else:
                self.predispense = Unit("0:microliter")

    def _set_prime(self, prime: Union[Unit, str, bool]) -> None:
        if isinstance(prime, Unit):
            self.prime = prime
        elif isinstance(prime, str):
            self.prime = parse_unit(prime, "ul")
        else:
            if prime:
                self.prime = Dispense.default_prime()
            else:
                self.prime = Unit("0:microliter")

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

    def _aspirate_transports(self, volume: Unit) -> List[dict]:
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
        total_aspirate_volume: Unit = parse_unit(volume, "ul")
        if self.prime:
            total_aspirate_volume += self.get_prime_volume()
        if self.predispense:
            total_aspirate_volume += self.get_predispense_volume()

        self._transport_aspirate_target_volume(total_aspirate_volume)
        return self._transports

    def _dispense_transports(self, volume: Unit) -> List[dict]:
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
        volume = parse_unit(volume, "ul")
        self._transport_dispense_target_volume(volume)
        return self._transports

    def _prime_transports(self, volume: Optional[Unit] = None) -> List[dict]:
        """Generates transports for priming volume back into the source location

        Generates all the transports that should happen to recirculate volume
        from the source aliquot back into itself

        Parameters
        ----------
        volume: Optional[Unit]

        Returns
        -------
        list
            priming transports
        """
        self._transports = []
        if not volume:
            self._transport_dispense_target_volume(self.get_prime_volume())
        else:
            volume = parse_unit(volume, "ul")

            # No transports if no volume specified
            if volume == Unit("0:ul"):
                return self._transports

            self._transport_dispense_target_volume(volume)

        return self._transports

    def _predispense_transports(self, volume: Optional[Unit] = None) -> List[dict]:
        """Generates transports for predispensing volume back into waste

        Generates all the transports that should happen to dispense volume into
        waste before dispensing into the destination aliquots.
        This is used to clear any residual air gaps out of the dispenser.

        Parameters
        ----------
        volume: Optional[Unit]

        Returns
        -------
        list
            predispense transports
        """
        self._transports = []

        if not volume:
            self._transport_dispense_target_volume(self.get_predispense_volume())
        else:
            volume = parse_unit(volume, "ul")

            # No transports if no volume specified
            if volume == Unit("0:ul"):
                return self._transports

            self._transport_dispense_target_volume(volume)

        return self._transports

    def get_prime_volume(self) -> Unit:
        return self.prime

    def get_predispense_volume(self) -> Unit:
        return self.predispense

    # pylint: disable=unused-argument, redundant-returns-doc
    @staticmethod
    def default_volume_resolution(volume: Unit) -> None:
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
    def default_prime(volume: Optional[Unit] = Unit(600, "uL")) -> Unit:
        """Default priming volume

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        Unit
            prime volume
        """
        return parse_unit(volume, "ul")

    # pylint: disable=unused-argument
    @staticmethod
    def default_predispense(volume: Optional[Unit] = Unit(10, "uL")) -> Unit:
        """Default predispense volume

        Parameters
        ----------
        volume : Unit

        Returns
        -------
        Unit
            predispense volume
        """
        return parse_unit(volume, "ul")

    def default_blowout(self, volume):
        pass

    def _calculate_overage_volume(self, volume):
        pass

    def _has_calibration(self):
        pass
