from .container import Container, Well, WellGroup
from .container_type import ContainerType, _CONTAINER_TYPES
from .unit import Unit
from .instruction import *
from .pipette_tools import assign

'''
    :copyright: 2015 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''


class Ref(object):
    """Link a ref name (string) to a Container instance.

    """
    def __init__(self, name, opts, container):
        self.name = name
        self.opts = opts
        self.container = container


class Protocol(object):
    """
    A Protocol is a sequence of instructions to be executed, and a set of
    containers on which those instructions act.

    Initially, a Protocol has an empty sequence of instructions and no
    referenced containers. To add a reference to a container, use the ref()
    method, which returns a Container

        .. code-block:: python

            p = Protocol()
            my_plate = p.ref("my_plate", id="ct1xae8jabbe6",
                                    cont_type="96-pcr", storage="cold_4")

    To add instructions to the protocol, use the helper methods in this class

        .. code-block:: python

            p.transfer(source=my_plate.well("A1"),
                       dest=my_plate.well("B4"),
                       volume="50:microliter")
            p.thermocycle(my_plate, groups=[
                          { "cycles": 1,
                            "steps": [
                              { "temperature": "95:celsius",
                                "duration": "1:hour"
                              }]
                          }])

    Autoprotocol Output:

        .. code-block:: json

            {
              "refs": {
                "my_plate": {
                  "id": "ct1xae8jabbe6",
                  "store": {
                    "where": "cold_4"
                  }
                }
              },
              "instructions": [
                {
                  "groups": [
                    {
                      "transfer": [
                        {
                          "volume": "50.0:microliter",
                          "to": "my_plate/15",
                          "from": "my_plate/0"
                        }
                      ]
                    }
                  ],
                  "op": "pipette"
                },
                {
                  "volume": "10:microliter",
                  "dataref": null,
                  "object": "my_plate",
                  "groups": [
                    {
                      "cycles": 1,
                      "steps": [
                        {
                          "duration": "1:hour",
                          "temperature": "95:celsius"
                        }
                      ]
                    }
                  ],
                  "op": "thermocycle"
                }
              ]
            }

    """

    def __init__(self, refs=[], instructions=None):
        super(Protocol, self).__init__()
        self.refs = {}
        for ref in refs:
            self.refs[ref.name] = ref
        self.instructions = instructions if instructions is not None else []

    def container_type(self, shortname):
        """
        Convert a ContainerType shortname into a ContainerType object.

        Parameters
        ----------
        shortname : {"384-flat", "384-pcr", "96-flat", "96-pcr", "96-deep",
                    "micro-2.0", "micro-1.5"}
            String representing one of the ContainerTypes in the
            _CONTAINER_TYPES dictionary

        Returns
        -------
        ContainerType
            Returns a Container type object corresponding to the shortname
            passed to the function.  If a ContainerType object is passed,
            that same ContainerType is returned.

        Raises
        ------
        ValueError
            If an unknown ContainerType shortname is passed as a parameter

        """
        if isinstance(shortname, ContainerType):
            return shortname
        elif shortname in _CONTAINER_TYPES:
            return _CONTAINER_TYPES[shortname]
        else:
            raise ValueError("Unknown container type %s (known types=%s)" %
                             (shortname, str(_CONTAINER_TYPES.keys())))

    def ref(self, name, id=None, cont_type=None, storage=None, discard=None):
        """
        Append a Ref object to the list of Refs associated with this protocol
        and returns a Container with the id, container type and storage or
        discard conditions specified.

        Example Usage:

        .. code-block:: python

            p = Protocol()

            # ref a new container (no id specified)
            sample_ref_1 = p.ref("sample_plate_1",
                                 cont_type="96-pcr",
                                 discard=True)

            # ref an existing container with a known id
            sample_ref_2 = p.ref("sample_plate_2",
                                 id="ct1cxae33lkj",
                                 cont_type="96-pcr",
                                 storage="ambient")

        Autoprotocol Output:

        .. code-block:: json

            {
              "refs": {
                "sample_plate_1": {
                  "new": "96-pcr",
                  "discard": true
                },
                "sample_plate_2": {
                  "id": "ct1cxae33lkj",
                  "store": {
                    "where": "ambient"
                  }
                }
              },
              "instructions": []
            }

        Parameters
        ----------
        name : str
            name of the container/ref being created
        id : str
            id of the container being created, from your organization's
            inventory on http://secure.transcriptic.com.  Strings representing
            ids begin with "ct"
        cont_type : str, ContainerType
            container type of the Container object that will be generated
        storage : {"ambient", "cold_20", "cold_4", "warm_37"}, optional
            temperature the container being referenced should be stored at
            after a run is completed.  Either a storage condition must be
            specified or discard must be set to True.
        discard : bool, optional
            if no storage condition is specified and discard is set to True,
            the container being referenced will be discarded after a run
        Returns
        -------
        container : Container
            Container object generated from the id and container type provided
        Raises
        ------
        ValueError
            if no container type is provided
        ValueError
            if no discard or storage condition is provided

        """
        assert name not in self.refs
        opts = {}
        cont_type = self.container_type(cont_type)
        if id:
            opts["id"] = id
        else:
            opts["new"] = cont_type.shortname
        if not cont_type:
            raise ValueError("You a container type must always be specified")
        else:
            container = Container(id, cont_type)
        if storage in ["ambient", "cold_20", "cold_4", "warm_37"] and \
                not discard:
            opts["store"] = {"where": storage}
        elif discard and not storage:
            opts["discard"] = discard
        else:
            raise ValueError("You must specify either a valid storage "
                             "temperature or set discard=True for a container")
        self.refs[name] = Ref(name, opts, container)
        return container

    def append(self, instructions):
        """
        Append instruction(s) to the list of Instruction objects associated
        with this protocol.  The other functions on Protocol() should be used
        in lieu of doing this directly.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            p.append(Incubate("sample_plate", "ambient", "1:hour"))

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "duration": "1:hour",
                  "where": "ambient",
                  "object": "sample_plate",
                  "shaking": false,
                  "op": "incubate"
                }
            ]

        Parameters
        ----------
        instructions : Instruction
            Instruction object to be appended

        """
        if type(instructions) is list:
            self.instructions.extend(instructions)
        else:
            self.instructions.append(instructions)

    def as_dict(self):
        """
        Return the entire protocol as a dictionary.

        Example Usage:

        .. code-block:: python

            from autoprotocol.protocol import Protocol
            import json

            p = Protocol()
            sample_ref_2 = p.ref("sample_plate_2",
                                  id="ct1cxae33lkj",
                                  cont_type="96-pcr",
                                  storage="ambient")
            p.seal(sample_ref_2)
            p.incubate(sample_ref_2, "warm_37", "20:minute")

            print json.dumps(p.as_dict(), indent=2)

        Autoprotocol Output:

        .. code-block:: json

            {
              "refs": {
                "sample_plate_2": {
                  "id": "ct1cxae33lkj",
                  "store": {
                    "where": "ambient"
                  }
                }
              },
              "instructions": [
                {
                  "object": "sample_plate_2",
                  "op": "seal"
                },
                {
                  "duration": "20:minute",
                  "where": "warm_37",
                  "object": "sample_plate_2",
                  "shaking": false,
                  "op": "incubate"
                }
              ]
            }

        Returns
        -------
        dict
            dict with keys "refs" and "instructions", each of which contain
            the "refified" contents of their corresponding Protocol attribute

        """
        return {
            "refs": dict(
                (key, value.opts)
                for key, value in self.refs.items()
            ),
            "instructions": list(map(lambda x: self._refify(x.data),
                                     self.instructions))
        }

    def distribute(self, source, dest, volume, allow_carryover=False,
                   mix_before=False, mix_vol=None, repetitions=10,
                   flowrate="100:microliter/second", aspirate_speed=None,
                   aspirate_source=None, distribute_target=None, pre_buffer=None,
                   disposal_vol=None, transit_vol=None, blowout_buffer=None,
                   tip_type=None, new_group=False):
        """
        Distribute liquid from source well(s) to destination wells(s)


        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")
            sample_source = p.ref("sample_source",
                                  "ct32kj234l21g",
                                  "micro-1.5",
                                  storage="cold_20")

            p.distribute(sample_source.well(0),
                         sample_plate.wells_from(0,8,columnwise=True),
                         "200:microliter",
                         mix_before=True,
                         mix_vol="500:microliter",
                         repetitions=20)

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
              {
                "groups": [
                  {
                    "distribute": {
                      "to": [
                        {
                          "volume": "150.0:microliter",
                          "well": "sample_plate/0"
                        },
                        {
                          "volume": "150.0:microliter",
                          "well": "sample_plate/12"
                        },
                        {
                          "volume": "150.0:microliter",
                          "well": "sample_plate/24"
                        },
                        {
                          "volume": "150.0:microliter",
                          "well": "sample_plate/36"
                        },
                        {
                          "volume": "150.0:microliter",
                          "well": "sample_plate/48"
                        },
                        {
                          "volume": "150.0:microliter",
                          "well": "sample_plate/60"
                        },
                        {
                          "volume": "150.0:microliter",
                          "well": "sample_plate/72"
                        },
                        {
                          "volume": "150.0:microliter",
                          "well": "sample_plate/84"
                        }
                      ],
                      "from": "sample_source/0",
                      "mix_before": {
                        "volume": "500:microliter",
                        "repetitions": 20,
                        "speed": "100:microliter/second"
                      }
                    }
                  }
                ],
                "op": "pipette"
              }
            ]

        Parameters
        ----------
        source : Well, WellGroup
            Well or wells to distribute liquid from.  If passed as a WellGroup
            with set_volume() called on it, liquid will be automatically be
            drawn from the wells specified using the fill_wells function
        dest : Well, WellGroup
            Well or wells to distribute liquid to
        volume : str, Unit, list
            Volume of liquid to be distributed to each destination well.  If a
            single string or unit is passed to represent the volume, that volume
            will be distributed to each destination well.  If a list of volumes
            is provided, that volume will be distributed to the corresponding
            well in the WellGroup provided. The length of the volumes list must
            therefore match the number of wells in the destination WellGroup if
            destination wells are recieving different volumes.
        allow_carryover : bool, optional
            specify whether the same pipette tip can be used to aspirate more
            liquid from source wells after the previous volume aspirated has
            been depleted
        mix_before : bool, optional
            Specify whether to mix the liquid in the destination well before
            liquid is transferred.
        mix_vol : str, Unit, optional
            Volume to aspirate and dispense in order to mix liquid in a wells
            before liquid is distributed.
        repetitions : int, optional
            Number of times to aspirate and dispense in order to mix
            liquid in a well before liquid is distributed.
        flowrate : str, Unit, optional
            Speed at which to mix liquid in well before liquid is distributed
        aspirate speed : str, Unit, optional
            Speed at which to aspirate liquid from source well.  May not be
            specified if aspirate_source is also specified. By default this is the
            maximum aspiration speed, with the start speed being half of the speed
            specified.
        aspirate_source : fn, optional
            Can't be specified if aspirate_speed is also specified.
        distribute_target : fn, optional
            A function that contains additional parameters for distributing to
            target wells including depth, dispense_speed, and calibrated volume.
            If this parameter is specified, the same parameters will be applied to
            every destination well.
            Can't be specified if dispense_speed is also specified.
        pre_buffer : str, Unit, optional
            Volume of air aspirated before aspirating liquid
        disposal_vol : str, Unit, optional
            Volume of extra liquid to aspirate that will be dispensed into trash
            afterwards
        transit_vol : str, Unit, optional
            Volume of air aspirated after aspirating liquid to reduce presence of
            bubbles at pipette tip
        blowout_buffer : bool, optional
            If true the operation will dispense the pre_buffer along with the
            dispense volume.
            Cannot be true if disposal_vol is specified

        Raises
        ------
        RuntimeError
            If no mix volume is specified for the mix_before instruction
        ValueError
            If source and destination well(s) is/are not expressed as either
            Wells or WellGroups

        """
        opts = {}
        dists = self.fill_wells(dest, source, volume, distribute_target)
        groups = []
        for d in dists:
            opts = {}
            if mix_before:
                if not mix_vol:
                    raise RuntimeError("No mix volume specified for "
                                       "mix_before")
                opts["mix_before"] = {
                    "volume": mix_vol,
                    "repetitions": repetitions,
                    "speed": flowrate
                }
            if allow_carryover:
                opts["allow_carryover"] = allow_carryover
            opts["from"] = d["from"]
            opts["to"] = d["to"]
            assign(opts, "aspirate_speed", aspirate_speed)
            assign(opts, "allow_carryover", allow_carryover)
            assign(opts, "x_aspirate_source", aspirate_source)
            assign(opts, "x_pre_buffer", pre_buffer)
            assign(opts, "x_disposal_vol", disposal_vol)
            assign(opts, "x_transit_vol", transit_vol)
            assign(opts, "x_blowout_buffer", blowout_buffer)
            assign(opts, "x_tip_type", tip_type)

            groups.append({"distribute": opts})

        if new_group:
          self.append(Pipette(groups))
        else:
          self._pipette(groups)

    def transfer(self, source, dest, volume, one_source=False, one_tip=False,
                 mix_after=False, mix_before=False, mix_vol=None,
                 repetitions=10, flowrate="100:microliter/second",
                 aspirate_speed=None, dispense_speed=None, aspirate_source=None,
                 dispense_target=None, pre_buffer=None, disposal_vol=None,
                 transit_vol=None, blowout_buffer=None, tip_type=None,
                 new_group=False):
        """
        Transfer liquid from one specific well to another.  A new pipette tip
        is used between each transfer step unless the "one_tip" parameter
        is set to True.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 ct32kj234l21g,
                                 "96-flat",
                                 storage="warm_37")


            # a basic one-to-one transfer:
            p.transfer(sample_plate.well("B3"),
                       sample_plate.well("C3"),
                       "20:microliter")

            # using a basic transfer in a loop:
            for i in xrange(1, 12):
              p.transfer(sample_plate.well(i-1),
                         sample_plate.well(i),
                         "10:microliter")

            # transfer liquid from each well in the first column of a 96-well
            # plate to each well of the second column using a new tip and
            # a different volume each time:
            volumes = ["5:microliter", "10:microliter", "15:microliter",
                       "20:microliter", "25:microliter", "30:microliter",
                       "35:microliter", "40:microliter"]

            p.transfer(sample_plate.wells_from(0,8,columnwise=True),
                       sample_plate.wells_from(1,8,columnwise=True),
                       volumes)

            # transfer liquid from wells A1 and A2 (which both contain the same
            # source) into each of the following 10 wells:
            p.transfer(sample_plate.wells_from("A1", 2),
                       sample_plate.wells_from("A3", 10),
                       "10:microliter",
                       one_source=True)

            # transfer liquid from wells containing the same source to multiple
            # other wells without discarding the tip in between:
            p.transfer(sample_plate.wells_from("A1", 2),
                       sample_plate.wells_from("A3", 10),
                       "10:microliter",
                       one_source=True,
                       one_tip=True)


        Parameters
        ----------
        source : Well, WellGroup
            Well or wells to transfer liquid from.  If multiple source wells
            are supplied and one_source is set to True, liquid will be
            transfered from each source well specified as long as it contains
            sufficient volume. Otherwise, the number of source wells specified
            must match the number of destination wells specified and liquid
            will be transfered from each source well to its corresponding
            destination well.
        dest : Well, WellGroup
            Well or WellGroup to which to transfer liquid.  The number of
            destination wells must match the number of source wells specified
            unless one_source is set to True.
        volume : str, Unit, list
            The volume(s) of liquid to be transferred from source wells to
            destination wells.  Volume can be specified as a single string or
            Unit, or can be given as a list of volumes.  The length of a list
            of volumes must match the number of destination wells given unless
            the same volume is to be transferred to each destination well.
        one_source : bool, optional
            Specify whether liquid is to be transferred to destination wells
            from a group of wells all containing the same substance.
        one_tip : bool, optional
            Specify whether all transfer steps will use the same tip or not.
        mix_after : bool, optional
            Specify whether to mix the liquid in the destination well after
            liquid is transferred.
        mix_before : bool, optional
            Specify whether to mix the liquid in the destination well before
            liquid is transferred.
        mix_vol : str, Unit, optional
            Volume to aspirate and dispense in order to mix liquid in a wells
            before and/or after each transfer step.
        repetitions : int, optional
            Number of times to aspirate and dispense in order to mix
            liquid in well before and/or after each transfer step.
        flowrate : str, Unit, optional
            Speed at which to mix liquid in well before and/or after each
            transfer step
        aspirate speed : str, Unit, optional
            Speed at which to aspirate liquid from source well.  May not be
            specified if aspirate_source is also specified. By default this is the
            maximum aspiration speed, with the start speed being half of the speed
            specified.
        dispense_speed : str, Unit, optional
            Speed at which to dispense liquid into the destination well.  May not be
            specified if dispense_target is also specified.
        aspirate_source : fn, optional
            Can't be specified if aspirate_speed is also specified.
        dispense_target : fn, optional
            Same but opposite of  aspirate_source
        pre_buffer : str, Unit, optional
            Volume of air aspirated before aspirating liquid
        disposal_vol : str, Unit, optional
            Volume of extra liquid to aspirate that will be dispensed into trash
            afterwards
        transit_vol : str, Unit, optional
            Volume of air aspirated after aspirating liquid to reduce presence of
            bubbles at pipette tip
        blowout_buffer : bool, optional
            If true the operation will dispense the pre_buffer along with the
            dispense volume cannot be true if disposal_vol is specified

        Raises
        ------
        RuntimeError
            If more than one volume is specified as a list but the list length
            does not match the number of destination wells given.
        RuntimeError
            if transferring from WellGroup to WellGroup that have different
            number of wells and one_source is not True

        """
        source = WellGroup(source)
        dest = WellGroup(dest)
        opts = []

        if len(dest.wells) > 1 and len(source.wells) == 1 and not one_source:
            source = WellGroup(source.wells * len(dest.wells))
        if isinstance(volume,str) or isinstance(volume, Unit):
            volume = [Unit.fromstring(volume)] * len(dest.wells)
        elif isinstance(volume, list) and len(volume) == len(dest.wells):
            volume = map(lambda x: Unit.fromstring(x), volume)
        else:
            raise RuntimeError("Unless the same volume of liquid is being "
                               "transferred to each destination well, each "
                               "destination well must have a corresponding "
                               "volume in the form of a list")
        if (len(source.wells) != len(dest.wells)) and not one_source:
            raise RuntimeError("To transfer liquid from one well or multiple wells "
                               "containing the same source, set one_source to "
                               "True.  Otherwise, you must specify the same "
                               "number of source and destination wells to "
                               "do a one-to-one transfer.")
        if one_source:
            sources = []
            for idx, d in enumerate(dest.wells):
              for s in source.wells:
                vol = s.volume
                while vol >= volume[idx] and (len(sources) < len(dest.wells)):
                  sources.append(s)
                  vol -= volume[idx]
              if len(sources) < len(dest.wells):
                  raise RuntimeError("There is not enough volume in the "
                                     "source well(s) specified to complete the "
                                     "transfers")
            source = WellGroup(sources)

        for s,d,v in list(zip(source.wells, dest.wells, volume)):
            if mix_after and not mix_vol:
                mix_vol = v
            xfer = {
                "from": s,
                "to": d,
                "volume": v
            }
            if mix_before:
                xfer["mix_before"] = {
                    "volume": mix_vol,
                    "repetitions": repetitions,
                    "speed": flowrate
                }
            if mix_after:
                xfer["mix_after"] = {
                    "volume": mix_vol,
                    "repetitions": repetitions,
                    "speed": flowrate
                }
            assign(xfer, "aspirate_speed", aspirate_speed)
            assign(xfer, "dispense_speed", dispense_speed)
            assign(xfer, "x_aspirate_source", aspirate_source)
            assign(xfer, "x_dispense_target", dispense_target)
            assign(xfer, "x_pre_buffer", pre_buffer)
            assign(xfer, "x_disposal_vol", disposal_vol)
            assign(xfer, "x_transit_vol", transit_vol)
            assign(xfer, "x_blowout_buffer", blowout_buffer)

            opts.append(xfer)
            if d.volume:
                d.volume += v
            else:
                d.volume = v
            if s.volume:
                s.volume -= v
        trans = {}
        assign(trans, "x_tip_type", tip_type)
        if one_tip:
            trans["transfer"] = opts
            if new_group:
              self.append(Pipette([trans]))
            else:
              self._pipette([trans])
        else:
            for x in opts:
                trans = {}
                assign(trans, "x_tip_type", tip_type)
                trans["transfer"] = [x]
                if new_group:
                  self.append(Pipette([trans]))
                else:
                  self._pipette([trans])


    def stamp(self, source, dest, volume, mix_before=False,
              mix_after=False, mix_vol=None, repetitions=10,
              flowrate="100:microliter/second", aspirate_speed=None,
              dispense_speed=None, aspirate_source=None,
              dispense_target=None, pre_buffer=None, disposal_vol=None,
              transit_vol=None, blowout_buffer=None):
      """
      Move the specified volume of liquid from every well on the source plate
      to the corersponding well on the destination plate using a 96-channel
      liquid handler.

      The following stamping configurations are supported:

      - 384-well plate to 384-well plate
      - 96-well plate to 96-well plate
      - one 394-well plate to one 96-well plate (quad parameter must be specified)
      - one 384-well plate to multiple 96-well plates (dest must be a list)
      - one 96-well plate to one 384-well plate (quad parameter must be specified)
      - multiple 96-well plates to one 384-well plate (source must be a list)

      Example Usage:

      .. code-block:: python

        p = Protocol()

        96well_1 = p.ref("source", None, "96-flat", discard=True)
        96well_2 = p.ref("96_well_", None, "96-flat", discard=True)
        96well_3 = p.ref("96_well_", None, "96-flat", discard=True)
        96well_4 = p.ref("source", None, "96-flat", discard=True)
        384well_1 = p.ref("dest", None, "384-flat", discard=True)
        384well_2 = p.ref("dest", None, "384-flat", discard=True)

        # 96 -> 96:
        p.stamp(96well_1, 96well_2, "10:microliter")

        # 384 -> 384:
        p.stamp(384well_1, 384well_2, "10:microliter")

        # 384 -> one 96-well (specific quadrant):
        p.stamp(384well_1, 96well_1, "10:microliter", quad=2)

        # one 96-well to specific quadrant of 384:
        p.stamp(96well_2, 384well_1, "10:microliter", quad=0)

        # 384-well to multiple 96-well plates:
        p.stamp(384well_2,
                [{"container":96well_1, "quadrant": 0},
                 {"container":96well_2, "quadrant": 1},
                 {"container":96well_3, "quadrant": 2},
                 {"container":96well_4} "quadrant": 3}],
                "10:microliter")

        # combine multiple 96-well plates into one 384-well:
        p.stamp([{"container":96well_1, "quadrant": 0},
                 {"container":96well_2, "quadrant": 1},
                 {"container":96well_3, "quadrant": 2},
                 {"container":96well_4} "quadrant": 3}],
                384well_2,
                "10:microliter")


      Parameters
      ----------
      source : Container, list of dicts
        96- or 384-well plate(s) to source liquid from.  To specify more than
        one 96-well plate as a source for a 384-well plate, you must specify
        them as a list of dicts in the form of

        .. code-block:: json

            {"container": <container>, "quadrant": <quadrant>}

        and specify the destination quadrant
      dest : Container, list of dicts
        96- or 384-well plate(s) to transfer liquid to.  To specify more than
        one 96-well plate as a source for a 384-well plate, you must specify
        them as a list of dicts in the form of

        .. code-block:: json

            {"container": <container>, "quadrant": <quadrant>}

        and specify the destination quadrant
      volume : str, Unit
        Volume of liquid to move from source plate(s) to destination plate(s)
      quad : int
        Quadrant of 384 well plate to transfer liquid to when source is a
        96-well plate. Quadrant 0 is every other well starting from well A1,
        quadrant 1 is every other well starting from well A2, quadrant 2 is
        every other well starting from well B1, and quadrant 3 is every other
        well starting from well B2.
      mix_after : bool, optional
        Specify whether to mix the liquid in the destination well after
        liquid is transferred.
      mix_before : bool, optional
        Specify whether to mix the liquid in the destination well before
        liquid is transferred.
      mix_vol : str, Unit, optional
        Volume to aspirate and dispense in order to mix liquid in a wells
        before and/or after each transfer step.
      repetitions : int, optional
        Number of times to aspirate and dispense in order to mix
        liquid in well before and/or after each transfer step.
      flowrate : str, Unit, optional
        Speed at which to mix liquid in well before and/or after each
        transfer step

      """

      if isinstance(source, list):
        if len(source) == 1 and dest.container_type.well_count == 96:
          self.stamp(source[0]["container"], dest, volume)
        else:
          assert len(source) <= 4
          assert dest.container_type.well_count == 384, "You can only transfer the contents of multiple 96-well plates to a 384-well container"
          for x in source:
            assert x["container"].container_type.well_count == 96
          for s in source:
            self.transfer(s["container"].all_wells(),
                        dest.quadrant(s["quadrant"]),
                        volume,
                        False,
                        True,
                        mix_after,
                        mix_before,
                        mix_vol,
                        repetitions,
                        flowrate,
                        aspirate_speed,
                        dispense_speed,
                        aspirate_source,
                        dispense_target,
                        pre_buffer,
                        disposal_vol,
                        transit_vol,
                        blowout_buffer,
                        None,
                        new_group=True)
      elif source.container_type.well_count == 96:
        if dest.container_type.well_count == 96:
          self.transfer(source.all_wells(),
                        dest.all_wells(),
                        volume,
                        False,
                        True,
                        mix_after,
                        mix_before,
                        mix_vol,
                        repetitions,
                        flowrate,
                        aspirate_speed,
                        dispense_speed,
                        aspirate_source,
                        dispense_target,
                        pre_buffer,
                        disposal_vol,
                        transit_vol,
                        blowout_buffer,
                        None, new_group=True)
        else:
          raise RuntimeError("When transferring liquid from a 96-well container "
                             "to a 384-well container, you must specify the "
                             "source as a list of dictionaries in the form of "
                             "[{'container': <container>, 'quadrant': <quadrant>}]")
      elif isinstance(dest, list):
        assert len(dest) <= 4
        assert source.container_type.well_count == 384, "You can only transfer the contents of a 384-well container to multiple 96-well containers"
        for x in dest:
          assert x["container"].container_type.well_count == 96
        for d in dest:
          self.transfer(source.quadrant(d["quadrant"]),
                      d["container"].all_wells(),
                      volume,
                      False,
                      True,
                      mix_after,
                      mix_before,
                      mix_vol,
                      repetitions,
                      flowrate,
                      aspirate_speed,
                      dispense_speed,
                      aspirate_source,
                      dispense_target,
                      pre_buffer,
                      disposal_vol,
                      transit_vol,
                      blowout_buffer,
                      None,
                      new_group=True)
      elif source.container_type.well_count == 384:
        if dest.container_type.well_count == 384:
          self.transfer(source.all_wells(),
                        dest.all_wells(),
                        volume,
                        False,
                        True,
                        mix_after,
                        mix_before,
                        mix_vol,
                        repetitions,
                        flowrate,
                        aspirate_speed,
                        dispense_speed,
                        aspirate_source,
                        dispense_target,
                        pre_buffer,
                        disposal_vol,
                        transit_vol,
                        blowout_buffer,
                        None,
                        new_group=True)
      else:
        raise RuntimeError("Stamping is not supported for the container "
                           "types provided")

    def sangerseq(self, cont, wells, dataref):
      """
      Send the indicated wells of the container specified for Sanger sequencing.
      The specified wells should already contain the appropriate mix for
      sequencing, including primers and DNA according to the instructions
      provided by the vendor.

      Example Usage:

      .. code-block:: python

        p = Protocol()
        sample_plate = p.ref("sample_plate",
                             None,
                             "96-flat",
                             storage="warm_37")

        p.sangerseq(sample_plate,
                    sample_plate.wells_from(0,5).indices(),
                    "seq_data_022415")

      Autoprotocol Output:

      .. code-block:: json

        "instructions": [
            {
              "dataref": "seq_data_022415",
              "object": "sample_plate",
              "wells": [
                "A1",
                "A2",
                "A3",
                "A4",
                "A5"
              ],
              "op": "sangerseq"
            }
          ]


      Parameters
      ----------
      cont : Container, str
        Container with well(s) that contain material to be sequenced.
      wells : list of str
        Well indices of the container that contain appropriate materials to be
        sent for sequencing.
      dataref : str
        Name of sequencing dataset that will be returned.

      """
      self.instructions.append(SangerSeq(cont, wells, dataref))

    def serial_dilute_rowwise(self, source, well_group, vol,
                              mix_after=True, reverse=False):
        """
        Serial dilute source liquid in specified wells of the container
        specified. Defaults to dilute from left to right (increasing well index)
        unless reverse is set to true.  This operation utilizes the transfers()
        method on Pipette, meaning only one tip is used.  All wells in the
        WellGroup well_group except for the first and last well should already
        contain the diluent.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")
            sample_source = p.ref("sample_source",
                                  "ct32kj234l21g",
                                  "micro-1.5",
                                  storage="cold_20")

            p.serial_dilute_rowwise(sample_source.well(0),
                                    sample_plate.wells_from(0,12),
                                    "50:microliter",
                                    mix_after=True)

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "groups": [
                    {
                      "transfer": [
                        {
                          "volume": "100.0:microliter",
                          "to": "sample_plate/0",
                          "from": "sample_source/0"
                        }
                      ]
                    }
                  ],
                  "op": "pipette"
                },
                {
                  "groups": [
                    {
                      "transfer": [
                        {
                          "volume": "50.0:microliter",
                          "to": "sample_plate/1",
                          "from": "sample_plate/0",
                          "mix_after": {
                            "volume": "50.0:microliter",
                            "repetitions": 10,
                            "speed": "100:microliter/second"
                          }
                        },
                        {
                          "volume": "50.0:microliter",
                          "to": "sample_plate/2",
                          "from": "sample_plate/1",
                          "mix_after": {
                            "volume": "50.0:microliter",
                            "repetitions": 10,
                            "speed": "100:microliter/second"
                          }
                        },
                        {
                          "volume": "50.0:microliter",
                          "to": "sample_plate/3",
                          "from": "sample_plate/2",
                          "mix_after": {
                            "volume": "50.0:microliter",
                            "repetitions": 10,
                            "speed": "100:microliter/second"
                          }
                        },
                        {
                          "volume": "50.0:microliter",
                          "to": "sample_plate/4",
                          "from": "sample_plate/3",
                          "mix_after": {
                            "volume": "50.0:microliter",
                            "repetitions": 10,
                            "speed": "100:microliter/second"
                          }
                        },
                        {
                          "volume": "50.0:microliter",
                          "to": "sample_plate/5",
                          "from": "sample_plate/4",
                          "mix_after": {
                            "volume": "50.0:microliter",
                            "repetitions": 10,
                            "speed": "100:microliter/second"
                          }
                        },
                        {
                          "volume": "50.0:microliter",
                          "to": "sample_plate/6",
                          "from": "sample_plate/5",
                          "mix_after": {
                            "volume": "50.0:microliter",
                            "repetitions": 10,
                            "speed": "100:microliter/second"
                          }
                        },
                        {
                          "volume": "50.0:microliter",
                          "to": "sample_plate/7",
                          "from": "sample_plate/6",
                          "mix_after": {
                            "volume": "50.0:microliter",
                            "repetitions": 10,
                            "speed": "100:microliter/second"
                          }
                        },
                        {
                          "volume": "50.0:microliter",
                          "to": "sample_plate/8",
                          "from": "sample_plate/7",
                          "mix_after": {
                            "volume": "50.0:microliter",
                            "repetitions": 10,
                            "speed": "100:microliter/second"
                          }
                        },
                        {
                          "volume": "50.0:microliter",
                          "to": "sample_plate/9",
                          "from": "sample_plate/8",
                          "mix_after": {
                            "volume": "50.0:microliter",
                            "repetitions": 10,
                            "speed": "100:microliter/second"
                          }
                        },
                        {
                          "volume": "50.0:microliter",
                          "to": "sample_plate/10",
                          "from": "sample_plate/9",
                          "mix_after": {
                            "volume": "50.0:microliter",
                            "repetitions": 10,
                            "speed": "100:microliter/second"
                          }
                        },
                        {
                          "volume": "50.0:microliter",
                          "to": "sample_plate/11",
                          "from": "sample_plate/10",
                          "mix_after": {
                            "volume": "50.0:microliter",
                            "repetitions": 10,
                            "speed": "100:microliter/second"
                          }
                        }
                      ]
                    }
                  ],
                  "op": "pipette"
                }
            ]



        Parameters
        ----------
        container : Container
        source : Well
            Well containing source liquid.  Will be transfered to starting well,
            with double the volume specified in parameters
        start_well : Well
            Start of dilution, well containing the highest concentration of
            liquid
        end_well : Well
            End of dilution, well containing the lowest concentration of liquid
        vol : Unit, str
            Final volume of each well in the dilution series, most concentrated
            liquid will be transfered to the starting well with double this
            volume
        mix_after : bool, optional
            If set to True, each well will be mixed after liquid is transfered
            to it.
        reverse : bool, optional
            If set to True, liquid will be most concentrated in the well in the
            dilution series with the highest index

        """
        if not isinstance(well_group, WellGroup):
            raise RuntimeError("serial_dilute_rowwise() must take a WellGroup "
                "as an argument")
        source_well = well_group.wells[0]
        begin_dilute = well_group.wells[0]
        end_dilute = well_group.wells[-1]
        wells_to_dilute = well_group[0].container.wells_from(begin_dilute,
                                    end_dilute.index-begin_dilute.index + 1)
        srcs = WellGroup([])
        dests = WellGroup([])
        vols = []
        if reverse:
            source_well = well_group.wells[-1]
            begin_dilute = well_group.wells[-1]
            end_dilute = well_group.wells[0]
            wells_to_dilute = well_group[0].container.wells_from(end_dilute,
                                    begin_dilute.index-end_dilute.index + 1)
        self.transfer(source.set_volume(Unit.fromstring(vol)*2),
                      source_well,
                      Unit.fromstring(vol)*2)
        if reverse:
            while len(wells_to_dilute.wells) >= 2:
                srcs.append(wells_to_dilute.wells.pop())
                dests.append(wells_to_dilute.wells[-1])
                vols.append(vol)
        else:
            for i in range(1, len(wells_to_dilute.wells)):
                srcs.append(wells_to_dilute.wells[i-1])
                dests.append(wells_to_dilute[i])
                vols.append(vol)
        self.transfer(srcs.set_volume(Unit.fromstring(vol)*2), dests, vols,
                      mix_after=mix_after, one_tip=True)


    def mix(self, well, volume="50:microliter", speed="100:microliter/second",
            repetitions=10):
        """
        Mix specified well using a new pipette tip

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_source = p.ref("sample_source",
                                  None,
                                  "micro-1.5",
                                  storage="cold_20")

            p.mix(sample_source.well(0), volume="200:microliter",
                  repetitions=25)

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "groups": [
                    {
                      "mix": [
                        {
                          "volume": "200:microliter",
                          "well": "sample_source/0",
                          "repetitions": 25,
                          "speed": "100:microliter/second"
                        }
                      ]
                    }
                  ],
                  "op": "pipette"
                }
              ]
            }


        Parameters
        ----------
        well : str, Well, WellGroup
            Well(s) to be mixed. If a WellGroup is passed, each well in the
            group will be mixed using the specified parameters.
        volume : str, Unit, optional
            volume of liquid to be aspirated and expelled during mixing
        speed : str, Unit, optional
            flowrate of liquid during mixing
        repetitions : int, optional
            number of times to aspirate and expell liquid during mixing

        """
        if isinstance(well, Well) or isinstance(well, str):
            well = WellGroup([well])
        for w in well.wells:
            opts = {
                "well": w,
                "volume": volume,
                "speed": speed,
                "repetitions": repetitions
            }
            self._pipette([{"mix": [opts]}])

    def dispense(self, ref, reagent, columns):
        """
        Dispense specified reagent to specified columns.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")

            p.dispense(sample_plate,
                       "water",
                       [{"column": 0, "volume": "10:microliter"},
                        {"column": 1, "volume": "20:microliter"},
                        {"column": 2, "volume": "30:microliter"},
                        {"column": 3, "volume": "40:microliter"},
                        {"column": 4, "volume": "50:microliter"},
                        {"column": 5, "volume": "60:microliter"},
                        {"column": 6, "volume": "70:microliter"},
                        {"column": 7, "volume": "80:microliter"},
                        {"column": 8, "volume": "90:microliter"},
                        {"column": 9, "volume": "100:microliter"},
                        {"column": 10, "volume": "110:microliter"},
                        {"column": 11, "volume": "120:microliter"}
                       ])


        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "reagent": "water",
                  "object": "sample_plate",
                  "columns": [
                    {
                      "column": 0,
                      "volume": "10:microliter"
                    },
                    {
                      "column": 1,
                      "volume": "20:microliter"
                    },
                    {
                      "column": 2,
                      "volume": "30:microliter"
                    },
                    {
                      "column": 3,
                      "volume": "40:microliter"
                    },
                    {
                      "column": 4,
                      "volume": "50:microliter"
                    },
                    {
                      "column": 5,
                      "volume": "60:microliter"
                    },
                    {
                      "column": 6,
                      "volume": "70:microliter"
                    },
                    {
                      "column": 7,
                      "volume": "80:microliter"
                    },
                    {
                      "column": 8,
                      "volume": "90:microliter"
                    },
                    {
                      "column": 9,
                      "volume": "100:microliter"
                    },
                    {
                      "column": 10,
                      "volume": "110:microliter"
                    },
                    {
                      "column": 11,
                      "volume": "120:microliter"
                    }
                  ],
                  "op": "dispense"
                }
              ]

        Parameters
        ----------
        ref : Container, str
            Container for reagent to be dispensed to.
        reagent : str
            Reagent to be dispensed to columns in container.
        columns : list
            Columns to be dispensed to, in the form of a list of dicts specifying
            the column number and the volume to be dispensed to that column.
            Columns are expressed as integers indexed from 0.
            [{"column": <column num>, "volume": <volume>}, ...]

        """
        assert isinstance(columns, list)
        self.instructions.append(Dispense(ref, reagent, columns))

    def dispense_full_plate(self, ref, reagent, volume):
        """
        Dispense the specified amount of the specified reagent to every well
        of a container using a reagent dispenser.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")

            p.dispense_full_plate(sample_plate,
                                  "water",
                                  "100:microliter")

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "reagent": "water",
                  "object": "sample_plate",
                  "columns": [
                    {
                      "column": 0,
                      "volume": "100:microliter"
                    },
                    {
                      "column": 1,
                      "volume": "100:microliter"
                    },
                    {
                      "column": 2,
                      "volume": "100:microliter"
                    },
                    {
                      "column": 3,
                      "volume": "100:microliter"
                    },
                    {
                      "column": 4,
                      "volume": "100:microliter"
                    },
                    {
                      "column": 5,
                      "volume": "100:microliter"
                    },
                    {
                      "column": 6,
                      "volume": "100:microliter"
                    },
                    {
                      "column": 7,
                      "volume": "100:microliter"
                    },
                    {
                      "column": 8,
                      "volume": "100:microliter"
                    },
                    {
                      "column": 9,
                      "volume": "100:microliter"
                    },
                    {
                      "column": 10,
                      "volume": "100:microliter"
                    },
                    {
                      "column": 11,
                      "volume": "100:microliter"
                    }
                  ],
                  "op": "dispense"
                }
            ]



        Parameters
        ----------
        ref : Container
            Container for reagent to be dispensed to.
        reagent : {"water", "LB", "LB-amp", "LB-kan", "SOC", "PBS"}
            Reagent to be dispensed to columns in container.
        volume : Unit, str
            Volume of reagent to be dispensed to each well

        """
        columns = []
        for col in range(0,ref.container_type.col_count):
            columns.append({"column": col, "volume": volume})
        self.instructions.append(Dispense(ref, reagent, columns))

    def spin(self, ref, acceleration, duration):
        """
        Apply acceleration to a container.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")

            p.spin(sample_plate, "700:meter/second^2", "20:minute")

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "acceleration": "700:g",
                  "duration": "20:minute",
                  "object": "sample_plate",
                  "op": "spin"
                }
            ]

        Parameters
        ----------
        ref : str, Ref
            The plate to be centrifuged.
        acceleration: str, Unit
            Acceleration to be applied to the plate, in units of `g` or
            `meter/second^2`
        duration: str, Unit
            Length of time that accelleration should be applied

        """
        self.instructions.append(Spin(ref, acceleration, duration))

    def thermocycle(self, ref, groups,
                    volume="10:microliter",
                    dataref=None,
                    dyes=None,
                    melting_start=None,
                    melting_end=None,
                    melting_increment=None,
                    melting_rate=None):
        """
        Append a Thermocycle instruction to the list of instructions, with
        groups being a list of dicts in the formof:

        .. code-block:: python

            "groups": [{
                "cycles": integer,
                "steps": [{
                  "duration": duration,
                  "temperature": temperature,
                  "read": boolean // optional (default true)
                },{
                  "duration": duration,
                  "gradient": {
                    "top": temperature,
                    "bottom": temperature
                  },
                  "read": boolean // optional (default true)
                }]
            }],

        Example Usage:

        To thermocycle a container according to the protocol:
            * 1 cycle:
                * 95 degrees for 5 minutes
            * 30 cycles:
                * 95 degrees for 30 seconds
                * 56 degrees for 20 seconds
                * 72 degrees for 30 seconds
            * 1 cycle:
                * 72 degrees for 10 minutes

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-pcr",
                                 storage="warm_37")

            # a plate must be sealed before it can be thermocycled
            p.seal(sample_plate)

            p.thermocycle(sample_plate,
                          [
                           {"cycles": 1,
                            "steps": [{
                               "temperature": "95:celsius",
                               "duration": "5:minute",
                               }]
                            },
                            {"cycles": 35,
                                "steps": [
                                   {"temperature": "95:celsius",
                                    "duration": "30:second"},
                                   {"temperature": "56:celsius",
                                    "duration": "30:second"},
                                   {"temperature": "72:celsius",
                                    "duration": "20:second"}
                                   ]
                           },
                               {"cycles": 1,
                                   "steps": [
                                   {"temperature": "72:celsius", "duration":"10:minute"}]
                               }
                          ])

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "object": "sample_plate",
                  "op": "seal"
                },
                {
                  "volume": "10:microliter",
                  "dataref": null,
                  "object": "sample_plate",
                  "groups": [
                    {
                      "cycles": 1,
                      "steps": [
                        {
                          "duration": "5:minute",
                          "temperature": "95:celsius"
                        }
                      ]
                    },
                    {
                      "cycles": 35,
                      "steps": [
                        {
                          "duration": "30:second",
                          "temperature": "95:celsius"
                        },
                        {
                          "duration": "30:second",
                          "temperature": "56:celsius"
                        },
                        {
                          "duration": "20:second",
                          "temperature": "72:celsius"
                        }
                      ]
                    },
                    {
                      "cycles": 1,
                      "steps": [
                        {
                          "duration": "10:minute",
                          "temperature": "72:celsius"
                        }
                      ]
                    }
                  ],
                  "op": "thermocycle"
                }
              ]

        Parameters
        ----------
        ref : str, Ref
            Container to be thermocycled
        groups : list of dicts
            List of thermocycling instructions formatted as above
        volume : str, Unit, optional
            Volume contained in wells being thermocycled
        dataref : str, optional
            Name of dataref representing read data if performing qPCR
        dyes : dict, optional
            Dictionary mapping dye types to the wells they're used in
        melting_start: str, Unit
            Temperature at which to start the melting curve.
        melting_end: str, Unit
            Temperature at which to end the melting curve.
        melting_increment: str, Unit
            Temperature by which to increment the melting curve. Accepted increment
            values are between 0.1 and 9.9 degrees celsius.
        melting_rate: str, Unit
            Specifies the duration of each temperature step in the melting curve.

        Raises
        ------
        AttributeError
            if groups are not properly formatted

        """
        if not isinstance(groups, list):
            raise AttributeError(
                "groups for thermocycling must be a list of cycles in the "
                "form of [{'cycles':___, 'steps': [{'temperature':___,"
                "'duration':___, }]}, { ... }, ...]")
        self.instructions.append(
            Thermocycle(ref, groups, volume, dataref, dyes, melting_start,
                        melting_end, melting_increment, melting_rate))

    def thermocycle_ramp(self, ref, start_temp, end_temp, time,
                         step_duration="60:second"):
        """Append instructions representing a thermocyle ramp-up or ramp-down
        protocol based on start_temp and end_temp

        Parameters
        ----------
        ref : str, Ref
            Plate to be thermocycled
        start_temp : str, Unit
            starting temperature to ramp up or down from
        end_temp : str, Unit
            final temperature to ramp up or down to
        time : str, Unit
            total duration of thermocycle protocol
        step_duration : str, Unit, optional
            individual temperature step duration
        """
        start_temp = int(Unit.fromstring(start_temp).value)
        end_temp = int(Unit.fromstring(end_temp).value)
        time = int(Unit.fromstring(time).value)
        num_steps = time // Unit.fromstring(step_duration).value
        groups = []
        step_size = (end_temp - start_temp) // num_steps
        assert num_steps > 0
        for i in range(0, int(num_steps)):
            groups.append({
                "cycles": 1,
                "steps": [{
                    "temperature": "%d:celsius" % (start_temp + i * step_size),
                    "duration": step_duration,
                }]
            })

        self.instructions.append(Thermocycle(ref, groups))

    def incubate(self, ref, where, duration, shaking=False, co2=0):
        '''
        Move plate to designated thermoisolater or ambient area for incubation
        for specified duration.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-pcr",
                                 storage="warm_37")

            # a plate must be sealed/covered before it can be incubated
            p.seal(sample_plate)
            p.incubate(sample_plate, "warm_37", "1:hour", shaking=True)

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "object": "sample_plate",
                  "op": "seal"
                },
                {
                  "duration": "1:hour",
                  "where": "warm_37",
                  "object": "sample_plate",
                  "shaking": true,
                  "op": "incubate",
                  "co2_percent": 0
                }
              ]

        '''
        self.instructions.append(Incubate(ref, where, duration, shaking, co2))

    def plate_to_mag_adapter(self, ref, duration):
        """
        Transfer a plate to the magnetized slot on the liquid handler.
        Duration is the length of time to incubate the plate on the magnetic
        block before the pipetting operation takes place.

        Magnetic adapter instructions MUST be followed by Pipette instructions

        Example Usage:

        .. code-block:: python

          p.plate_to_mag_adapter(sample_plate, "5:minutes")
          p.transfer(sample_plate.well(0), sample_plate.well(1), "12:microliter")

        Autoprotocol Output:

        .. code-block:: json

          {
            "groups": [
              {
                "transfer": [
                  {
                    "volume": "12.0:microliter",
                    "to": "sample_plate/1",
                    "from": "sample_plate/0"
                  }
                ]
              }
            ],
            "x-magnetic_separate": {
              "duration": "5:minute",
              "object": "sample_plate"
            },
            "op": "pipette"
          }

        Parameters
        ----------
        ref : str, Ref
            plate to be transferred to magnetic adapter
        duration : str, Unit
            duration for plate to incubate on the magentic adapter (with no
            pipetting occuring)

        """
        sep = Pipette([])
        sep.data["x-magnetic_separate"] = {
            "object": ref,
            "duration": duration
        }
        self.instructions.append(sep)

    def plate_off_mag_adapter(self, ref):
        """
        Transfer a plate from the magnetized spot on the liquid handler to a
        non-magnetized one

        Magnetic adapter instructions MUST be followed by Pipette instructions

        Example Usage:

        .. code-block:: python

          p.plate_to_mag_adapter(sample_plate, "5:minutes")
          p.transfer(sample_plate.well(0), sample_plate.well(1), "12:microliter")
          p.plate_off_mag_adapter(sample_plate)
          p.transfer(sample_plate.well(13), sample_plate.well(1), "12:microliter")

        Autoprotocol Output:

        .. code-block:: json

          {
            "groups": [
              {
                "transfer": [
                  {
                    "volume": "12.0:microliter",
                    "to": "sample_plate/1",
                    "from": "sample_plate/0"
                  }
                ]
              }
            ],
            "x-magnetic_separate": {
              "duration": "5:minute",
              "object": "sample_plate"
            },
            "op": "pipette"
          },
          {
            "groups": [
              {
                "transfer": [
                  {
                    "volume": "12.0:microliter",
                    "to": "sample_plate/1",
                    "from": "sample_plate/13"
                  }
                ]
              }
            ],
            "op": "pipette"
          }

        Parameters
        ----------
        ref : str, Ref
            plate to be removed from magentic block

        """
        self.instructions.append(Pipette([]))

    def absorbance(self, ref, wells, wavelength, dataref, flashes=25):
        """
        Read the absorbance for the indicated wavelength for the indicated
        wells. Append an Absorbance instruction to the list of instructions for
        this Protocol object.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")

            p.absorbance(sample_plate, sample_plate.wells_from(0,12),
                         "600:nanometer", "test_reading", flashes=50)

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "dataref": "test_reading",
                  "object": "sample_plate",
                  "wells": [
                    "A1",
                    "A2",
                    "A3",
                    "A4",
                    "A5",
                    "A6",
                    "A7",
                    "A8",
                    "A9",
                    "A10",
                    "A11",
                    "A12"
                  ],
                  "num_flashes": 50,
                  "wavelength": "600:nanometer",
                  "op": "absorbance"
                }
              ]

        Parameters
        ----------
        ref : str, Ref
        wells : list, WellGroup
            WellGroup of wells to be measured or a list of well references in
            the form of ["A1", "B1", "C5", ...]
        wavelength : str, Unit
            wavelength of light absorbance to be read for the indicated wells
        dataref : str
            name of this specific dataset of measured absorbances
        flashes : int, optional

        """
        if isinstance(wells, WellGroup):
            wells = wells.indices()
        self.instructions.append(
            Absorbance(ref, wells, wavelength, dataref, flashes))

    def fluorescence(self, ref, wells, excitation, emission, dataref,
                     flashes=25):
        """
        Read the fluoresence for the indicated wavelength for the indicated
        wells.  Append a Fluorescence instruction to the list of instructions
        for this Protocol object.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")

            p.fluorescence(sample_plate, sample_plate.wells_from(0,12),
                           excitation="587:nanometer", emission="610:nanometer",
                           dataref="test_reading")

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "dataref": "test_reading",
                  "excitation": "587:nanometer",
                  "object": "sample_plate",
                  "emission": "610:nanometer",
                  "wells": [
                    "A1",
                    "A2",
                    "A3",
                    "A4",
                    "A5",
                    "A6",
                    "A7",
                    "A8",
                    "A9",
                    "A10",
                    "A11",
                    "A12"
                  ],
                  "num_flashes": 25,
                  "op": "fluorescence"
                }
              ]

        Parameters
        ----------
        ref : str, Container
            Container to plate read.
        wells : list, WellGroup
            WellGroup of wells to be measured or a list of well references in
            the form of ["A1", "B1", "C5", ...]
        excitation : str, Unit
            Wavelength of light used to excite the wells indicated
        emission : str, Unit
            Wavelength of light to be measured for the indicated wells
        dataref : str
            Name of this specific dataset of measured absorbances
        flashes : int, optional
            Number of flashes.

        """
        if isinstance(wells, WellGroup):
            wells = wells.indices()
        self.instructions.append(
            Fluorescence(ref, wells, excitation, emission, dataref, flashes))

    def luminescence(self, ref, wells, dataref):
        """
        Read luminescence of indicated wells.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")

            p.luminescence(sample_plate, sample_plate.wells_from(0,12),
                           "test_reading")

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "dataref": "test_reading",
                  "object": "sample_plate",
                  "wells": [
                    "A1",
                    "A2",
                    "A3",
                    "A4",
                    "A5",
                    "A6",
                    "A7",
                    "A8",
                    "A9",
                    "A10",
                    "A11",
                    "A12"
                  ],
                  "op": "luminescence"
                }
              ]

        Parameters
        ----------
        ref : str, Container
            Container to plate read.
        wells : list, WellGroup
            WellGroup or list of wells to be measured
        dataref : str
            Name of this dataset of measured luminescence readings.

        """
        if isinstance(wells, WellGroup):
            wells = wells.indices()
        self.instructions.append(Luminescence(ref, wells, dataref))

    def gel_separate(self, wells, volume, matrix, ladder, duration, dataref):
        """
        Separate nucleic acids on an agarose gel.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")

            p.gel_separate(sample_plate.wells_from(0,12), "10:microliter",
                           "agarose(8,0.8%)", "ladder1", "11:minute",
                           "genotyping_030214")

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "dataref": "genotyping_030214",
                  "matrix": "agarose(8,0.8%)",
                  "volume": "10:microliter",
                  "ladder": "ladder1",
                  "objects": [
                    "sample_plate/0",
                    "sample_plate/1",
                    "sample_plate/2",
                    "sample_plate/3",
                    "sample_plate/4",
                    "sample_plate/5",
                    "sample_plate/6",
                    "sample_plate/7",
                    "sample_plate/8",
                    "sample_plate/9",
                    "sample_plate/10",
                    "sample_plate/11"
                  ],
                  "duration": "11:minute",
                  "op": "gel_separate"
                }
            ]

        Parameters
        ----------
        wells : list, WellGroup
            List of string well references or WellGroup containing wells to be
            separated on gel.
        volume : str, Unit
            Volume of liquid to be transferred from each well specified to a
            lane of the gel.
        matrix : str
            Matrix (gel) in which to gel separate samples
        ladder : str
            Ladder by which to measure separated fragment size
        duration : str, Unit
            Length of time to run current through gel.
        dataref : str
            Name of this set of gel separation results.
        """
        max_well = int(matrix.split("(", 1)[1].split(",", 1)[0])
        if len(wells) > max_well:
          datarefs = 1
          for x in xrange(0, len(wells), max_well):
            self.gel_separate(wells[x:x+max_well], volume, matrix, ladder, duration,
                              "%s_%d" % (dataref, datarefs))
            datarefs += 1
        else:
          self.instructions.append(GelSeparate(wells, volume, matrix, ladder,
                                               duration, dataref))

    def seal(self, ref, type="ultra-clear"):
        """
        Seal indicated container using the automated plate sealer.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")

            p.seal(sample_plate)

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "object": "sample_plate",
                  "type": "ultra-clear"
                  "op": "seal"
                }
              ]

        Parameters
        ----------
        ref : Ref, str
          Container to be sealed
        type : str
          Seal type to be used, such as "ultra-clear" or "foil".

        """
        self.instructions.append(Seal(ref, type))

    def unseal(self, ref):
        """
        Remove seal from indicated container using the automated plate unsealer.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")
            # a plate must be sealed to be unsealed
            p.seal(sample_plate)

            p.unseal(sample_plate)

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "object": "sample_plate",
                  "op": "seal"
                },
                {
                  "object": "sample_plate",
                  "op": "unseal"
                }
              ]

        Parameters
        ----------
        ref : Ref, str
            Container to be unsealed

        """
        self.instructions.append(Unseal(ref))

    def cover(self, ref, lid='standard'):
        """
        Place specified lid type on specified container

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")
            p.cover(sample_plate, lid="universal")

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "lid": "universal",
                  "object": "sample_plate",
                  "op": "cover"
                }
              ]

        Parameters
        ----------
        ref : str
            Container to be convered
        lid : {"standard", "universal", "low-evaporation"}, optional
            Type of lid to cover container with

        """
        self.instructions.append(Cover(ref, lid))

    def uncover(self, ref):
        """
        Remove lid from specified container

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")
            # a plate must have a cover to be uncovered
            p.cover(sample_plate, lid="universal")

            p.uncover(sample_plate)

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "lid": "universal",
                  "object": "sample_plate",
                  "op": "cover"
                },
                {
                  "object": "sample_plate",
                  "op": "uncover"
                }
              ]

        Parameters
        ----------
        ref : str
            Container to remove lid from

        """
        self.instructions.append(Uncover(ref))

    def flow_analyze(self, dataref, FSC, SSC, neg_controls, samples,
                     colors=None, pos_controls=None):
      """
      Perform flow cytometry.The instruction will be executed within the voltage
      range specified for each channel, optimized for the best sample
      separation/distribution that can be achieved within these limits. The
      vendor will specify the device that this instruction is executed on and
      which excitation and emission spectra are available. At least one negative
      control is required, which will be used to define data acquisition
      parameters as well as to determine any autofluorescent properties for the
      sample set. Additional negative positive control samples are optional.
      Positive control samples will be used to optimize single color signals and,
      if desired, to minimize bleed into other channels.


      For each sample this instruction asks you to specify the `volume` and/or
      `captured_events`. Vendors might also require `captured_events` in case
      their device does not support volumetric sample intake. If both conditions
      are supported, the vendor will specify if data will be collected only until
      the first one is met or until both conditions are fulfilled.

      Example Usage:


      Autoprotocol Output:

      Parameters
      ----------
      dataref : str
          Name of flow analysis dataset generated.
      FSC : dict
          Dictionary containing FSC channel parameters in the form of:

          .. code-block:: json

              {
                "voltage_range": {
                  "low": "230:volt",
                  "high": "280:volt"
                  },
                "area": true,             //default: true
                "height": true,           //default: true
                "weight": false           //default: false
              }

      SSC : dict
          Dictionary of SSC channel parameters in the form of:

          .. code-block:: json

              {
                "voltage_range": {
                  "low": <voltage>,
                  "high": <voltage>"
                  },
                "area": true,             //default: true
                "height": true,           //default: false
                "weight": false           //default: false
              }

      neg_controls : list of dicts
          List of negative control wells in the form of:

          .. code-block:: json

              {
                  "well": well,
                  "volume": volume,
                  "captured_events": integer,     // optional, default infinity
                  "channel": [channel_name]
              }

          at least one negative control is required.
      samples : list of dicts
          List of samples in the form of:

          .. code-block:: json

              {
                  "well": well,
                  "volume": volume,
                  "captured_events": integer,     // optional, default infinity
              }

          at least one sample is required
      colors : list of dicts, optional
          Optional list of colors in the form of:

          .. code-block:: json

            [{
              "name": "FitC",
              "emission_wavelength": "495:nanometer",
              "excitation_wavelength": "519:nanometer",
              "voltage_range": {
                "low": <voltage>,
                "high": <voltage>
              },
              "area": true,             //default: true
              "height": false,          //default: false
              "weight": false           //default: false
            }, ... ]

      pos_controls : list of dicts, optional
          Optional list of positive control wells in the form of:

          .. code-block:: json

              [{
                  "well": well,
                  "volume": volume,
                  "captured_events": integer,     // optional, default infinity
                  "channel": [channel_name],
                  "minimize_bleed": [{            // optional
                    "from": color,
                    "to": [color]
                  }, ...
              ]

    """
      self.instructions.append(FlowAnalyze(dataref, FSC, SSC, neg_controls,
                                           samples, colors, pos_controls))

    def oligosynthesize(self, oligos):
        """
        Specify a list of oligonucleotides to be synthesized and a destination for each product.

        Example Usage:

        .. code-block:: python

            oligo_1 = p.ref("oligo_1", None, "micro-1.5", discard=True)

            p.oligosynthesize([{"sequence": "CATGGTCCCCTGCACAGG",
                                "destination": oligo_1.well(0),
                                "scale": "25nm",
                                "purification": "standard"}])

        Autoprotocol Output:

        .. code-block:: json

            "instructions": [
                {
                  "oligos": [
                    {
                      "destination": "oligo_1/0",
                      "sequence": "CATGGTCCCCTGCACAGG",
                      "scale": "25nm",
                      "purification": "standard"
                    }
                  ],
                  "op": "oligosynthesize"
                }
              ]

        Parameters
        ----------
        oligos : list of dicts
            List of oligonucleotides to synthesize.  Each dictionary should
            contain the oligo's sequence, destination, scale and purification

            .. code-block:: json

                [
                    {
                      "destination": "my_plate/A1",
                      "sequence": "GATCRYMKSWHBVDN",
                        // - standard IUPAC base codes
                        // - IDT also allows rX (RNA), mX (2' O-methyl RNA), and
                        //   X*/rX*/mX* (phosphorothioated)
                        // - they also allow inline annotations for modifications,
                        //   eg "GCGACTC/3Phos/" for a 3' phosphorylation
                        //   eg "aggg/iAzideN/cgcgc" for an internal modification
                      "scale": "25nm" | "100nm" | "250nm" | "1um",
                      "purification": "standard" | "page" | "hplc",
                        // default: standard
                    },
                    ...
                ]
        """
        self.instructions.append(Oligosynthesize(oligos))

    def spread(self, source, dest, volume):
      """
      Spread the specified volume of the source aliquot across the surace of the
      agar contained in the object container

      Example Usage:


      Autoprotocol Output:


      Parameters
      ----------
      source : str, Well
          Source of material to spread on agar
      dest : str, Well
          Reference to destination location (plate containing agar)
      volume : str, Unit
          Volume of source material to spread on agar

      """
      self.instructions.append(Spread(source, dest, volume))

    def autopick(self, source, dests, min_count=1):
      """
      Pick at least `min_count` colonies from the location specified in "from" to
      the location(s) specified in "to" in the order that they are specified
      until there are no more colonies available. If there are fewer than
      `min_count` colonies detected, the instruction will fail.

      Example Usage:


      Autoprotocol Output:


      Parameters
      ----------
      source : str, Well
          Reference to plate containing agar and colonies to pick
      dests : list of str, list of Well
          List of destination(s) for picked colonies
      min_count : int, optional
          Minimum number of colonies to detect in order to continue with
          autopicking

      """
      if isinstance(dests, Well) or isinstance(dests, str):
        dests = [dests]
      self.instructions.append(Autopick(source, dests, min_count))

    def _ref_for_well(self, well):
        return "%s/%d" % (self._ref_for_container(well.container), well.index)

    def _ref_for_container(self, container):
        for k in self.refs:
            v = self.refs[k]
            if v.container is container:
                return k

    @staticmethod
    def fill_wells(dst_group, src_group, volume, distribute_target):
        """
        Distribute liquid to a WellGroup, sourcing the liquid from a group
        of wells all containing the same substance.

        Parameters
        ----------
        dst_group : WellGroup
            WellGroup to distribute liquid to
        src_group : WellGroup
            WellGroup containing the substance to be distributed
        volume : str, Unit
            volume of liquid to be distributed to each destination well

        Returns
        -------
        distributes : list
            List of distribute groups

        Raises
        ------
        RuntimeError
            if source wells run out of liquid before distributing to all
            designated destination wells
        RuntimeError
            if length of list of volumes does not match the number of destination
            wells to be distributed to

        """

        src = None
        distributes = []
        src_group = WellGroup(src_group)
        dst_group = WellGroup(dst_group)
        if isinstance(volume, list):
            if len(volume) != len(dst_group.wells):
                raise RuntimeError("List length of volumes provided for "
                                   "distribution does not match the number of "
                                   " destination wells")
            volume = [Unit.fromstring(x) for x in volume]
        else:
            volume = [Unit.fromstring(volume)]*len(dst_group.wells)
        for d,v in list(zip(dst_group.wells, volume)):
            if len(distributes) == 0 or src.volume < v:
                # find a src well with enough volume
                src = next(
                    (w for w in src_group.wells if w.volume > v), None)
                if src is None:
                    raise RuntimeError(
                        "no well in source group has more than %s %s(s)" %
                        (str(v).rsplit(":")[0],str(v).rsplit(":")[1]))
                distributes.append({
                    "from": src,
                    "to": []
                })
            opts = {
              "well": d,
              "volume": v
            }
            if distribute_target:
              opts["distribute_target"] = distribute_target
            distributes[-1]["to"].append(opts)
            src.volume -= v
            if d.volume:
                d.volume += v
            else:
                d.volume = v
        return distributes

    def _pipette(self, groups):
        """Append given pipette groups to the protocol

        """
        if len(self.instructions) > 0 and \
                self.instructions[-1].op == 'pipette':
            self.instructions[-1].groups += groups
        else:
            self.instructions.append(Pipette(groups))

    def _refify(self, op_data):
        if type(op_data) is dict:
            return {k: self._refify(v) for k, v in op_data.items()}
        elif type(op_data) is list:
            return [self._refify(i) for i in op_data]
        elif isinstance(op_data, Well):
            return self._ref_for_well(op_data)
        elif isinstance(op_data, WellGroup):
            return [self._ref_for_well(w) for w in op_data.wells]
        elif isinstance(op_data, Container):
            return self._ref_for_container(op_data)
        elif isinstance(op_data, Unit):
            return str(op_data)
        else:
            return op_data

    def _ref_containers_and_wells(self, params):
        """
        Used by harness.run() to process JSON container and well references

        .. code-block:: python

            parameters = {
                "sample": {
                        "id": null,
                        "type": "micro-1.5",
                        "storage": "cold_4",
                        "discard": null
                },
                "mastermix_loc": "sample_plate/A1",
                "samples": [
                    "sample_plate/B1",
                    "sample_plate/B2",
                    "sample_plate/B3",
                    "sample_plate/B4"
                ]
            }

            protocol.make_well_references(parameters)

        returns:

        .. code-block:: python

            {
                "refs":{
                    "sample": Container(None, "micro-1.5")
                },
                "mastermix_loc": protocol.refs["sample_plate"].well("A1"),
                "samples": WellGroup([
                        protocol.refs["sample_plate"].well("B1"),
                        protocol.refs["sample_plate"].well("B2"),
                        protocol.refs["sample_plate"].well("B3"),
                        protocol.refs["sample_plate"].well("B4")
                    ])
            }

        Parameters
        ----------
        params : dict
            A dictionary of parameters to be passed to a protocol.

        """
        parameters = {}
        containers = {}

        # ref containers
        for k, v in params.items():
            if isinstance(v, dict):
                parameters[str(k)] = self._ref_containers_and_wells(v)
            if isinstance(v, list) and isinstance(v[0], dict):
                for cont in v:
                    self._ref_containers_and_wells(cont.encode('utf-8'))
            elif isinstance(v, dict) and "type" in v:
                if "discard" in v:
                    discard = v["discard"]
                    if discard and v.get("storage"):
                        raise RuntimeError("You must either specify a storage "
                                           "condition or set discard to true, "
                                           "not both.")
                else:
                    discard = False
                containers[str(k)] = \
                    self.ref(k, v["id"], v["type"], storage=v.get("storage"),
                             discard=discard)
            else:
                parameters[str(k)] = v

        parameters["refs"] = containers

        # ref wells (must be done after reffing containers)
        for k, v in params.items():
            if isinstance(v, list) and "/" in str(v[0]):
                group = WellGroup([])

                for w in v:
                    cont, well = w.rsplit("/", 1)
                    group.append(self.refs[cont].container.well(well))

                parameters[str(k)] = group
            elif "/" in str(v):
                ref_name = v.rsplit("/")[0]

                if not ref_name in self.refs:
                    raise RuntimeError(
                        "Parameters contain well references to "
                        "a container that isn't referenced in this protocol: "
                        "'%s'." % ref_name)

                if v.rsplit("/")[1] == "all_wells":
                    parameters[str(k)] = self.refs[ref_name].container.all_wells()
                else:
                    parameters[str(k)] = self.refs[ref_name].container.well(v.rsplit("/")[1])
            else:
                parameters[str(k)] = v

        return parameters
