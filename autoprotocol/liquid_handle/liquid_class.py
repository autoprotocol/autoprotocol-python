"""LiquidClass

Base class for defining the portions of liquid handling behavior that are
intrinsic to specific types of liquids.

    :copyright: 2021 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""
from collections import namedtuple
from numbers import Number

from ..util import parse_unit


# pylint: disable=too-many-instance-attributes,too-few-public-methods
class LiquidClass(object):
    """Contains properties intrinsic to individual LiquidClasses

    Attributes
    ----------
    name : str
        the name of the liquid_class may be used by vendors to generate more
        sensible defaults for unspecified behavior
    volume_calibration_curve : dict(str, VolumeCalibration)
        a calibration curve describing the relationship between tip_type,
        volume bins, and volume calibration parameters
        See Also VolumeCalibration
    aspirate_flowrate_calibration_curve : dict(str, VolumeCalibration)
        a calibration curve describing the relationship between tip_type,
        volume bins, and aspirate flowrate calibration parameters
        See Also VolumeCalibration
    dispense_flowrate_calibration_curve : dict(str, VolumeCalibration)
        a calibration curve describing the relationship between tip_type,
        volume bins, and dispense flowrate calibration parameters
        See Also VolumeCalibration
    _safe_volume_multiplier: Numeric
        a multiplier used by LiquidHandleMethods to estimate safe pump buffers
        for volume calibration without any prior knowledge about tip_type
        See Also LiquidHandleMethod._estimate_calibrated_volume

    Examples
    --------
    For specifying a single, global liquid handling behavior across all
    volumes the easiest way is to specify parameters when instantiating a
    LiquidClass. If the following LiquidClass is specified then the
    pump_override_volume will always be set to 10:uL and the flowrate for all
    aspirate steps will have a target of 10:uL/s, regardless of the stated
    volume to be transferred.

    .. code-block:: python

        from autoprotocol import Unit
        from autoprotocol.instruction import LiquidHandle
        from autoprotocol.liquid_handle import LiquidClass

        lc = LiquidClass(
            aspirate_flowrate=LiquidHandle.builders.flowrate(
                target=Unit(10, "ul/s")
            ),
            calibrated_volume=Unit(10, "uL")
        )

    For behavior that differs between volumes you can define your own
    LiquidClass.

    .. code-block:: python

        from autoprotocol import Unit
        from autoprotocol.instruction import LiquidHandle
        from autoprotocol.liquid_handle.liquid_class import (
            LiquidClass, VolumeCalibration, VolumeCalibrationBin
        )

        vol_curve = {
            "generic_1_50": VolumeCalibration(
                (Unit(5, "uL"), VolumeCalibrationBin(
                    slope=1.1, intercept=Unit(0.1, "uL")
                )),
                (Unit(10, "uL"), VolumeCalibrationBin(
                    slope=0.9, intercept=Unit(0.2, "uL")
                ))
            )
        }
        asp_flow_curve = {
            "generic_1_50": VolumeCalibration(
                (Unit(5, "uL"), LiquidHandle.builders.flowrate(
                    target=Unit(50, "uL/s")
                )),
                (Unit(15, "uL"), LiquidHandle.builders.flowrate(
                    target=Unit(200, "uL/s")
                ))
            )
        }

        class NewLC(LiquidClass):
            def __init__(self, *args, **kwargs):
                super(NewLC, self).__init__(*args, **kwargs)
                self.volume_calibration_curve = vol_curve
                self.aspirate_flowrate_calibration_curve = asp_flow_curve

    See Also
    --------
    VolumeCalibration : used to specify calibration_curves
    LiquidHandleMethod : used to specify liquid handling movement behavior
    Protocol.transfer : accepts LiquidClass arguments to determine behavior
    Protocol.mix : accepts a LiquidClass argument to determine behavior
    """

    def __init__(
        self,
        calibrated_volume=None,
        aspirate_flowrate=None,
        dispense_flowrate=None,
        delay_time=None,
        clld_threshold=None,
        plld_threshold=None,
    ):
        """
        Parameters
        ----------
        calibrated_volume : Unit, optional
            used to specify a calibrated volume, if not specified then will
            default to the calibration from `volume_calibration_curve`
        aspirate_flowrate : dict, optional
            used to specify an aspirate flowrate, if not specified then will
            default to the calibration using
            `aspirate_flowrate_calibration_curve`
        dispense_flowrate : dict, optional
            used to specify a dispense flowrate, if not specified then will
            default to the calibration using
            `dispense_flowrate_calibration_curve`
        delay_time : Unit, optional
            the amount of time to wait after each liquid handling step.
            this is helpful for cases such as pressure equilibration
        clld_threshold : Unit, optional
            the capacitive liquid level detection threshold
        plld_threshold : Unit, optional
            the pressure liquid level detection threshold
        """

        self.calibrated_volume = calibrated_volume
        self.aspirate_flowrate = aspirate_flowrate
        self.dispense_flowrate = dispense_flowrate
        self.delay_time = delay_time
        self.clld_threshold = clld_threshold
        self.plld_threshold = plld_threshold

        # Dicts of {tip_type: VolumeCalibration}
        self.volume_calibration_curve = None
        self.aspirate_flowrate_calibration_curve = None
        self.dispense_flowrate_calibration_curve = None

        # May be used by vendors to set defaults for different liquid classes
        self.name = None

        # Multiplier for volume when making calibrated volume estimates without
        # any volume_calibration_curve or prior tip type knowledge
        self._safe_volume_multiplier = 1.1

    def _has_calibration(self):
        """Checks whether any calibration attributes are specified

        Returns
        -------
        bool
            Whether there are any calibration attributes for this LiquidClass
        """
        return any(
            [
                self.calibrated_volume,
                self.aspirate_flowrate,
                self.dispense_flowrate,
                self.volume_calibration_curve,
                self.aspirate_flowrate_calibration_curve,
                self.dispense_flowrate_calibration_curve,
            ]
        )

    def _get_calibrated_volume(self, volume, tip_type):
        """Calculates the calibrated volume for a given volume and tip_type

        Parameters
        ----------
        volume : str or Unit
            Desired volume to be transferred into the target well
        tip_type: str
            liquid handling device to be used for the transfer

        Returns
        -------
        Unit
            calibrated volume
        """
        if self.calibrated_volume is not None:
            calibrated_volume = self.calibrated_volume
        elif self.volume_calibration_curve is not None:
            # pylint: disable=unsubscriptable-object
            calibration = self.volume_calibration_curve[tip_type]
            volume_calibration = calibration.binned_calibration_for_volume(volume)
            calibrated_volume = volume_calibration.calibrate_volume(volume)
        else:
            calibrated_volume = None
        return calibrated_volume

    def _get_aspirate_flowrate(self, volume, tip_type):
        """Returns recommended aspiration flowrate based on transfer volume

        Parameters
        ----------
        volume : str or Unit
            Desired volume to be transferred into the target well
        tip_type : str
            liquid handling device to be used for the transfer

        Returns
        -------
        dict
            flowrate params
        """
        if self.aspirate_flowrate is not None:
            flowrate = self.aspirate_flowrate
        elif self.aspirate_flowrate_calibration_curve is not None:
            # pylint: disable=unsubscriptable-object
            calibration = self.aspirate_flowrate_calibration_curve[tip_type]
            flowrate = calibration.binned_calibration_for_volume(volume)
        else:
            flowrate = None
        return flowrate

    def _get_dispense_flowrate(self, volume, tip_type):
        """Returns recommended aspiration flowrate based on transfer volume

        Parameters
        ----------
        volume : str or Unit
            Desired volume to be transferred into the target well
        tip_type : str
            liquid handling device to be used for the transfer

        Returns
        -------
        dict
            flowrate params
        """
        if self.dispense_flowrate is not None:
            flowrate = self.dispense_flowrate
        elif self.dispense_flowrate_calibration_curve is not None:
            # pylint: disable=unsubscriptable-object
            calibration = self.dispense_flowrate_calibration_curve[tip_type]
            flowrate = calibration.binned_calibration_for_volume(volume)
        else:
            flowrate = None
        return flowrate


class VolumeCalibrationBin(namedtuple("VolumeCalibrationBin", ["slope", "intercept"])):
    """Wrapper for slope and intercept parameters for linear fitting
    Holds information required to calibrate a volume for liquid handle step
    assuming a linear relationship between volume and calibrated volume.
    """

    def __new__(cls, slope, intercept):
        """
        Parameters
        ----------
        slope : Number
          The slope of the linear fit volume calibration function.
        intercept : Unit
          The intercept of the linear fit volume calibration function.

        Returns
        -------
        VolumeCalibrationBin
            an object used for linear fitting volumes within a bin

        Raises
        ------
        TypeError
            if slope is not a number
        """
        if not isinstance(slope, Number):
            raise TypeError(f"slope {slope} is not a Number")
        intercept = parse_unit(intercept, "microliter")
        return super(VolumeCalibrationBin, cls).__new__(cls, slope, intercept)

    def calibrate_volume(self, volume):
        """Calibrates the volume using slope and intercept

        Parameters
        ----------
        volume : Unit
            the volume to be calibrated

        Returns
        -------
        Unit
            calibrated volume
        """
        return self.slope * volume + self.intercept


# pylint: disable=too-few-public-methods
class VolumeCalibration(object):
    """Wrapper for a volume-binned calibration curve
    A data structure that represents a calibration curve for either volumes
    or flowrates that are binned by upper bounded volume ranges.
    """

    def __init__(self, *args):
        """
        Parameters
        ----------
        args : (Unit(volume), VolumeCalibrationBin or dict)
            individual calibration bins

        Raises
        ------
        TypeError
            Not all points on the calibration curve are of the correct type
        """
        calibration_curve = list((parse_unit(bin, "uL"), point) for bin, point in args)

        points = [point for _, point in calibration_curve]
        calibration_types = (VolumeCalibrationBin, dict)
        if not all(isinstance(_, calibration_types) for _ in points):
            raise TypeError(f"values {points} are not one of {calibration_types}")

        sorted_curve = list(sorted(calibration_curve, key=lambda k: k[0]))

        self.calibration_curve = sorted_curve

    def binned_calibration_for_volume(self, volume):
        """Gets the smallest suitable bin in the calibration curve
        Finds the smallest point on the calibration curve that has a bin
        that's greater than or equal to the size of the specified value.

        Parameters
        ----------
        volume: Unit or int or float
            the value to be binned

        Returns
        -------
        dict
            target_bin

        Raises
        ------
        RuntimeError
            No suitably large calibration bin
        """
        volume = parse_unit(volume, "microliter")

        valid_bins = list(
            point
            for _, point in filter(lambda b: b[0] >= volume, self.calibration_curve)
        )
        if not valid_bins:
            raise RuntimeError(
                f"No volume calibration bin in {self.calibration_curve} is "
                f"large enough to accommodate {volume}."
            )

        return valid_bins[0]
