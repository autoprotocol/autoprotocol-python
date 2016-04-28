from .unit import Unit
from textwrap import dedent

'''
    :copyright: 2016 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''


def quad_ind_to_num(q):
    """
    Convert a 384-well plate quadrant well index into its corresponding
    integer form.

    "A1" -> 0
    "A2" -> 1
    "B1" -> 2
    "B2" -> 3

    Parameters
    ----------
    q : int, str
        A string or integer representing a well index that corresponds to a
        quadrant on a 384-well plate.

    """
    if isinstance(q, str):
        q = q.lower()
    if q in ["a1", 0]:
        return 0
    elif q in ["a2", 1]:
        return 1
    elif q in ["b1", 24]:
        return 2
    elif q in ["b2", 25]:
        return 3
    else:
        raise ValueError("Invalid quadrant index.")


def quad_num_to_ind(q, human=False):
    """
    Convert a 384-well plate quadrant integer into its corresponding well index.

    0 -> "A1" or 0
    1 -> "A2" or 1
    2 -> "B1" or 24
    3 -> "B2" or 25

    Parameters
    ----------
    q : int
        An integer representing a quadrant number of a 384-well plate.
    human : bool, optional
        Return the corresponding well index in human readable form instead of
        as an integer if True.

    """
    if q == 0:
        if human:
            return "A1"
        else:
            return 0
    elif q == 1:
        if human:
            return "A2"
        else:
            return 1
    elif q == 2:
        if human:
            return "B1"
        else:
            return 24
    elif q == 3:
        if human:
            return "B2"
        else:
            return 25
    else:
        raise ValueError("Invalid quadrant number.")


def check_valid_origin(origin, stamp_type, columns, rows):
    # Checks if selected well is a valid origin destination for the given plate
    # Assumption: SBS formatted plates and 96-tip layout
    robotized_origin = origin.index
    well_count = origin.container.container_type.well_count
    col_count = origin.container.container_type.col_count
    row_count = well_count // col_count

    if well_count == 96:
        if stamp_type == "full":
            if robotized_origin != 0:
                raise ValueError("For full 96-well transfers, origin has "
                                 "to be well 0.")
        elif stamp_type == "row":
            if (robotized_origin % col_count) != 0 or robotized_origin > ((
                    row_count - rows) * col_count):
                raise ValueError("For row transfers, origin "
                                 "has to be specified within the left "
                                 "column and not more than allowed by shape.")
        else:
            if robotized_origin > (col_count - columns) or robotized_origin < 0:
                raise ValueError("For column transfers, origin "
                                 "has to be specified within the top "
                                 "column and not more than allowed by shape.")
    elif well_count == 384:
        if stamp_type == "full":
            if robotized_origin not in [0, 1, 24, 25]:
                raise ValueError("For full 384-well transfers, origin has "
                                 "to be well 0, 1, 24 or 25.")
        elif stamp_type == "row":
            if (robotized_origin % col_count) not in [0, 1] or (
                robotized_origin >= ((row_count - ((
                    rows - 1) * 2)) * col_count)):
                raise ValueError("For row transfers, origin"
                                 "has to be specified within the left "
                                 "two columns and not more than allowed by "
                                 "shape.")
        else:
            if robotized_origin >= col_count * 2 or (
                robotized_origin < 0) or (
                robotized_origin % col_count >= (
                    col_count - ((columns - 1) * 2))):
                raise ValueError("For column transfers, origin "
                                 "has to be specified within the top "
                                 "two columns and not more than allowed by "
                                 "shape.")
    else:
        raise RuntimeError("Unsupported plate type for checking origin.")


def check_stamp_append(current_xfer, prev_xfer_list, maxTransfers=3,
                       maxContainers=3,
                       volumeSwitch=Unit.fromstring("31:microliter")):
    """
    Checks whether current stamp can be appended to previous stamp instruction.
    """
    prev_cols = prev_xfer_list[0]["shape"]["columns"]
    prev_rows = prev_xfer_list[0]["shape"]["rows"]
    cols = current_xfer["shape"]["columns"]
    rows = current_xfer["shape"]["rows"]

    # Ensure Instruction contains either all full plate or selective (all rows
    # or all columns)
    if (prev_cols == cols == 12) and (prev_rows == rows == 8):
        axis_key = None
    elif prev_cols == 12:
        axis_key = "rows"
        if cols != 12:
            return False
    elif prev_rows == 8:
        axis_key = "columns"
        if rows != 8:
            return False

    # Ensure Instruction contain the same volume type as defined by TCLE
    # Currently volumeSwitch is hardcoded to check against the two tip volume
    # types used in TCLE
    if prev_xfer_list[0]["transfer"][0]["volume"] <= volumeSwitch:
        if current_xfer["transfer"][0]["volume"] > volumeSwitch:
            return False
    elif prev_xfer_list[0]["transfer"][0]["volume"] > volumeSwitch:
        if current_xfer["transfer"][0]["volume"] <= volumeSwitch:
            return False

    # Check if maximum Transfers/Containers is reached
    originList = ([y["from"] for x in prev_xfer_list for y in x["transfer"]] +
                  [y["to"] for x in prev_xfer_list for y in x["transfer"]] +
                  [y["from"] for y in current_xfer["transfer"]] +
                  [y["to"] for y in current_xfer["transfer"]])

    if axis_key:
        num_prev_xfers = sum([x["shape"][axis_key] for x in prev_xfer_list])
        num_current_xfers = current_xfer["shape"][axis_key]
    else:
        num_prev_xfers = len(prev_xfer_list)
        num_current_xfers = 1

    if (num_prev_xfers + num_current_xfers > maxTransfers or
            len(set(map(lambda x: x.container, originList))) > maxContainers):
        return False

    return True


def check_valid_mag(container, head):
    shortname = container.container_type.shortname

    if head == "96-deep":
        if shortname not in ["96-v-kf", "96-deep-kf", "96-deep"]:
            raise ValueError("{} container is not compatible with {} head"
                             .format(container.container_type.shortname, head))
    elif head == "96-pcr":
        if shortname not in ["96-pcr", "96-v-kf", "96-flat", "96-flat-uv"]:
            raise ValueError("{} container is not compatible with {} head"
                             .format(container.container_type.shortname, head))


def check_valid_mag_params(mag_dict):
    if "frequency" in mag_dict:
        if Unit.fromstring(mag_dict["frequency"]) < Unit.fromstring("0:hertz"):
            raise ValueError("Frequency set at {}, must not be less than 0:hertz"
                             .format(mag_dict["frequency"]))

    if "temperature" in mag_dict and mag_dict["temperature"]:
        if Unit.fromstring(mag_dict["temperature"]) < Unit.fromstring("-273.15:celsius"):
            raise ValueError("Temperature set at {}, must not be less than absolute zero'"
                             .format(mag_dict["temperature"]))
    elif "temperature" in mag_dict and not mag_dict["temperature"]:
            del mag_dict["temperature"]

    if "amplitude" in mag_dict:
        if mag_dict["amplitude"] > mag_dict["center"]:
            raise ValueError("'amplitude': {}, must be less than 'center': {}"
                             .format(mag_dict["amplitude"], mag_dict["center"]))
        if mag_dict["amplitude"] < 0:
            raise ValueError("Amplitude set at %s, must not be negative" % mag_dict["amplitude"])

    if any(kw in mag_dict for kw in ("center", "bottom_position", "tip_position")):
        tip_position = mag_dict.get("tip_position")
        bottom_position = mag_dict.get("bottom_position", tip_position)
        position = mag_dict.get("center", bottom_position)

        if position < 0:
            raise ValueError("Tip head position set at %s, must not be negative" % position)

    if "magnetize" in mag_dict:
        if not isinstance(mag_dict["magnetize"], bool):
            raise ValueError("Magnetize set at: %s, must be boolean" % mag_dict["magnetize"])


def check_valid_gel_purify_band(band):
    from .container import Well

    if not isinstance(band, dict):
        error_str = dedent("""
            Bands for gel_purify must be a dictionary in the form of
                {
                  'elution_volume': volume,
                  'elution_buffer': str,
                  'band_size_range': {
                    'min_bp': int,
                    'max_bp': int
                    },
                  'destination': well
                }
        """)
        raise AttributeError(error_str)

    if not all(k in band.keys() for k in ["elution_buffer", "band_size_range", "destination", "elution_volume"]):
        raise KeyError("Band parameter keys must be: 'elution_buffer', 'band_size_range', 'destination' 'elution_volume'.")
    if not isinstance(band["elution_volume"], Unit):
        raise ValueError("All band elution volumes must be of type Unit.")
    if band["elution_volume"] <= Unit(0, "microliter"):
        raise ValueError("Band elution volume: %s must be greater than 0:microliter." % band["elution_volume"])
    if not isinstance(band["destination"], Well):
        raise ValueError("All band destinations must be of type Well.")
    if not isinstance(band["band_size_range"], dict):
        raise AttributeError("Band parameter 'band_size_range' must be a dict with keys: 'max_bp', 'min_bp.")
    if not all(k in band["band_size_range"].keys() for k in ["min_bp", "max_bp"]):
        raise KeyError("Band parameter 'band_size_range' keys must be: 'max_bp', 'min_bp'.")
    if not band["band_size_range"]["max_bp"] > band["band_size_range"]["min_bp"]:
        raise ValueError("max_bp must be greater than min_bp")


def check_valid_gel_purify_extract(extract):

    from .container import Well

    if not isinstance(extract, dict):
        raise AttributeError("Extract for gel_purify must be a dictionary in the form of {'source': well, 'band_list': list, 'gel': int, 'lane': int}")
    if not all(k in extract.keys() for k in ["source", "band_list", "lane", "gel"]):
        raise KeyError("Extract parameter keys must be 'source', 'band_list', 'lane', 'gel'.")
    if not isinstance(extract["source"], Well):
        raise ValueError("All extract sources must be of type Well.")

    for band in extract["band_list"]:
        check_valid_gel_purify_band(band)


def make_gel_extract_params(source, band_list, lane=None, gel=None):

    if isinstance(band_list, dict):
        band_list = [band_list]

    for band in band_list:
        check_valid_gel_purify_band(band)

    extract = {
        "source": source,
        "band_list": band_list,
        "lane": lane,
        "gel": gel
    }

    check_valid_gel_purify_extract(extract)

    return extract


def make_band_param(elution_buffer, elution_volume, max_bp, min_bp, destination):

    band = {
        "band_size_range": {
            "min_bp": min_bp, "max_bp": max_bp
        },
        "elution_volume": Unit(elution_volume),
        "elution_buffer": elution_buffer,
        "destination": destination
    }

    check_valid_gel_purify_band(band)

    return band


class make_dottable_dict(dict):

    '''Enable dictionaries to be accessed using dot notation instead of bracket
    notation.  This class should probably never be used.

    Example
    -------
    .. code-block:: python

        >>> d = {"foo": {
                    "bar": {
                        "bat": "Hello!"
                        }
                    }
                }

        >>> print d["foo"]["bar"]["bat"]
        Hello!

        >>> d = make_dottable_dict(d)

        >>> print d.foo.bar.bat
        Hello!

    Parameters
    ----------
    dict : dict
        Dictionary to be made dottable.

    '''

    def __getattr__(self, attr):
        if type(self[attr]) == dict:
            return make_dottable_dict(self[attr])
        return self[attr]

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def deep_merge_params(defaults, override):
    """Merge two dictionaries while retaining common key-value pairs.

    Parameters
    ----------
    defaults : dict
        Default dictionary to compare with overrides.
    override : dict
        Dictionary containing additional keys and/or values to override those
        corresponding to keys in the defaults dicitonary.

    """
    defaults = make_dottable_dict(defaults.copy())
    for key, value in override.items():
        if isinstance(value, dict):
            # get node or create one
            defaults[key] = deep_merge_params(defaults.get(key, {}), value)
        else:
            defaults[key] = value

    return defaults


def incubate_params(duration, shake_amplitude=None, shake_orbital=None):
    """
    Create a dictionary with incubation parameters which can be used as input
    for instructions. Currenly supports plate reader instructions and could be
    extended for use with other instructions.

    Parameters
    ----------
    shake_amplitude: str, Unit
        amplitude of shaking between 1 and 6:millimeter
    shake_orbital: bool
        True for oribital and False for linear shaking
    duration: str, Unit
        time for shaking
    """

    incubate_dict = {}
    incubate_dict["duration"] = duration
    if (shake_amplitude is not None) and (shake_orbital is not None):
        shake_dict = {
            "amplitude": shake_amplitude,
            "orbital": shake_orbital
        }
        incubate_dict["shaking"] = shake_dict
    elif (shake_amplitude is not None) ^ (shake_orbital is not None):
        raise RuntimeError("Both `shake_amplitude`: {} and `shake_orbital`: {} "
                           "must not be None for shaking to be set".format(shake_amplitude, shake_orbital))

    check_valid_incubate_params(incubate_dict)

    return incubate_dict


def check_valid_incubate_params(idict):
    """Check to be sure incubate_params are structured correctly

    .. code-block:: json

        {
          "shaking": {
            "amplitude": str, Unit
            "orbital": bool
            }
        "duration": str, Unit
        }

    where duration is required, shaking is optional, and amplitude and orbital
    are both required if shaking is specified.

    """

    if 'duration' not in idict:
        raise RuntimeError("For the incubation dictionary: %s, `duration` must be specified" % idict)
    else:
        if Unit.fromstring(idict['duration']) <= Unit("0:second"):
            raise ValueError("duration: %s must be positive" % idict['duration'])

    if "shaking" in idict:
        shaking = idict["shaking"]
        if "orbital" in shaking and "amplitude" in shaking:
            if not isinstance(shaking["orbital"], bool):
                raise ValueError("shake_orbital: %s must be a boolean" % shaking["orbital"])
            if Unit.fromstring(shaking["amplitude"]) < Unit.fromstring("0:millimeter"):
                raise ValueError("shake_amplitude: %s must be positive" % shaking["amplitude"])
        else:
            raise RuntimeError("Both `shake_amplitude`: {} and `shake_orbital`: "
                               "{} must not be None for shaking to be set"
                               .format(shaking.get("amplitude"), shaking.get("orbital")))

    return True
