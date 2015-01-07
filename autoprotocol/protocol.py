from .container import Container, Well, WellGroup
from .container_type import ContainerType, _CONTAINER_TYPES
from .unit import Unit
from .instruction import *


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
    method, which returns a Container:

        my_plate = protocol.ref("my_plate", id="ct1xae8jabbe6",
                                cont_type="96-pcr", storage="cold_4")

    To add instructions to the protocol, use the helper methods:

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
        """Convert a ContainerType shortname into a ContainerType object.

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
        """Append a Ref object to the list of Refs associated with this protocol
        and returns a Container with the id, container type and storage or
        discard conditions specified.

        Example
        -------
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
        """Append instruction(s) to the list of Instruction objects associated
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

    def distribute(self, source, dest, volume, allow_carryover=False):
        """Distribute liquid from source well(s) to destination wells(s)

        Parameters
        ----------
        source : Well, WellGroup
            Well or wells to distribute liquid from.  If passed as a WellGroup
            with set_volume() called on it, liquid will be automatically be
            drawn from the wells specified using the fill_wells function
        dest : Well, WellGroup
            Well or wells to distribute liquid to
        volume : str, Unit
            volume of liquid to be distributed to each destination well
        allow_carryover : bool, optional
            specify whether the same pipette tip can be used to aspirate more
            liquid from source wells after the previous volume aspirated has
            been depleted

        Raises
        ------
        RuntimeError
            if volume is not expressed either as a string with the format
            "value:unit" or as a Unit object
        """
        opts = {}
        opts["allow_carryover"] = allow_carryover
        if isinstance(source, WellGroup) and isinstance(dest, WellGroup):
            dists = self.fill_wells(dest, source, Unit.fromstring(volume))
            groups = []
            for d in dists:
                groups.append(
                    {"distribute": {
                        "from": d["from"],
                        "to": d["to"],
                        "allow_carryover": allow_carryover
                    }}
                )
            self.pipette(groups)
        elif isinstance(source, Well) and isinstance(dest, WellGroup):
            opts["from"] = source
            opts["to"] = []
            for well in dest.wells:
                opts["to"].append(
                    {"well": well, "volume": volume})
            self.pipette([{"distribute": opts}])
        elif isinstance(source, Well) and isinstance(dest, Well):
            opts["from"] = source
            opts["to"] = []
            opts["to"].append({"well": dest,
                "volume": volume})
            self.pipette([{"distribute": opts}])

    def transfer(self, source, dest, volume, mix_after=False,
                 mix_vol="20:microliter", repetitions=10,
                 flowrate="100:microliter/second", allow_carryover=False):
        """Transfer liquid from one specific well to another.  A new pipette tip
        is used between each transfer step.

        Parameters
        ----------
        source : Well, WellGroup
            Well or wells to transfer liquid from.  Expressing both source and
            dest as WellGroups appends transfer steps from each well in the
            source group to the well at the corresponding index in the list of
            destination wells.
        dest : Well, WellGroup
            Well or wells to transfer liquid to.
        volume : str, Unit
            volume of liquid to be transfered from one well to another
        mix_after : bool, optional
            set True to mix destination well using the same pipette tip
        mix_vol : str, optional
            volume to be aspirated and expelled during mixing
        repetitions : int, optional
            mix repititions
        flowrate : str, optional
            liquid flow rate during mixing

        Raises
        ------
        RuntimeError
            if transferring from WellGroup to WellGroup that have different
            number of wells
        RuntimeError
            if volume is passed as anything other than a string in the format
            "value:unit" or as a Unit object
        RuntimeError
            if source and/or destination wells are passed as anything other
            than Well or WellGroup objects
        """
        opts = []
        if isinstance(volume, basestring):
            volume = Unit.fromstring(volume)
        if volume > Unit(900,"microliter"):
            diff = Unit.fromstring(volume) - Unit(900,"microliter")
            self.transfer(source, dest, "900:microliter", mix_after,
                mix_vol, repetitions, flowrate)
            self.transfer(source, dest, diff, mix_after, mix_vol, repetitions,
                flowrate)
        elif isinstance(source, WellGroup) and isinstance(dest, WellGroup):
            if len(source.wells) != len(dest.wells):
                raise RuntimeError(
                    "source and destination WellGroups do not have the same "
                    "number of wells and transfer cannot happen one to one")
            else:
                for s,d in zip(source.wells, dest.wells):
                    self.transfer(s,d,volume)
        elif isinstance(source, Well) and isinstance(dest, WellGroup):
            for d in dest.wells:
                self.transfer(source, d, volume)
        elif isinstance(source, Well) and isinstance(dest, Well):
            xfer = {
                "from": source,
                "to": dest,
                "volume": volume
            }
            if mix_after:
                xfer["mix_after"] = {
                    "volume": mix_vol,
                    "repetitions": repetitions,
                    "speed": flowrate
                }
            opts.append(xfer)
        else:
            raise RuntimeError("transfer function must take Well or WellGroup "
                               "objects")
        if opts:
            self.pipette([{"transfer": opts}])

    def serial_dilute_rowwise(self, source, well_group, vol,
                                mix_after=True, reverse=False):
        """
        Serial dilute source liquid in specified wells of the container
        specified. Defaults to dilute from left to right (increasing well index) unless
        reverse is set to true.  This operation utilizes the transfers() method
        on Pipette, meaning only one tip is used.  All wells in the WellGroup
        well_group except for the first well and the last well should already
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
        mix_after : bool
            If set to True, each well will be mixed after liquid is transfered
            to it.
        reverse : bool
            If set to True, liquid will be most concentrated in the well in the
            dilution series with the highest index
        """
        if not isinstance(well_group, WellGroup):
            raise RuntimeError("serial_dilute_rowwise() must take a WellGroup "
                "as an argument")
        source_well = well_group.wells[0]
        begin_dilute = well_group.wells[0]
        end_dilute = well_group.wells[-1]
        wells_to_dilute = container.wells_from(begin_dilute,
            end_dilute.index-begin_dilute.index + 1)
        srcs = []
        dests = []
        vols = []
        if reverse:
            source_well = well_group.wells[-1]
            begin_dilute = well_group.wells[-1]
            end_dilute = well_group.wells[0]
            wells_to_dilute = container.wells_from(end_dilute,
                begin_dilute.index-end_dilute.index + 1)
        self.transfer(source, source_well,
            Unit.fromstring(vol)*Unit(2,"microliter"))
        if reverse:
            while len(wells_to_dilute.wells) >= 2:
                srcs.append(wells_to_dilute.wells.pop())
                dests.append(wells_to_dilute.wells[-1])
                vols.append(vol)
            self.append(Pipette(Pipette.transfers(srcs, dests, vols,
                mix_after=mix_after)))
        else:
            for i in range(1, len(wells_to_dilute.wells)):
                srcs.append(wells_to_dilute.wells[i-1])
                dests.append(wells_to_dilute[i])
                vols.append(vol)
            self.append(Pipette(Pipette.transfers(srcs, dests, vols,
                mix_after=mix_after)))

    def mix(self, well, volume="50:microliter", speed="100:microliter/second",
            repetitions=10):
        """Mix specified well using a new pipette tip

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

    def spin(self, ref, speed, duration):
        """Append a Spin Instruction to the instructions list

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
        groups being a list of dicts in the form of:
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
            if groups are not in the form of:
                [{
                    'cycles':___,
                    'steps': [
                        {'temperature':___,"
                            'duration':___,
                        },
                        { ... }
                    ]},
                    { ... }, ...
                }]
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
        self.instructions.append(Incubate(ref, where, duration, shaking))

    def plate_to_mag_adapter(self, ref, duration):
        """Transfer a plate to the magnetized slot on the liquid handler

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
        """Transfer a plate from the magnetized spot on the liquid handler to a
        non-magnetized one

        Magnetic adapter instructions MUST be followed by Pipette instructions

        Parameters
        ----------
        ref : str, Ref
            plate to be removed from magentic block
        """
        self.instructions.append(Pipette([]))

    def absorbance(self, ref, wells, wavelength, dataref, flashes=25):
        """Reads the absorbance for the indicated wavelength for the indicated
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
            wells = wells.indices(human=True)
        self.instructions.append(
            Absorbance(ref, wells, wavelength, dataref, flashes))

    def fluorescence(self, ref, wells, excitation, emission, dataref,
                     flashes=25):
        """Read the fluoresence for the indicated wavelength for the indicated
        wells.  Append a Fluorescence instruction to the list of instructions
        for this Protocol object.

        Parameters
        ----------
        ref : str, Container
        wells : list, WellGroup
            WellGroup of wells to be measured or a list of well references in
            the form of ["A1", "B1", "C5", ...]
        excitation : str, Unit
            wavelength of light used to excite the wells indicated
        emission : str, Unit
            wavelength of light to be measured for the indicated wells
        dataref : str
            name of this specific dataset of measured absorbances
        flashes : int, optional
        """
        if isinstance(wells, WellGroup):
            wells = wells.indices()
        self.instructions.append(
            Fluorescence(ref, wells, excitation, emission, dataref, flashes))

    def luminesence(self, ref, wells, dataref):
        """
        Parameters
        ----------
        ref : str, Container
        wells : list, WellGroup
            WellGroup or list of wells to be measured
        dataref : str
        """
        if isinstance(wells, WellGroup):
            wells = wells.indices()
        self.instructions.append(Luminesence(refs, wells, dataref))

    def gel_separate(self, ref, matrix, ladder, duration, dataref):
        """
        Parameters
        ----------
        ref : str, Container
            reference to be gel separated
        matrix : {'agarose(96,2.0%)', 'agarose(48,4.0%)', 'agarose(48,2.0%)',
                  'agarose(12,1.2%)', 'agarose(8,0.8%)'}
            matrix in which to gel separate samples
        ladder : {'ladder1', 'ladder2'}
            ladder by which to measure separated fragment size
        duration : str, Unit
        dataref : str
        """
        self.instructions.append(
            GelSeparate(ref, matrix, ladder, duration, dataref))

    def seal(self, ref):
        self.instructions.append(Seal(ref))

    def unseal(self, ref):
        self.instructions.append(Unseal(ref))

    def cover(self, ref, lid='standard'):
        self.instructions.append(Cover(ref, lid))

    def uncover(self, ref):
        self.instructions.append(Uncover(ref))

    def _ref_for_well(self, well):
        return "%s/%d" % (self._ref_for_container(well.container), well.index)

    def _ref_for_container(self, container):
        for k, v in self.refs.iteritems():
            if v.container is container:
                return k

    def fill_wells(self, dst_group, src_group, volume):
        """Distribute liquid to a WellGroup, sourcing the liquid from a group
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
        distirbutes : list


        Raises
        ------
        RuntimeError
            if source wells run out of liquid before distributing to all
            designated destination wells

        """
        src = None
        distributes = []

        for d in dst_group.wells:
            if len(distributes) == 0 or src.volume < volume:
                # find a src well with enough volume
                src = next(
                    (w for w in src_group.wells if w.volume > volume), None)
                if src is None:
                    raise RuntimeError(
                        "no well in source group has more than %s" %
                        str(volume))
                distributes.append({
                    "from": self._refify(src),
                    "to": []
                })
            distributes[-1]["to"].append({
                "well": self._ref_for_well(d),
                "volume": str(volume)
            })
            src.volume -= volume
            if d.volume:
                d.volume += volume
            else:
                d.volume = volume
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
        """Used by harness.run() to process JSON container and well references

        Example
        -------

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
        """
        parameters = {}
        containers = {}

        #ref containers
        for k, v in params.items():
            if isinstance(v, dict):
                parameters[str(k)] = self._ref_containers_and_wells(v)
            if isinstance(v, list) and isinstance(v[0], dict):
                for cont in v:
                    self._ref_containers_and_wells(cont.encode('utf-8'))
            elif isinstance(v, dict) and "type" in v:
                if "discard" in v:
                    discard = v["discard"]
                    if discard and v["storage"]:
                        raise RuntimeError("You must either specify a storage "
                            "condition or set discard to true, not both.")
                else:
                    discard = False
                containers[str(k)] = \
                    self.ref(k, v["id"], v["type"], storage=v["storage"],
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
                if not v.rsplit("/")[0] in self.refs:
                    raise RuntimeError("Parameters contain well references to \
                        a container that isn't referenced in this protocol.")
                if v.rsplit("/")[1] == "all_wells":
                    parameters[str(k)] = self.refs[v.rsplit("/")[0]].container.all_wells()
                else:
                    parameters[str(k)] = self.refs[v.rsplit("/")[0]].container.well(v.rsplit("/")[1])
            else:
                parameters[str(k)] = v

        return parameters
