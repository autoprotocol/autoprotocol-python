from .container import Container, Well, WellGroup
from .container_type import ContainerType, _CONTAINER_TYPES
from .unit import Unit
from .instruction import *

'''
    :copyright: 2015 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''


class Ref(object):
    """Link a ref name (string) to a Container instance.

    """
    def __init__(self, name, opts, container):
        assert "/" not in name
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

            my_plate = protocol.ref("my_plate", id="ct1xae8jabbe6",
                                    cont_type="96-pcr", storage="cold_4")

    To add instructions to the protocol, use the helper methods in this class

        .. code-block:: python

            protocol.transfer(source=my_plate.well("A1"),
                              dest=my_plate.well("B4"),
                              volume="50:microliter")
            protocol.thermocycle(my_plate, groups=[
                { "cycles": 1,
                  "steps": [
                    { "temperature": "95:celsius", "duration": "1:hour" }
                    ]
                  }
                ])

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
            string representing one of the ContainerTypes in the
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
            if an unknown ContainerType shortname is passed as a parameter

        """
        if shortname in _CONTAINER_TYPES:
            return _CONTAINER_TYPES[shortname]
        elif isinstance(shortname, ContainerType):
            return shortname
        else:
            raise ValueError("Unknown container type %s (known types=%s)" %
                             (shortname, str(_CONTAINER_TYPES.keys())))

    def ref(self, name, id=None, cont_type=None, storage=None, discard=None):
        """
        Append a Ref object to the list of Refs associated with this protocol
        and returns a Container with the id, container type and storage or
        discard conditions specified.

        Ex)

        .. code-block:: python

            sample_ref = ref("sample_plate", cont_type="96-pcr", discard=True)
            sample_ref = ref("sample_plate", id="ct1cxae33lkj",
                             cont_type="96-pcr", storage="ambient")

        returns a Container object using Container(None, "96-pcr")

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
        assert storage or discard
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
        with this protocol

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

        Returns
        -------
        dict
            dict with keys "refs" and "instructions", each of which contain
            the "refified" contents of their corresponding Protocol attribute

        """
        return {
            "refs": dict(map(lambda (k, v): (k, v.opts), self.refs.items())),
            "instructions": map(lambda x: self._refify(x.data),
                                self.instructions)
        }

    def pipette(self, groups):
        """Append given pipette groups to the protocol

        Parameters
        ----------
        groups : list of dicts
            a list of "distribute" and/or "transfer" instructions to be passed
            to a Pipette object, which is then appended to this protocol's
            instructions attribute

        """
        if len(self.instructions) > 0 and \
                self.instructions[-1].op == 'pipette':
            self.instructions[-1].groups += groups
        else:
            self.instructions.append(Pipette(groups))


    def distribute(self, source, dest, volume, allow_carryover=False,
                   mix_before=False, mix_vol=None, repetitions=10,
                   flowrate="100:microliter/second"):
        """
        Distribute liquid from source well(s) to destination wells(s)

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

        Raises
        ------
        RuntimeError
            If no mix volume is specified for the mix_before instruction
        ValueError
            If source and destination well(s) is/are not expressed as either
            Wells or WellGroups

        """
        opts = {}
        dists = self.fill_wells(dest, source, volume)
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
            groups.append(
                {"distribute": opts}
            )

        self.pipette(groups)

    def transfer(self, source, dest, volume, one_source=False, one_tip=False,
                 mix_after=False, mix_before=False, mix_vol=None,
                 repetitions=10, flowrate="100:microliter/second"):
        """
        Transfer liquid from one specific well to another.  A new pipette tip
        is used between each transfer step.

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
        if len(source.wells) > 1 and len(dest.wells) == 1:
            dest = WellGroup(dest.wells * len(source.wells))
        if isinstance(volume,str) or isinstance(volume, Unit):
            volume = [Unit.fromstring(volume)] * len(dest.wells)
        elif isinstance(volume, list) and len(volume) == len(dest.wells):
            volume = map(lambda x: Unit.fromstring(x), volume)
        else:
            raise RuntimeError("Unless the same volume of liquid is being "
                               "transferred to each destination well, each "
                               "destination well must have a corresponding "
                               "volume")
        if (len(volume) != len (dest.wells)) and (len(dest.wells) != len(volume)) and not one_source:
            raise RuntimeError("To transfer liquid from multiple wells "
                               "containing the same source, set one_source to "
                               "True.  Otherwise, you must specify the same "
                               "number of source and destinationi wells to "
                               "do a one-to-one transfer.")
        elif one_source:
            sources = []
            for idx, d in enumerate(dest.wells):
                for s in source.wells:
                    while s.volume > volume[idx] and (len(sources) < len(dest.wells)):
                        sources.append(s)
                        s.volume -= volume[idx]
            source = WellGroup(sources)

        for s,d,v in list(zip(source.wells, dest.wells, volume)):
            if mix_after and not mix_vol:
                mix_vol = v
            if v > Unit(900, "microliter"):
                diff = Unit.fromstring(vol) - Unit(900, "microliter")
                self.transfer(s, d, "900:microliter", mix_after,
                              mix_vol, repetitions, flowrate)
                self.transfer(s, d, diff, one_source, one_tip, mix_after,
                              mix_vol, repetitions, flowrate)
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
            opts.append(xfer)
            if d.volume:
                d.volume += v
            else:
                d.volume = v
            if s.volume:
                s.volume -= v
        if one_tip:
            self.append(Pipette([{"transfer": opts}]))
        else:
            for x in opts:
                self.pipette([{"transfer": [x]}])


    def serial_dilute_rowwise(self, source, well_group, vol,
                              mix_after=True, reverse=False):
        """
        Serial dilute source liquid in specified wells of the container
        specified. Defaults to dilute from left to right (increasing well index)
        unless reverse is set to true.  This operation utilizes the transfers()
        method on Pipette, meaning only one tip is used.  All wells in the
        WellGroup well_group except for the first and last well should already
        contain the diluent.

        Parameters
        ----------
        container : Container
        source : Well
            Well containing source liquid.  Will be transfered to starting well
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
            self.transfer(srcs.set_volume(Unit.fromstring(vol)*Unit(2,
                          "microliter")), dests, vols, mix_after=mix_after)

        else:
            for i in range(1, len(wells_to_dilute.wells)):
                srcs.append(wells_to_dilute.wells[i-1])
                dests.append(wells_to_dilute[i])
                vols.append(vol)
            self.transfer(srcs.set_volume(Unit.fromstring(vol)*2), dests, vols, mix_after=mix_after)


    def mix(self, well, volume="50:microliter", speed="100:microliter/second",
            repetitions=10):
        """
        Mix specified well using a new pipette tip

        Parameters
        ----------
        well : str, Well
            well to be mixed
        volume : str, Unit, optional
            volume of liquid to be aspirated and expelled during mixing
        speed : str, Unit, optional
            flowrate of liquid during mixing
        repetitions : int, optional
            number of times to aspirate and expell liquid during mixing

        """
        opts = {
            "well": well,
            "volume": volume,
            "speed": speed,
            "repetitions": repetitions
        }
        self.pipette([{"mix": [opts]}])

    def dispense(self, ref, reagent, columns):
        """
        Dispense specified reagent to specified columns.

        Parameters
        ----------
        ref : Container, str
            Container for reagent to be dispensed to.
        reagent : {"water", "LB", "LB-amp", "LB-kan", "SOC", "PBS"}
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
        Dispense specified reagent to every well of specified container using the
        reagent dispenser.

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

    def spin(self, ref, speed, duration):
        """
        Append a Spin Instruction to the instructions list

        Parameters
        ----------
        ref : str, Ref
        speed: str, Unit
        duration: str, Unit

        """
        self.instructions.append(Spin(ref, speed, duration))

    def thermocycle(self, ref, groups,
                    volume="10:microliter",
                    dataref=None,
                    dyes=None,
                    melting=None):
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

        Parameters
        ----------
        ref : str, Ref
        groups : list of dicts
        volume : str, Unit, optional
        dataref : str, optional
        dyes : list, optional
        melting : str, Unit, optional

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
            Thermocycle(ref, groups, volume, dataref, dyes, melting))

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

    def incubate(self, ref, where, duration, shaking=False):
        '''
        Move plate to designated thermoisolater or ambient area for incubation
        for specified duration.

        '''
        self.instructions.append(Incubate(ref, where, duration, shaking))

    def plate_to_mag_adapter(self, ref, duration):
        """
        Transfer a plate to the magnetized slot on the liquid handler

        Magnetic adapter instructions MUST be followed by Pipette instructions

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
        Read luminescence of indicated wells

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

    def gel_separate(self, wells, matrix, ladder, duration, dataref):
        """
        Separate nucleic acids on an agarose gel.

        Parameters
        ----------
        wells : list, WellGroup
            List of string well references or WellGroup containing wells to be
            separated on gel
        matrix : {'agarose(96,2.0%)', 'agarose(48,4.0%)', 'agarose(48,2.0%)',
                  'agarose(12,1.2%)', 'agarose(8,0.8%)'}
            Matrix in which to gel separate samples
        ladder : {'ladder1', 'ladder2'}
            Ladder by which to measure separated fragment size
        duration : str, Unit
            Length of time to run current through gel.
        dataref : str
            Name of this set of gel separation results.
        """
        self.instructions.append(
            GelSeparate(wells, matrix, ladder, duration, dataref))

    def seal(self, ref):
        """
        Seal indicated container using the automated plate sealer.

        Parameters
        ----------
        ref : Ref, str
            Container to be sealed

        """
        self.instructions.append(Seal(ref))

    def unseal(self, ref):
        """
        Remove seal from indicated container using the automated plate unsealer.

        Parameters
        ----------
        ref : Ref, str
            Container to be unsealed

        """
        self.instructions.append(Unseal(ref))

    def cover(self, ref, lid='standard'):
        """
        Place specified lid type on specified container

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

        Parameters
        ----------
        ref : str
            Container to remove lid from

        """
        self.instructions.append(Uncover(ref))

    def _ref_for_well(self, well):
        return "%s/%d" % (self._ref_for_container(well.container), well.index)

    def _ref_for_container(self, container):
        for k, v in self.refs.iteritems():
            if v.container is container:
                return k

    def fill_wells(self, dst_group, src_group, volume):
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
            distributes[-1]["to"].append({
                "well": d,
                "volume": v
            })
            src.volume -= v
            if d.volume:
                d.volume += v
            else:
                d.volume = v
        return distributes

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


        #ref wells (must be done after reffing containers)
        for k, v in params.items():
            if isinstance(v, list) and "/" in str(v[0]):
                group = WellGroup([])
                for w in v:
                    cont = w.rsplit("/")[0].encode('utf-8')
                    well = w.rsplit("/")[1].encode('utf-8')
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
