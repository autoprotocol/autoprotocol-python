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


class make_dottable_dict(dict):
    '''Enable dictionaries to be accessed using dot notation instead of bracket
    notation.

    Example
    -------
    .. code-block:: python

        >>> sample = {
            "forks": 6,
            "spoons": 5,
            "knives": 3
        }

        >>> print sample["forks"]
        6

        >>> sample = make_dottable_dict(sample)

        >>> print sample.forks
        6

    Parameters
    ----------
    dict : dict
        Dictionary to be made dottable.

    '''
    def __getattr__(self, attr):
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
