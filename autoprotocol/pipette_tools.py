def aspirate_source(depth=None, aspirate_speed=None, cal_volume=None,
                    primer_vol=None):
    '''
    Set parameters for aspirating from a source well before a transfer or
    distribute operation.

    Parameters
    ----------
    depth : fn, optional
        Depth at which to aspirate liquid from a well.
    aspirate_speed : dict
        Dictionary specifying the "start" and "max" aspirate speed.
        .. code-block:: json

          {
            "start": "50:microliter/second",
            "max": "150:microliter/second"
          }

    cal_volume : str, Unit, optional
        Calibrated volume to aspirate from a well.
    primer_vol : str, Unit
        An amount of liquid that is aspirated in addition to the nominal volume
        specified and then re-dispensed into the well the tip is aspirating
        from (source well).

    '''
    source = {}
    assign(source, "depth", depth)
    assign(source, "aspirate_speed", aspirate_speed)
    assign(source, "volume", cal_volume)
    assign(source, "primer_vol", primer_vol)
    return source


def dispense_target(depth=None, dispense_speed=None, cal_volume=None):
    '''
    Set parameters for dispensing to a target well during a transfer or
    distribute.

    Parameters
    ----------
    depth : fn, optional
        Depth at which to dispense liquid into target well.
    dispense_speed : dict
        Dictionary specifying the "start" and "max" dispense speed.
        .. code-block:: json

          {
            "start": "50:microliver/second",
            "max": "150:microliter/second"
          }

    cal_volume : str, Unit, optional
        Calibrated volume to be dispensed to target well.

    '''
    target = {}
    assign(target, "depth", depth)
    assign(target, "dispense_speed", dispense_speed)
    assign(target, "volume", cal_volume)
    return target


def distribute_target(dst_loc, volume, dispense_speed=None,
                      dispense_target=None):
    '''
    Set parameters target wells of a distrbute instruction.

    Example usage:

    .. code-block:: python

        p = Protocol()
        sample_plate = p.ref("sample", None, "96-pcr", discard=True)

        distribute_targets = []

        distribute_targets.append(
            distribute_target(sample_plate.well(1), "20:microliter",
                              dispense_speed="120:microliter/second",
                              dispense_target= dispense_target(
                                depth=depth("ll_surface")))
            )

        distribute_targets.append(
            distribute_target(sample_plate.well(2), "50:microliter",
                              dispense_speed="50:microliter/second")
            )

        p.append(Pipette([
                        {"distribute": {
                            "from": sample_plate.well(0),
                            "to": distribute_targets
                            }
                        }]))

    outputs:

    .. code-block:: json

        {
          "refs": {
            "sample": {
              "new": "96-pcr",
              "discard": true
            }
          },
          "instructions": [
            {
              "groups": [
                {
                  "distribute": {
                    "to": [
                      {
                        "volume": "20:microliter",
                        "dispense_speed": "120:microliter/second",
                        "well": "sample/1",
                        "x_dispense_target": {
                          "depth": {
                            "method": "ll_surface"
                          }
                        }
                      },
                      {
                        "volume": "50:microliter",
                        "dispense_speed": "50:microliter/second",
                        "well": "sample/2"
                      }
                    ],
                    "from": "sample/0"
                  }
                }
              ],
              "op": "pipette"
            }
          ]
        }


    Parameters
    ----------
    dst_loc : Well, str
        Well (target) to distribute liquid to.
    volume : str, unit
        Nominal volume of liquid to dispense to the target well.
    dispense_speed : dict
        Dictionary specifying the "start" and "max" dispense speed.
        .. code-block:: json

          {
            "start": "50:microliver/second",
            "max": "150:microliter/second"
          }

    dispense_target : fn, optional
        May not be specified if dispense_speed is specified.  Allows further
        configuration of dispense parameters such as depth.

    '''
    distribute = {
        "well": dst_loc,
        "volume": volume
    }
    assign(distribute, "dispense_speed", dispense_speed)
    assign(distribute, "x_dispense_target", dispense_target)
    return distribute


def depth(relation, lld=None, distance="0.0:meter"):
    """
    Return a stanza specifying pipette tip depth for aspirating or dispensing.

    Parameters
    ----------
    relation : str
      Relative position from which to measure distance of the pipette tip.
    lld : str, optional
      Method of liquid level detection.
    distance : str, unit
      Distance compared to position set by relation parameter, measured
      in millimeters.

    """
    valid_depths = set(["ll_surface", "ll_following", "ll_top", "ll_bottom"])
    if relation not in valid_depths:
        print("Invalid depth:", relation)
        sys.exit()
    depth = {"method": relation}
    assign(depth, "lld", lld)
    assign(depth, "distance", distance)
    return depth


def assign(obj, key, var):
    if var is not None:
        obj[key] = var
