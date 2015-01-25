'''
    :copyright: 2015 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''

class make_dottable_dict(dict):
    '''Enable dictionaries to be accessed using dot notation instead of bracket
    notation.

    Ex)
        sample = {
            "forks": 6,
            "spoons": 5,
            "knives": 3
        }

        print sample["forks"]
        >>> 6

        sample = make_dottable_dict(sample)

        print sample.forks
        >>> 6

    '''
    def __getattr__(self, attr):
        return self[attr]

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def deep_merge_params(defaults, override):
    defaults = make_dottable_dict(defaults.copy())
    for key, value in override.items():
        if isinstance(value, dict):
            # get node or create one
            defaults[key] = deep_merge_params(defaults.get(key, {}), value)
        else:
            defaults[key] = value

    return defaults
