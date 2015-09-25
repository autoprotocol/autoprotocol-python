from .unit import Unit
'''
    :copyright: 2015 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''

def convert_to_ul(vol):
    """
    Convert a Unit or volume string into its equivalent in microliters.

    Parameters
    ----------
    vol : Unit, str
        A volume string or Unit with the unit "nanoliter" or "milliliter"

    """
    v = Unit.fromstring(vol)
    if v.unit == "nanoliter":
        v = Unit(v.value/1000, "microliter")
    elif v.unit == "milliliter":
        v = Unit(v.value*1000, "microliter")
    elif v.unit == "microliter":
        return v
    else:
        raise ValueError("The unit you're trying to convert to microliters "
                         "is invalid.")
    return v


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


def check_valid_origin(origin, plate_type, stamp_type):
    # Checks if selected well is a valid origin destination for the given plate
    # Assumption: SBS formatted plates and 96-tip layout
    robotized_origin = plate_type.robotize(origin)
    well_count = plate_type.well_count
    col_count = plate_type.col_count
    row_count = plate_type.well_count // col_count

    if well_count == 96:
        if stamp_type == "full":
            if robotized_origin != 0:
                raise ValueError("For full 96-well transfers, origin has "
                                 "to be well 0.")
        elif stamp_type == "row":
            if (robotized_origin % col_count) != 0:
                raise ValueError("For row transfers, origin"
                                 "has to be specified within the left "
                                 "column.")
        else:
            if robotized_origin >= col_count or robotized_origin < 0:
                raise ValueError("For column transfers, origin "
                                 "has to be specified within the top "
                                 "column.")
    elif well_count == 384:
        if stamp_type == "full":
            if robotized_origin not in [0, 1, 24, 25]:
                raise ValueError("For full 384-well transfers, origin has "
                                 "to be well 0, 1, 24 or 25.")
        elif stamp_type == "row":
            if (robotized_origin % col_count) not in [0, 1]:
                raise ValueError("For row transfers, origin"
                                 "has to be specified within the left "
                                 "column.")
        else:
            if robotized_origin >= col_count*2 or robotized_origin < 0:
                raise ValueError("For column transfers, origin "
                                 "has to be specified within the top "
                                 "column.")
    else:
        raise RuntimeError("Unsupported plate type for checking origin.")


def check_stamp_append(current_xfer, prev_xfer_list, maxTransfers=3, maxContainers=3, volumeSwitch=Unit.fromstring("31:microliter")):
    """
    Checks whether current stamp can be appended to previous stamp instruction.
    """
    # Ensure Instruction contains either all full plate or selective
    axis_key = None
    if (prev_xfer_list[0]["shape"]["columns"] == 12 and
       prev_xfer_list[0]["shape"]["rows"] == 8):
        if (current_xfer["shape"]["columns"] != 12 or
           current_xfer["shape"]["rows"] != 8):
            return False
    elif (current_xfer["shape"]["columns"] == 12 and
          current_xfer["shape"]["rows"] == 8):
        if (prev_xfer_list[0]["shape"]["columns"] != 12 or
           prev_xfer_list[0]["shape"]["rows"] != 8):
            return False
    # Ensure Instruction contains all column/row-wise transfers
    elif prev_xfer_list[0]["shape"]["columns"] == 12:
        axis_key = "rows"
        if current_xfer["shape"]["columns"] != 12:
            return False
    elif prev_xfer_list[0]["shape"]["rows"] == 8:
        axis_key = "columns"
        if current_xfer["shape"]["rows"] != 8:
            return False

    # Ensure Instruction contain the same volume type as defined by TCLE
    # Currently volumeSwitch is hardcoded to check against the two tip volume types used in TCLE
    if prev_xfer_list[0]["volume"] <= volumeSwitch:
        if current_xfer["volume"] > volumeSwitch:
            return False
    elif prev_xfer_list[0]["volume"] > volumeSwitch:
        if current_xfer["volume"] <= volumeSwitch:
            return False

    # Check if maximum Transfers/Containers is reached
    originList = ([x["from"] for x in prev_xfer_list] +
                  [x["to"] for x in prev_xfer_list] +
                  [current_xfer["from"], current_xfer["to"]])

    if axis_key:
        num_prev_xfers = sum([x["shape"][axis_key] for x in prev_xfer_list])
    else:
        num_prev_xfers = len(prev_xfer_list)

    if (num_prev_xfers + 1 > maxTransfers or
       len(set(map(lambda x: x.container, originList))) > maxContainers):
        return False

    return True


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
