"""
Module containing the main `Protocol` object and associated functions

    :copyright: 2020 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""

import warnings

from .constants import AGAR_CLLD_THRESHOLD, SPREAD_PATH
from .container import Container, Well, SEAL_TYPES, COVER_TYPES
from .container_type import ContainerType, _CONTAINER_TYPES
from .instruction import *  # pylint: disable=unused-wildcard-import
from .liquid_handle import Transfer, Mix, LiquidClass
from .unit import Unit, UnitError
from .util import _validate_as_instance, _check_container_type_with_shape


class Ref(object):

    """
    Link a ref name (string) to a Container instance.

    """

    def __init__(self, name, opts, container):
        self.name = name
        self.opts = opts
        self.container = container

    def __repr__(self):
        return f"Ref({self.name}, {self.container}, {self.opts})"


# noinspection PyCompatibility
class Protocol(object):
    """
    A Protocol is a sequence of instructions to be executed, and a set of
    containers on which those instructions act.

    Parameters
    ----------
    refs : list(Ref)
        Pre-existing refs that the protocol should be populated with.
    instructions : list(Instruction)
        Pre-existing instructions that the protocol should be populated with.
    propagate_properties : bool, optional
        Whether liquid handling operations should propagate aliquot properties
        from source to destination wells.
    time_constraints : List(time_constraints)
        Pre-existing time_constraints that the protocol should be populated with.

    Examples
    --------
    Initially, a Protocol has an empty sequence of instructions and no
    referenced containers. To add a reference to a container, use the ref()
    method, which returns a Container.

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

    def __init__(
        self,
        refs=None,
        instructions=None,
        propagate_properties=False,
        time_constraints=None,
    ):
        super(Protocol, self).__init__()
        self.refs = refs or {}
        self.instructions = instructions or []
        self.propagate_properties = propagate_properties
        self.time_constraints = time_constraints or []

    def __repr__(self):
        return f"Protocol({self.__dict__})"

    def container_type(self, shortname):
        """
        Convert a ContainerType shortname into a ContainerType object.

        Parameters
        ----------
        shortname : str
            String representing one of the ContainerTypes in the
            _CONTAINER_TYPES dictionary.

        Returns
        -------
        ContainerType
            Returns a Container type object corresponding to the shortname
            passed to the function.  If a ContainerType object is passed,
            that same ContainerType is returned.

        Raises
        ------
        ValueError
            If an unknown ContainerType shortname is passed as a parameter.

        """
        if isinstance(shortname, ContainerType):
            return shortname
        elif shortname in _CONTAINER_TYPES:
            return _CONTAINER_TYPES[shortname]
        else:
            raise ValueError(
                f"Unknown container type {shortname}"
                f"(known types={str(_CONTAINER_TYPES.keys())})"
            )

    # pragma pylint: disable=redefined-builtin
    def ref(
        self, name, id=None, cont_type=None, storage=None, discard=None, cover=None
    ):
        """
        Add a Ref object to the dictionary of Refs associated with this protocol
        and return a Container with the id, container type and storage or
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
            name of the container/ref being created.
        id : str, optional
            id of the container being created, from your organization's
            inventory on http://secure.transcriptic.com.  Strings representing
            ids begin with "ct".
        cont_type : str or ContainerType
            container type of the Container object that will be generated.
        storage : Enum({"ambient", "cold_20", "cold_4", "warm_37"}), optional
            temperature the container being referenced should be stored at
            after a run is completed.  Either a storage condition must be
            specified or discard must be set to True.
        discard : bool, optional
            if no storage condition is specified and discard is set to True,
            the container being referenced will be discarded after a run.
        cover: str, optional
            name of the cover which will be on the container/ref

        Returns
        -------
        Container
            Container object generated from the id and container type provided

        Raises
        ------
        RuntimeError
            If a container previously referenced in this protocol (existent
            in refs section) has the same name as the one specified.
        RuntimeError
            If no container type is specified.
        RuntimeError
            If no valid storage or discard condition is specified.

        """

        if name in self.refs.keys():
            raise RuntimeError(
                "Two containers within the same protocol cannot have the same " "name."
            )
        opts = {}

        # Check container type
        try:
            cont_type = self.container_type(cont_type)
            if id and cont_type:
                opts["id"] = id
            elif cont_type:
                opts["new"] = cont_type.shortname
        except ValueError:
            raise RuntimeError(f"{cont_type} is not a recognized container type.")

        if storage:
            opts["store"] = {"where": storage}
        elif discard and not storage:
            opts["discard"] = discard
        else:
            raise RuntimeError(
                "You must specify either a valid storage condition or set "
                "discard=True for a Ref."
            )

        if cover:
            opts["cover"] = cover

        container = Container(
            id,
            cont_type,
            name=name,
            storage=storage if storage else None,
            cover=cover if cover else None,
        )
        self.refs[name] = Ref(name, opts, container)
        return container

    # pragma pylint: enable=redefined-builtin

    def add_time_constraint(
        self,
        from_dict,
        to_dict,
        less_than=None,
        more_than=None,
        mirror=False,
        ideal=None,
        optimization_cost=None,
    ):
        """Constraint the time between two instructions

        Add time constraints from `from_dict` to `to_dict`. Time constraints
        guarantee that the time from the `from_dict` to the `to_dict` is less
        than or greater than some specified duration. Care should be taken when
        applying time constraints as constraints may make some protocols
        impossible to schedule or run.

        Though autoprotocol orders instructions in a list, instructions do
        not need to be run in the order they are listed and instead depend on
        the preceding dependencies. Time constraints should be added with such
        limitations in mind.

        Constraints are directional; use `mirror=True` if the time constraint
        should be added in both directions. Note that mirroring is only applied
        to the less_than constraint, as the more_than constraint implies both a
        minimum delay betweeen two timing points and also an explicit ordering
        between the two timing points.

        Ideal time constraints are sometimes helpful for ensuring that a certain
        set of operations happen within some specified time. This can be specified
        by using the `ideal` parameter. There is an optional `optimization_cost`
        parameter associated with `ideal` time constraints for specifying the
        penalization system used for calculating deviations from the `ideal` time.
        When left unspecified, the `optimization_cost` function defaults to linear.
        Please refer to the ASC for more details on how this is implemented.

        Example Usage:

        .. code-block:: python

            plate_1 = protocol.ref("plate_1", id=None, cont_type="96-flat",
                                   discard=True)
            plate_2 = protocol.ref("plate_2", id=None, cont_type="96-flat",
                                   discard=True)

            protocol.cover(plate_1)
            time_point_1 = protocol.get_instruction_index()

            protocol.cover(plate_2)
            time_point_2 = protocol.get_instruction_index()

            protocol.add_time_constraint(
                {"mark": plate_1, "state": "start"},
                {"mark": time_point_1, "state": "end"},
                less_than = "1:minute")
            protocol.add_time_constraint(
                {"mark": time_point_2, "state": "start"},
                {"mark": time_point_1, "state": "start"},
                less_than = "1:minute", mirror=True)

            # Ideal time constraint
            protocol.add_time_constraint(
                {"mark": time_point_1, "state": "start"},
                {"mark": time_point_2, "state": "end"},
                ideal = "30:second",
                optimization_cost = "squared")


        Autoprotocol Output:

        .. code-block:: json

            {
                "refs": {
                    "plate_1": {
                        "new": "96-flat",
                        "discard": true
                    },
                    "plate_2": {
                        "new": "96-flat",
                        "discard": true
                    }
                },
                "time_constraints": [
                    {
                        "to": {
                            "instruction_end": 0
                        },
                        "less_than": "1.0:minute",
                        "from": {
                            "ref_start": "plate_1"
                        }
                    },
                    {
                        "to": {
                            "instruction_start": 0
                        },
                        "less_than": "1.0:minute",
                        "from": {
                            "instruction_start": 1
                        }
                    },
                    {
                        "to": {
                            "instruction_start": 1
                        },
                        "less_than": "1.0:minute",
                        "from": {
                            "instruction_start": 0
                        }
                    },
                    {
                        "from": {
                            "instruction_start": 0
                        },
                        "to": {
                            "instruction_end": 1
                        },
                        "ideal": {
                            "value": "5:minute",
                            "optimization_cost": "squared"
                        }
                    }

                ],
                "instructions": [
                    {
                        "lid": "standard",
                        "object": "plate_1",
                        "op": "cover"
                    },
                    {
                        "lid": "standard",
                        "object": "plate_2",
                        "op": "cover"
                    }
                ]
            }


        Parameters
        ----------
        from_dict: dict
            Dictionary defining the initial time constraint condition.
            Composed of keys: "mark" and "state"

            mark: int or Container
                instruction index of container
            state: "start" or "end"
                specifies either the start or end of the "mark" point

        to_dict: dict
            Dictionary defining the end time constraint condition.
            Specified in the same format as from_dict
        less_than: str or Unit, optional
            max time between from_dict and to_dict
        more_than: str or Unit, optional
            min time between from_dict and to_dict
        mirror: bool, optional
            choice to mirror the from and to positions when time constraints
            should be added in both directions
            (only applies to the less_than constraint)
        ideal: str or Unit, optional
            ideal time between from_dict and to_dict
        optimization_cost: Enum({"linear", "squared", "exponential"}), optional
            cost function used for calculating the penalty for missing the
            `ideal` timing

        Raises
        ------
        ValueError
            If an instruction mark is less than 0
        TypeError
            If mark is not container or integer
        TypeError
            If state not in ['start', 'end']
        TypeError
            If any of `ideal`, `more_than`, `less_than` is not a
            Unit of the 'time' dimension
        KeyError
            If `to_dict` or `from_dict` does not contain 'mark'
        KeyError
            If `to_dict` or `from_dict` does not contain 'state'
        ValueError
            If time is less than '0:second'
        ValueError
            If `optimization_cost` is specified but `ideal` is not
        ValueError
            If `more_than` is greater than `less_than`
        ValueError
            If `ideal` is smaller than `more_than` or greater than
            `less_than`
        RuntimeError
            If `from_dict` and `to_dict` are equal
        RuntimeError
            If from_dict["marker"] and to_dict["marker"] are equal and
            from_dict["state"] = "end"

        """

        inst_string = "instruction_"
        cont_string = "ref_"

        state_strings = ["start", "end"]

        keys = []

        # Move the 4th param to mirror if the caller used the syntax
        # add_time_constraint(a, b, 1:minute, True)
        if type(more_than) == bool:
            mirror = more_than
            more_than = None

        # Validate input types
        def validate_timing(constraint):
            if constraint is not None:
                constraint = parse_unit(constraint, "minute")
                if constraint < Unit(0, "second"):
                    raise ValueError(
                        f"The timing constraint {constraint} cannot be "
                        "less than '0:second'"
                    )
            return constraint

        more_than = validate_timing(more_than)
        less_than = validate_timing(less_than)
        ideal = validate_timing(ideal)

        if ideal and optimization_cost is None:
            optimization_cost = "linear"

        if optimization_cost is not None:
            if ideal is None:
                raise ValueError(
                    "'optimization_cost' can only be specified if 'ideal'"
                    "is also specified"
                )
            ACCEPTED_COST_FUNCTIONS = ["linear", "squared", "exponential"]
            if optimization_cost not in ACCEPTED_COST_FUNCTIONS:
                raise ValueError(
                    f"'optimization_cost': {optimization_cost} has to be a "
                    f"member of {ACCEPTED_COST_FUNCTIONS}"
                )

        if more_than and less_than and more_than > less_than:
            raise ValueError(
                f"'more_than': {more_than} cannot be greater than 'less_than': "
                f"{less_than}"
            )

        if ideal and more_than and ideal < more_than:
            raise ValueError(
                f"'ideal': {ideal} cannot be smaller than 'more_than': " f"{more_than}"
            )
        if ideal and less_than and ideal > less_than:
            raise ValueError(
                f"'ideal': {ideal} cannot be greater than 'less_than': " f"{less_than}"
            )

        for m in [from_dict, to_dict]:
            if "mark" in m:
                if isinstance(m["mark"], Container):
                    k = cont_string
                elif isinstance(m["mark"], int):
                    k = inst_string
                    if m["mark"] < 0:
                        raise ValueError(
                            f"The instruction 'mark' in {m} must be greater "
                            f"than and equal to 0"
                        )
                else:
                    raise TypeError(f"The 'mark' in {m} must be Container or Integer")
            else:
                raise KeyError(f"The {m} dict must contain `mark`")

            if "state" in m:
                if m["state"] in state_strings:
                    k += m["state"]
                else:
                    raise TypeError(
                        f"The 'state' in {m} must be in " f"{', '.join(state_strings)}"
                    )
            else:
                raise KeyError(f"The {m} dict must contain 'state'")

            keys.append(k)

        if from_dict["mark"] == to_dict["mark"]:
            if from_dict["state"] == to_dict["state"]:
                raise RuntimeError(
                    f"The from_dict: {from_dict} and to_dict: {to_dict} are "
                    f"the same"
                )
            if from_dict["state"] == "end":
                raise RuntimeError(
                    f"The from_dict: {from_dict} cannot come before the "
                    f"to_dict {to_dict}"
                )

        from_time_point = {keys[0]: from_dict["mark"]}
        to_time_point = {keys[1]: to_dict["mark"]}

        if less_than is not None:
            self.time_constraints += [
                {"from": from_time_point, "to": to_time_point, "less_than": less_than}
            ]
            if mirror:
                self.add_time_constraint(to_dict, from_dict, less_than, mirror=False)

        if more_than is not None:
            self.time_constraints += [
                {"from": from_time_point, "to": to_time_point, "more_than": more_than}
            ]

        if ideal is not None:
            ideal_dict = dict(value=ideal)
            if optimization_cost is not None:
                ideal_dict["optimization_cost"] = optimization_cost

            self.time_constraints += [
                {"from": from_time_point, "to": to_time_point, "ideal": ideal_dict}
            ]

    def get_instruction_index(self):
        """Get index of the last appended instruction

        Example Usage:

        .. code-block:: python

            p = Protocol()
            plate_1 = p.ref("plate_1", id=None, cont_type="96-flat",
                            discard=True)

            p.cover(plate_1)
            time_point_1 = p.get_instruction_index()  # time_point_1 = 0

        Raises
        ------
        ValueError
            If an instruction index is less than 0

        Returns
        -------
        int
            Index of the preceding instruction
        """
        instruction_index = len(self.instructions) - 1
        if instruction_index < 0:
            raise ValueError("Instruction index less than 0")
        return instruction_index

    def _append_and_return(self, instructions):
        """
        Append instruction(s) to the Protocol list and returns the
        Instruction(s).

        The other functions on Protocol() should be used
        in lieu of doing this directly.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            p._append_and_return(
                Incubate("sample_plate", "ambient", "1:hour")
            )

        Autoprotocol Output:

        .. code-block:: none

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
        instructions : Instruction or list(Instruction)
            Instruction object(s) to be appended.

        Returns
        -------
        Instruction or list(Instruction)
            Instruction object(s) to be appended and returned

        """
        if type(instructions) is list:
            self.instructions.extend(instructions)
        else:
            self.instructions.append(instructions)

        return instructions

    def batch_containers(self, containers, batch_in=True, batch_out=False):
        """
        Batch containers such that they all enter or exit together.

        Example Usage:

        .. code-block:: python

            plate_1 = protocol.ref("p1", None, "96-pcr", storage="cold_4")
            plate_2 = protocol.ref("p2", None, "96-pcr", storage="cold_4")

            protocol.batch_containers([plate_1, plate_2])

        Autoprotocol Output:

        .. code-block:: json

            {
              "refs": {
                "p1": {
                  "new": "96-pcr",
                  "store": {
                    "where": "cold_4"
                  }
                },
                "p2": {
                  "new": "96-pcr",
                  "store": {
                    "where": "cold_4"
                  }
                }
              },
              "time_constraints": [
                {
                  "from": {
                    "ref_start": "p1"
                  },
                  "less_than": "0:second",
                  "to": {
                    "ref_start": "p2"
                  }
                },
                {
                  "from": {
                    "ref_start": "p1"
                  },
                  "more_than": "0:second",
                  "to": {
                    "ref_start": "p2"
                  }
                }
              ]
            }

        Parameters
        ----------
        containers : list(Container)
            Containers to batch
        batch_in : bool, optional
            Batch the entry of containers, default True
        batch_out: bool, optional
            Batch the exit of containers, default False

        Raises
        ------
        TypeError
            If containers is not a list
        TypeError
            If containers is not a list of Container object

        """

        time = Unit(0, "second")

        if not isinstance(containers, list):
            raise TypeError("batch_containers containers must be a list")
        if not all(isinstance(cont, Container) for cont in containers):
            raise TypeError("batch_containers containers must be a list of containers.")
        if not batch_in and not batch_out or len(containers) < 2:
            warnings.warn("batch_containers is used but has no effect")

        reference_container = containers[0]
        remainder_containers = containers[1:]

        states = []
        if batch_in:
            states.append("start")
        if batch_out:
            states.append("end")

        for container in remainder_containers:
            for state in states:
                from_dict = {"mark": reference_container, "state": state}
                to_dict = {"mark": container, "state": state}
                self.add_time_constraint(
                    from_dict=from_dict, to_dict=to_dict, less_than=time, more_than=time
                )

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
            dict with keys "refs" and "instructions" and optionally
            "time_constraints" and "outs", each of which contain the
            "refified" contents of their corresponding Protocol attribute.

        Raises
        ------
        RuntimeError
            If either refs or instructions attribute is empty
        """
        outs = {}
        # pragma pylint: disable=protected-access
        for n, ref in self.refs.items():
            for well in ref.container._wells:
                if well.name or len(well.properties) > 0:
                    if n not in outs.keys():
                        outs[n] = {}
                    outs[n][str(well.index)] = {}
                    if well.name:
                        outs[n][str(well.index)]["name"] = well.name
                    if len(well.properties) > 0:
                        outs[n][str(well.index)]["properties"] = well.properties
            # assign any storage or discard condition changes to ref
            if "store" in ref.opts:
                ref.opts["store"] = {"where": ref.container.storage}
            if ref.container.storage is None and "discard" not in ref.opts:
                ref.opts["discard"] = True
                del ref.opts["store"]
            elif ref.container.storage is not None and "discard" in ref.opts:
                ref.opts["store"] = {"where": ref.container.storage}
                del ref.opts["discard"]
        # pragma pylint: enable=protected-access

        if outs:
            setattr(self, "outs", outs)

        prop_list = [
            a
            for a in dir(self)
            if not a.startswith("__") and not callable(getattr(self, a))
        ]

        explicit_props = ["outs", "refs", "instructions"]
        # attributes that are always serialized.
        optional_props = ["time_constraints"]
        # optional attributes that are serialized only when there are values
        for prop in optional_props:
            if getattr(self, prop):
                explicit_props.append(prop)

        return {
            attr: self._refify(getattr(self, attr))
            for attr in prop_list
            if attr in explicit_props
        }

    def store(self, container, condition):
        """
        Manually adjust the storage destiny for a container used within
        this protocol.

        Parameters
        ----------
        container : Container
            Container used within this protocol
        condition : str
            New storage destiny for the specified Container

        Raises
        ------
        TypeError
            If container argument is not a Container object
        RuntimeError
            If the container passed is not already present in self.refs

        """
        if not condition or condition == "discard":
            condition = None
        if not isinstance(container, Container):
            raise TypeError("Protocol.store() can only be used on a Container object.")
        container.storage = condition
        r = self.refs.get(container.name)
        if not r:
            raise RuntimeError(
                "That container does not exist in the refs for this protocol."
            )
        if "discard" in r.opts:
            r.opts.pop("discard")
        if condition:
            r.opts["store"] = {"where": str(condition)}
        else:
            r.opts.pop("store")
            r.opts["discard"] = True

    def acoustic_transfer(
        self, source, dest, volume, one_source=False, droplet_size="25:nanoliter"
    ):
        """
        Specify source and destination wells for transferring liquid via an
        acoustic liquid handler.  Droplet size is usually device-specific.

        Example Usage:

        .. code-block:: python

            p.acoustic_transfer(
                echo.wells(0,1).set_volume("12:nanoliter"),
                plate.wells_from(0,5), "4:nanoliter", one_source=True)


        Autoprotocol Output:

        .. code-block:: none

            "instructions": [
                {
                    "groups": [
                        {
                            "transfer": [
                                {
                                    "volume": "0.004:microliter",
                                    "to": "plate/0",
                                    "from": "echo_plate/0"
                                },
                                {
                                    "volume": "0.004:microliter",
                                    "to": "plate/1",
                                    "from": "echo_plate/0"
                                },
                                {
                                    "volume": "0.004:microliter",
                                    "to": "plate/2",
                                    "from": "echo_plate/0"
                                },
                                {
                                    "volume": "0.004:microliter",
                                    "to": "plate/3",
                                    "from": "echo_plate/1"
                                },
                                {
                                    "volume": "0.004:microliter",
                                    "to": "plate/4",
                                    "from": "echo_plate/1"
                                }
                            ]
                        }
                    ],
                    "droplet_size": "25:microliter",
                    "op": "acoustic_transfer"
                }
            ]


        Parameters
        ----------
        source : Well or WellGroup or list(Well)
            Well or wells to transfer liquid from.  If multiple source wells
            are supplied and one_source is set to True, liquid will be
            transferred from each source well specified as long as it contains
            sufficient volume. Otherwise, the number of source wells specified
            must match the number of destination wells specified and liquid
            will be transferred from each source well to its corresponding
            destination well.
        dest : Well or WellGroup or list(Well)
            Well or WellGroup to which to transfer liquid.  The number of
            destination wells must match the number of source wells specified
            unless one_source is set to True.
        volume : str or Unit or list
            The volume(s) of liquid to be transferred from source wells to
            destination wells.  Volume can be specified as a single string or
            Unit, or can be given as a list of volumes.  The length of a list
            of volumes must match the number of destination wells given unless
            the same volume is to be transferred to each destination well.
        one_source : bool, optional
            Specify whether liquid is to be transferred to destination wells
            from a group of wells all containing the same substance.
        droplet_size : str or Unit, optional
            Volume representing a droplet_size.  The volume of each `transfer`
            group should be a multiple of this volume.

        Returns
        -------
        AcousticTransfer
            Returns the :py:class:`autoprotocol.instruction.AcousticTransfer`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            Incorrect input types, e.g. source/dest are not Well or WellGroup
            or list of Well
        RuntimeError
            Incorrect length for source and destination
        RuntimeError
            Transfer volume not being a multiple of droplet size
        RuntimeError
            Insufficient volume in source wells

        """
        # Check valid well inputs
        if not is_valid_well(source):
            raise TypeError("Source must be of type Well, list of Wells, or WellGroup.")
        if not is_valid_well(dest):
            raise TypeError(
                "Destination (dest) must be of type Well, list of Wells, or "
                "WellGroup."
            )

        transfers = []
        source = WellGroup(source)
        dest = WellGroup(dest)
        len_source = len(source.wells)
        len_dest = len(dest.wells)
        droplet_size = Unit(droplet_size)
        max_decimal_places = 12  # for rounding after floating point arithmetic

        # Auto-generate well-group if only 1 well specified and using >1 source
        if not one_source:
            if len_dest > 1 and len_source == 1:
                source = WellGroup(source.wells * len_dest)
                len_source = len(source.wells)
            if len_dest == 1 and len_source > 1:
                dest = WellGroup(dest.wells * len_source)
                len_dest = len(dest.wells)
            if len_source != len_dest:
                raise RuntimeError(
                    "To transfer liquid from one well or multiple wells "
                    "containing the same source, set one_source to True. To "
                    "transfer liquid from multiple wells to a single "
                    "destination well, specify only one destination well. "
                    "Otherwise, you must specify the same number of source and "
                    "destination wells to do a one-to-one transfer."
                )

        # Auto-generate list from single volume, check if list length matches
        if isinstance(volume, str) or isinstance(volume, Unit):
            if len_dest == 1 and not one_source:
                volume = [Unit(volume).to("ul")] * len_source
            else:
                volume = [Unit(volume).to("ul")] * len_dest
        elif isinstance(volume, list) and len(volume) == len_dest:
            volume = list(map(lambda x: Unit(x).to("ul"), volume))
        else:
            raise RuntimeError(
                "Unless the same volume of liquid is being transferred to each "
                "destination well, each destination well must have a "
                "corresponding volume in the form of a list."
            )
        vol_errors = []
        for vol_d in volume:
            if not round(vol_d / droplet_size, max_decimal_places) % 1 == 0:
                vol_errors.append(vol_d)
        if len(vol_errors) > 0:
            raise RuntimeError(
                f"Transfer volume has to be a multiple of the droplet size ({droplet_size}).This is not true for the following volumes: {vol_errors}"
            )
        # Ensure enough volume in single well to transfer to all dest wells
        if one_source:
            try:
                source_vol = [s.volume for s in source.wells]
                if sum([a for a in volume]) > sum([a for a in source_vol]):
                    raise RuntimeError(
                        "There is not enough volume in the source well(s) "
                        "specified to complete the transfers."
                    )
                if len_source >= len_dest and all(
                    i > j for i, j in zip(source_vol, volume)
                ):
                    sources = source.wells[:len_dest]
                    destinations = dest.wells
                    volumes = volume
                else:
                    sources = []
                    source_counter = 0
                    destinations = []
                    volumes = []
                    s = source.wells[source_counter]
                    vol = s.volume

                    for idx, d in enumerate(dest.wells):
                        vol_d = volume[idx]
                        while vol_d > Unit("0:microliter"):
                            if vol > vol_d:
                                sources.append(s)
                                destinations.append(d)
                                volumes.append(vol_d)
                                vol -= vol_d
                                vol = round(vol, max_decimal_places)
                                vol_d -= vol_d
                                vol_d = round(vol_d, max_decimal_places)
                            else:
                                sources.append(s)
                                destinations.append(d)
                                vol = int(vol / droplet_size) * droplet_size
                                volumes.append(vol)
                                vol_d -= vol
                                vol_d = round(vol_d, max_decimal_places)
                                source_counter += 1
                                if source_counter < len_source:
                                    s = source.wells[source_counter]
                                    vol = s.volume
                source = WellGroup(sources)
                dest = WellGroup(destinations)
                volume = volumes
            except (ValueError, AttributeError, TypeError):
                raise RuntimeError(
                    "When transferring liquid from multiple wells containing "
                    "the same substance to multiple other wells, each source "
                    "Well must have a volume attribute (aliquot) associated "
                    "with it."
                )

        for s, d, v in list(zip(source.wells, dest.wells, volume)):
            self._remove_cover(s.container, "acoustic_transfer")
            self._remove_cover(d.container, "acoustic_transfer")
            xfer = {"from": s, "to": d, "volume": v}
            # Volume accounting
            if d.volume:
                d.volume += v
            else:
                d.volume = v
            if s.volume:
                s.volume -= v
            if v > Unit(0, "microliter"):
                transfers.append(xfer)

        for x in transfers:
            x["volume"] = round(x["volume"].to("nl"), max_decimal_places)

        return self._append_and_return(
            AcousticTransfer([{"transfer": transfers}], droplet_size)
        )

    def illuminaseq(
        self,
        flowcell,
        lanes,
        sequencer,
        mode,
        index,
        library_size,
        dataref,
        cycles=None,
    ):
        """
        Load aliquots into specified lanes for Illumina sequencing.
        The specified aliquots should already contain the appropriate mix for
        sequencing and require a library concentration reported in
        ng/uL.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_wells = p.ref(
                "test_plate", None, "96-pcr", discard=True).wells_from(0, 8)

            p.illuminaseq(
                "PE",
                [
                    {"object": sample_wells[0], "library_concentration": 1.0},
                    {"object": sample_wells[1], "library_concentration": 5.32},
                    {"object": sample_wells[2], "library_concentration": 54},
                    {"object": sample_wells[3], "library_concentration": 20},
                    {"object": sample_wells[4], "library_concentration": 23},
                    {"object": sample_wells[5], "library_concentration": 23},
                    {"object": sample_wells[6], "library_concentration": 21},
                    {"object": sample_wells[7], "library_concentration": 62}
                ],
                "hiseq", "rapid", 'none', 250, "my_illumina")

        Autoprotocol Output:

        .. code-block:: none

            "instructions": [
                {
                    "dataref": "my_illumina",
                    "index": "none",
                    "lanes": [
                        {
                            "object": "test_plate/0",
                            "library_concentration": 1
                        },
                        {
                            "object": "test_plate/1",
                            "library_concentration": 5.32
                        },
                        {
                            "object": "test_plate/2",
                            "library_concentration": 54
                        },
                        {
                            "object": "test_plate/3",
                            "library_concentration": 20
                        },
                        {
                            "object": "test_plate/4",
                            "library_concentration": 23
                        },
                        {
                            "object": "test_plate/5",
                            "library_concentration": 23
                        },
                        {
                            "object": "test_plate/6",
                            "library_concentration": 21
                        },
                        {
                            "object": "test_plate/7",
                            "library_concentration": 62
                        }
                    ],
                    "flowcell": "PE",
                    "mode": "mid",
                    "sequencer": "hiseq",
                    "library_size": 250,
                    "op": "illumina_sequence"
                }
            ]


        Parameters
        ----------
        flowcell : str
            Flowcell designation: "SR" or " "PE"
        lanes : list(dict)

            .. code-block:: none

                "lanes": [
                {
                    "object": aliquot, Well,
                    "library_concentration": decimal, // ng/uL
                },
                {...}]

        sequencer : str
            Sequencer designation: "miseq", "hiseq" or "nextseq"
        mode : str
            Mode designation: "rapid", "mid" or "high"
        index : str
            Index designation: "single", "dual" or "none"
        library_size: int
            Library size expressed as an integer of basepairs
        dataref : str
            Name of sequencing dataset that will be returned.
        cycles : Enum({"read_1", "read_2", "index_1", "index_2"})
            Parameter specific to Illuminaseq read-length or number of
            sequenced bases. Refer to the ASC for more details

        Returns
        -------
        IlluminaSeq
            Returns the :py:class:`autoprotocol.instruction.IlluminaSeq`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            If index and dataref are not of type str.
        TypeError
            If library_concentration is not a number.
        TypeError
            If library_size is not an integer.
        ValueError
            If flowcell, sequencer, mode, index are not of type a valid option.
        ValueError
            If number of lanes specified is more than the maximum lanes of the
            specified type of sequencer.
        KeyError
            Invalid keys specified for cycles parameter
        """

        valid_flowcells = ["PE", "SR"]
        # currently available sequencers, modes and max number of lanes and
        # cycles
        valid_sequencers = {
            "miseq": {"max_lanes": 1, "modes": ["high"], "max_cycles_read": 600},
            "hiseq": {
                "max_lanes": 8,
                "modes": ["high", "rapid"],
                "max_cycles_read": 500,
            },
            "nextseq": {
                "max_lanes": 4,
                "modes": ["high", "mid"],
                "max_cycles_read": 300,
            },
        }

        valid_indices = ["single", "dual", "none"]
        valid_cycles = ["index_1", "index_2", "read_1", "read_2"]
        max_cycles_ind = 12

        if flowcell not in valid_flowcells:
            raise ValueError(
                f"Illumina sequencing flowcell type must be one "
                f"of: {', '.join(valid_flowcells)}."
            )
        if sequencer not in valid_sequencers.keys():
            raise ValueError(
                f"Illumina sequencer must be one of: "
                f"{', '.join(valid_sequencers.keys())}."
            )
        if not isinstance(lanes, list):
            raise TypeError("Illumina sequencing lanes must be a list(dict)")

        for l in lanes:
            if not isinstance(l, dict):
                raise TypeError("Illumina sequencing lanes must be a list(dict)")
            if not all(k in l.keys() for k in ["object", "library_concentration"]):
                raise TypeError(
                    "Each Illumina sequencing lane must contain an "
                    "'object' and a 'library_concentration'"
                )
            if not isinstance(l["object"], Well):
                raise TypeError(
                    "Each Illumina sequencing object must be of " "type Well"
                )
            if not isinstance(l["library_concentration"], (float, int)):
                raise TypeError(
                    "Each Illumina sequencing "
                    "library_concentration must be a number."
                )
        if len(lanes) > valid_sequencers[sequencer]["max_lanes"]:
            raise ValueError(
                f"The type of sequencer selected ({sequencer}) only has {valid_sequencers[sequencer]['max_lanes']} lane(s).  You specified {len(lanes)}. Please submit additional Illumina Sequencing instructions."
            )
        if mode not in valid_sequencers[sequencer]["modes"]:
            raise ValueError(
                f"The type of sequencer selected ({sequencer}) has valid modes: {', '.join(valid_sequencers[sequencer]['modes'])}.You specified: {mode}."
            )
        if index not in valid_indices:
            raise ValueError(
                f"Illumina sequencing index must be one of: "
                f"{', '.join(valid_indices)}."
            )
        if not isinstance(dataref, str):
            raise TypeError(f"dataref: {dataref}, must be a string")
        if not isinstance(library_size, int):
            raise TypeError(f"library_size: {library_size}, must be an integer.")

        if cycles:
            if not isinstance(cycles, dict):
                raise TypeError("Cycles must be a dict.")
            if not all(c in valid_cycles for c in cycles.keys()):
                raise KeyError(
                    f"Valid cycle parameters are: " f"{', '.join(valid_cycles)}"
                )
            if "read_1" not in cycles.keys():
                raise ValueError("If specifying cycles, 'read_1' must be designated.")
            if flowcell == "SR" and "read_2" in cycles.keys():
                raise ValueError("SR does not have a second read: 'read_2'.")
            if not all(isinstance(i, int) for i in cycles.values()):
                raise ValueError("Cycles must be specified as an integer.")
            for read in ["read_1", "read_2"]:
                if cycles.get(read):
                    if cycles[read] > valid_sequencers[sequencer]["max_cycles_read"]:
                        raise ValueError(
                            f"The maximum number of cycles for {read} is {valid_sequencers[sequencer]['max_cycles_read']}."
                        )
            for ind in ["index_1", "index_2"]:
                if cycles.get(ind):
                    if cycles[ind] > max_cycles_ind:
                        raise ValueError(
                            f"The maximum number of cycles for {ind} is "
                            f"{max_cycles_ind}."
                        )
                # set index 1 and 2 to default 0 if not otherwise specified
                else:
                    cycles[ind] = 0

        return self._append_and_return(
            IlluminaSeq(
                flowcell, lanes, sequencer, mode, index, library_size, dataref, cycles
            )
        )

    # pylint: disable=redefined-builtin
    def sangerseq(self, cont, wells, dataref, type="standard", primer=None):
        """
        Send the indicated wells of the container specified for Sanger
        sequencing.
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

          .. code-block:: none

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
                    "op": "sanger_sequence"
                }
            ]


        Parameters
        ----------
        cont : Container or str
            Container with well(s) that contain material to be sequenced.
        wells : list(Well) or WellGroup or Well
            WellGroup of wells to be measured or a list of well references in
            the form of ["A1", "B1", "C5", ...]
        dataref : str
            Name of sequencing dataset that will be returned.
        type: Enum({"standard", "rca"})
            Sanger sequencing type
        primer : Container, optional
            Tube containing sufficient primer for all RCA reactions.  This field
            will be ignored if you specify the sequencing type as "standard".
            Tube containing sufficient primer for all RCA reactions

        Returns
        -------
        SangerSeq
            Returns the :py:class:`autoprotocol.instruction.SangerSeq`
            instruction created from the specified parameters

        Raises
        ------
        RuntimeError
            No primer location specified for rca sequencing type
        ValueError
            Wells belong to more than one container
        TypeError
            Invalid input type for wells

        """
        seq_type = type.lower()
        if seq_type == "rca" and not primer:
            raise RuntimeError(
                "You must specify the location of primer for "
                "RCA sequencing reactions."
            )

        if isinstance(wells, Well):
            wells = WellGroup(wells)

        if isinstance(wells, WellGroup):
            container = set([w.container for w in wells])
            if len(container) > 1:
                raise ValueError("All wells need to be on one container for SangerSeq")
            wells = [str(w.index) for w in wells]

        if not isinstance(wells, list):
            raise TypeError(
                "Unknown input. SangerSeq wells accepts either a"
                "Well, a WellGroup, or a list of well indices"
            )

        return self._append_and_return(SangerSeq(cont, wells, dataref, type, primer))

    def dispense(
        self,
        ref,
        reagent,
        columns,
        is_resource_id=False,
        step_size="5:uL",
        flowrate=None,
        nozzle_position=None,
        pre_dispense=None,
        shape=None,
        shake_after=None,
    ):
        """
        Dispense specified reagent to specified columns.

        Example Usage:

        .. code-block:: python

            from autoprotocol.liquid_handle.liquid_handle_builders import *
            from autoprotocol.instructions import Dispense
            from autoprotocol import Protocol

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")

            p.dispense(sample_plate,
                       "water",
                       Dispense.builders.columns(
                           [Dispense.builders.column(0, "10:uL"),
                            Dispense.builders.column(1, "20:uL"),
                            Dispense.builders.column(2, "30:uL"),
                            Dispense.builders.column(3, "40:uL"),
                            Dispense.builders.column(4, "50:uL")
                           ])
                       )

            p.dispense(
                sample_plate,
                "water",
                Dispense.builders.columns(
                    [Dispense.builders.column(0, "10:uL")]
                ),
                Dispense.builders.nozzle_position(
                    position_x=Unit("1:mm"),
                    position_y=Unit("2:mm"),
                    position_z=Unit("20:mm")
                ),
                shape_builder(
                    rows=8, columns=1, format="SBS96"
                )
            )

        Autoprotocol Output:

        .. code-block:: none

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
                        }
                    ],
                    "op": "dispense"
                },
                {
                    "reagent": "water",
                    "object": "sample_plate",
                    "columns": [
                        {
                            "column": 0,
                            "volume": "10:microliter"
                        }
                    ],
                    "nozzle_position" : {
                        "position_x" : "1:millimeter",
                        "position_y" : "2:millimeter",
                        "position_z" : "20:millimeter"
                    },
                    "shape" : {
                        "rows" : 8,
                        "columns" : 1,
                        "format" : "SBS96"
                    }
                    "op": "dispense"
                },
            ]

        Parameters
        ----------
        ref : Container
            Container for reagent to be dispensed to.
        reagent : str or well
            Reagent to be dispensed. Use a string to specify the name or
            resource_id (see below) of the reagent to be dispensed.
            Alternatively, use a well to specify that the dispense operation
            must be executed using a specific aliquot as the dispense source.
        columns : list(dict("column": int, "volume": str/Unit))
            Columns to be dispensed to, in the form of a list(dict)
            specifying the column number and the volume to be dispensed to that
            column. Columns are expressed as integers indexed from 0.
            [{"column": <column num>, "volume": <volume>}, ...]
        is_resource_id : bool, optional
            If true, interprets reagent as a resource ID
        step_size : str or Unit, optional
            Specifies that the dispense operation must be executed
            using a peristaltic pump with the given step size. Note
            that the volume dispensed in each column must be an integer
            multiple of the step_size. Currently, step_size must be either
            5 uL or 0.5 uL. If set to None, will use vendor specified defaults.
        flowrate : str or Unit, optional
            The rate at which liquid is dispensed into the ref in units
            of volume/time.
        nozzle_position : dict, optional
            A dict represent nozzle offsets from the bottom middle of the
            plate's wells. see Dispense.builders.nozzle_position; specified as
            {"position_x": Unit, "position_y": Unit, "position_z": Unit}.
        pre_dispense : str or Unit, optional
            The volume of reagent to be dispensed per-nozzle into waste
            immediately prior to dispensing into the ref.
        shape: dict, optional
            The shape of the dispensing head to be used for the dispense.
            See liquid_handle_builders.shape_builder; specified as
            {"rows": int, "columns": int, "format": str} with format being a
            valid SBS format.
        shake_after: dict, optional
            Parameters that specify how a plate should be shaken at the very
            end of the instruction execution. See Dispense.builders.shake_after.

        Returns
        -------
        Dispense
            Returns the :py:class:`autoprotocol.instruction.Dispense`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            Invalid input types, e.g. ref is not of type Container
        ValueError
            Columns specified is invalid for this container type
        ValueError
            Invalid step-size given
        ValueError
            Invalid pre-dispense volume

        """
        _VALID_STEP_SIZES = [Unit(5, "uL"), Unit(0.5, "uL")]
        _DEFAULT_NOZZLE_COUNT = 8

        if not isinstance(ref, Container):
            raise TypeError(f"ref must be a Container but it was {type(ref)}.")

        columns = Dispense.builders.columns(columns)

        ref_cols = list(range(ref.container_type.col_count))
        if not all(_["column"] in ref_cols for _ in columns):
            raise ValueError(
                f"Specified dispense columns: {columns} contains a column index that is outside of the valid columns: {ref_cols} for ref: {ref}."
            )

        # pre-evaluate all parameters before making any changes to the Protocol
        if flowrate is not None:
            flowrate = parse_unit(flowrate, "uL/s")
        if nozzle_position is not None:
            nozzle_position = Dispense.builders.nozzle_position(**nozzle_position)
        if pre_dispense is not None:
            pre_dispense = parse_unit(pre_dispense, "uL")
        if shape is not None:
            shape = Dispense.builders.shape(**shape)
        if shake_after is not None:
            shake_after = Dispense.builders.shake_after(**shake_after)

        nozzle_count = (
            shape["rows"] * shape["columns"] if shape else _DEFAULT_NOZZLE_COUNT
        )

        if step_size is not None:
            step_size = parse_unit(step_size, "uL")
            if step_size not in _VALID_STEP_SIZES:
                raise ValueError(
                    f"specified step_size was {step_size} but it must be in "
                    f"{_VALID_STEP_SIZES}"
                )

            for c in columns:
                if c["volume"] % step_size != Unit("0:uL"):
                    raise ValueError(
                        f"Dispense volume must be a multiple of the step size {step_size}, but column {c} does not meet these requirements."
                    )

            if pre_dispense is not None:
                invalid_pre_dispense_range = pre_dispense < 2 * step_size
                if invalid_pre_dispense_range and pre_dispense != Unit(0, "uL"):
                    raise ValueError(
                        f"Dispense pre_dispense must either be 0:uL or at least 2 * step_size: {step_size} but it was {pre_dispense}."
                    )
                if pre_dispense % step_size != Unit(0, "uL"):
                    raise ValueError(
                        f"Dispense pre_dispense must be a multiple of step_size: {step_size} but it was {pre_dispense}."
                    )

        row_count = ref.container_type.row_count()
        if isinstance(reagent, Well):
            self._remove_cover(reagent.container, "dispense from")

            # Volume accounting
            total_vol_dispensed = sum([Unit(c["volume"]) for c in columns]) * row_count
            if pre_dispense is not None:
                total_vol_dispensed += nozzle_count * pre_dispense
            if reagent.volume:
                reagent.volume -= total_vol_dispensed
            else:
                reagent.volume = -total_vol_dispensed

            reagent, resource_id, reagent_source = None, None, reagent
        else:
            if not isinstance(reagent, str):
                raise TypeError(
                    f"reagent: {reagent} must be a Well or string but it was: "
                    f"{type(reagent)}."
                )
            if is_resource_id:
                reagent, resource_id, reagent_source = None, reagent, None
            else:
                # reagent remains unchanged
                resource_id, reagent_source = None, None

        self._remove_cover(ref, "dispense to")

        for c in columns:
            wells = ref.wells_from(c["column"], row_count, columnwise=True)
            for w in wells:
                if w.volume:
                    w.volume += c["volume"]
                else:
                    w.volume = c["volume"]

        return self._append_and_return(
            Dispense(
                object=ref,
                columns=columns,
                reagent=reagent,
                resource_id=resource_id,
                reagent_source=reagent_source,
                step_size=step_size,
                flowrate=flowrate,
                nozzle_position=nozzle_position,
                pre_dispense=pre_dispense,
                shape=shape,
                shake_after=shake_after,
            )
        )

    def dispense_full_plate(
        self,
        ref,
        reagent,
        volume,
        is_resource_id=False,
        step_size="5:uL",
        flowrate=None,
        nozzle_position=None,
        pre_dispense=None,
        shape=None,
        shake_after=None,
    ):
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

        .. code-block:: none

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
        reagent : str or Well
            Reagent to be dispensed. Use a string to specify the name or
            resource_id (see below) of the reagent to be dispensed.
            Alternatively, use a well to specify that the dispense operation
            must be executed using a specific aliquot as the dispense source.
        volume : Unit or str
            Volume of reagent to be dispensed to each well
        is_resource_id : bool, optional
            If true, interprets reagent as a resource ID
        step_size : str or Unit, optional
            Specifies that the dispense operation must be executed
            using a peristaltic pump with the given step size. Note
            that the volume dispensed in each column must be an integer
            multiple of the step_size. Currently, step_size must be either
            5 uL or 0.5 uL. If set to None, will use vendor specified defaults.
        flowrate : str or Unit, optional
            The rate at which liquid is dispensed into the ref in units
            of volume/time.
        nozzle_position : dict, optional
            A dict represent nozzle offsets from the bottom middle of the
            plate's wells. see Dispense.builders.nozzle_position; specified as
            {"position_x": Unit, "position_y": Unit, "position_z": Unit}.
        pre_dispense : str or Unit, optional
            The volume of reagent to be dispensed per-nozzle into waste
            immediately prior to dispensing into the ref.
        shape: dict, optional
            The shape of the dispensing head to be used for the dispense.
            See liquid_handle_builders.shape_builder; specified as
            {"rows": int, "columns": int, "format": str} with format being a
            valid SBS format.
        shake_after: dict, optional
            Parameters that specify how a plate should be shaken at the very
            end of the instruction execution. See Dispense.builders.shake_after.

        Returns
        -------
        Dispense
            Returns the :py:class:`autoprotocol.instruction.Dispense`
            instruction created from the specified parameters

        """
        columns = Dispense.builders.columns(
            [
                {"column": col, "volume": volume}
                for col in range(ref.container_type.col_count)
            ]
        )

        return self.dispense(
            ref,
            reagent,
            columns,
            is_resource_id,
            step_size,
            flowrate,
            nozzle_position,
            pre_dispense,
            shape,
            shake_after,
        )

    def spin(
        self, ref, acceleration, duration, flow_direction=None, spin_direction=None
    ):
        """
        Apply acceleration to a container.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-flat",
                                 storage="warm_37")

            p.spin(sample_plate, "1000:g", "20:minute", flow_direction="outward")

        Autoprotocol Output:

        .. code-block:: none

            "instructions": [
                {
                    "acceleration": "1000:g",
                    "duration": "20:minute",
                    "flow_direction": "outward",
                    "spin_direction": [
                        "cw",
                        "ccw"
                    ]
                    "object": "sample_plate",
                    "op": "spin"
                }
            ]

        Parameters
        ----------
        ref : Container
            The container to be centrifuged.
        acceleration: str
            Acceleration to be applied to the plate, in units of `g` or
            `meter/second^2`.
        duration: str or Unit
            Length of time that acceleration should be applied.
        flow_direction: str
            Specifies the direction contents will tend toward with respect to
            the container. Valid directions are "inward" and "outward", default
            value is "inward".
        spin_direction: list(str)
            A list of "cw" (clockwise), "cww" (counterclockwise). For each
            element in the list, the container will be spun in the stated
            direction for the set "acceleration" and "duration". Default values
            are derived from the "flow_direction" parameter. If
            "flow_direction" is "outward", then "spin_direction" defaults to
            ["cw", "ccw"]. If "flow_direction" is "inward", then
            "spin_direction" defaults to ["cw"].

        Returns
        -------
        Spin
            Returns the :py:class:`autoprotocol.instruction.Spin`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            If ref to spin is not of type Container.
        TypeError
            If spin_direction or flow_direction are not properly formatted.
        ValueError
            If spin_direction or flow_direction do not have appropriate values.

        """
        if flow_direction is not None and flow_direction not in ["inward", "outward"]:
            raise ValueError(
                "The specified value for flow_direction was not valid. If "
                "specifying, please choose either 'inward' or 'outward'"
            )

        default_directions = {"inward": ["cw"], "outward": ["cw", "ccw"]}
        if spin_direction is None and flow_direction:
            spin_direction = default_directions[flow_direction]

        if spin_direction is not None:
            if not isinstance(spin_direction, list):
                raise TypeError("Spin directions must be in the form of a list.")
            if len(spin_direction) is 0:
                raise ValueError(
                    "Spin direction must be a list containing at least one "
                    "spin direction ('cw', 'ccw')"
                )

        if spin_direction and not all(s in ["cw", "ccw"] for s in spin_direction):
            raise ValueError("Spin directions must be 'cw' or 'ccw'.")

        try:
            duration = Unit(duration)
        except ValueError as e:
            raise ValueError(f"Duration must be a unit. {e}")

        if not isinstance(ref, Container):
            raise TypeError("Ref must be of type Container.")

        if not flow_direction or flow_direction == "inward":
            self._add_cover(ref, "inward spin")
        elif flow_direction == "outward":
            self._remove_cover(ref, "outward spin")

        return self._append_and_return(
            Spin(ref, acceleration, duration, flow_direction, spin_direction)
        )

    def agitate(self, ref, mode, speed, duration, temperature=None, mode_params=None):
        """
        Agitate a container in a specific condition for a given duration. If
        temperature is not specified, container is agitated at ambient
        temperature by default.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            plate = p.ref("test pcr plate", id=None, cont_type="96-pcr",
                          storage="cold_4")
            p.agitate(
                ref = plate,
                mode="vortex",
                speed="1000:rpm",
                duration="5:minute",
                temperature="25:celsius"
            )

        Autoprotocol Output:

        .. code-block:: none

            "instructions" : [
                {
                    "object": "test pcr plate",
                    "mode": "vortex",
                    "speed": "1000:rpm",
                    "duration": "5:minute",
                    "temperature": "25:celsius",
                    "op": "agitate"
                }
            ]


        Parameters
        ----------
        ref : Container
            Container to be agitated
        mode : str
            Mode by which to agitate container
        speed : str or Unit
            Speed at which to agitate container
        duration : str or Unit
            Specify the duration to agitate for
        temperature : Unit or str, optional
            Specify target temperature to agitate container at.
            Defaults to ambient
        mode_params : dict, optional
            Dictionary containing mode params for agitation modes

        Returns
        -------
            Agitate
                returns a :py:class:`autoprotocol.instruction.Agitate`
                instruction created from the specified parameters

        Raises
        ------
        ValueError
            If ref provided is not of type Container
        ValueError
            If speed is less than 0 rpm
        ValueError
            if duration is less than 0 minutes
        ValueError
            If `mode_params` not specified for mode `stir_bar`
        ValueError
            If valid keys for `mode_params` used for `stir_bar` are not included
        ValueError
            If wells specified in `mode_params` are not in the same container
        ValueError
            If `bar_shape` is not valid
        ValueError
            If `bar_length` is less than 0 millimeter
        ValueError
            If `mode` used does not require `mode_params`
        TypeError
            If ref cannot be undergo agitate mode `roll` or `invert`

        """
        valid_modes = ["vortex", "invert", "roll", "stir_bar"]
        valid_bar_shapes = ["bar", "cross"]
        valid_bar_mode_params = ["wells", "bar_shape", "bar_length"]

        speed = parse_unit(speed)
        temperature = parse_unit(temperature, "celsius") if temperature else None
        duration = parse_unit(duration, "minute")

        if not isinstance(ref, Container):
            raise ValueError("Ref is not of type Container.")
        if speed <= Unit("0:rpm"):
            raise ValueError(f"Speed: {speed} must be more than 0 rpm.")

        if duration <= Unit("0:minute"):
            raise ValueError(f"Duration: {duration} must be longer than 0 minutes.")
        if mode not in valid_modes:
            raise ValueError(f"Agitate mode must be one of {valid_modes}")
        if mode == "stir_bar":
            if mode_params is None:
                raise ValueError(
                    "Dictionary `mode_params` must be specified for the "
                    "mode `stir_bar`"
                )
            elif not set(mode_params.keys()) == set(valid_bar_mode_params):
                raise ValueError(
                    f"Params for `stir_bar` must include " f"{valid_bar_mode_params}"
                )

            wells = WellGroup(mode_params["wells"])
            container = set([w.container for w in wells])
            shape = mode_params["bar_shape"]
            length = parse_unit(mode_params["bar_length"], "millimeter")

            if len(container) > 1:
                raise ValueError(
                    "All wells need to be on the same container for Agitate"
                )
            if shape not in valid_bar_shapes:
                raise ValueError(f"Param `bar_shape` must be one of {valid_bar_shapes}")
            if length <= Unit(0, "millimeter"):
                raise ValueError(
                    "Params `bar_length` must be greater than 0 millimeter"
                )
        elif mode != "stir_bar" and mode_params:
            raise ValueError(f"Mode {mode} does not need mode_params specified")
        elif mode in ["invert", "roll"] and not ref.container_type.is_tube:
            raise TypeError(f"Specified container {ref} cannot be inverted or rolled.")

        return self._append_and_return(
            Agitate(ref, mode, speed, duration, temperature, mode_params)
        )

    def thermocycle(
        self,
        ref,
        groups,
        volume="10:microliter",
        dataref=None,
        dyes=None,
        melting_start=None,
        melting_end=None,
        melting_increment=None,
        melting_rate=None,
        lid_temperature=None,
    ):
        """
        Append a Thermocycle instruction to the list of instructions, with
        groups is a list(dict) in the form of:

        .. code-block:: python

            "groups": [{
                "cycles": integer,
                "steps": [
                    {
                        "duration": duration,
                        "temperature": temperature,
                        "read": boolean // optional (default false)
                    },
                    {
                        "duration": duration,
                        "gradient": {
                            "top": temperature,
                            "bottom": temperature
                        },
                        "read": boolean // optional (default false)
                    }
                ]
            }],

        Thermocycle can also be used for either conventional or row-wise
        gradient PCR as well as qPCR. Refer to the examples below for details.

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
            * 1 cycle:
                * 4 degrees for 30 seconds
            * all cycles: Lid temperature at 97 degrees


        .. code-block:: python

            from instruction import Thermocycle

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-pcr",
                                 storage="warm_37")

            # a plate must be sealed before it can be thermocycled
            p.seal(sample_plate)

            p.thermocycle(
                sample_plate,
                [
                    Thermocycle.builders.group(
                        steps=[
                            Thermocycle.builders.step("95:celsius", "5:minute")
                        ]
                    ),
                    Thermocycle.builders.group(
                        steps=[
                            Thermocycle.builders.step("95:celsius", "30:s"),
                            Thermocycle.builders.step("56:celsius", "20:s"),
                            Thermocycle.builders.step("72:celsius", "20:s"),
                        ],
                        cycles=30
                    ),
                    Thermocycle.builders.group(
                        steps=[
                            Thermocycle.builders.step("72:celsius", "10:minute")
                        ]
                    ),
                    Thermocycle.builders.group(
                        steps=[
                            Thermocycle.builders.step("4:celsius", "30:s")
                        ]
                    )
                ],
                lid_temperature="97:celsius"
            )


        Autoprotocol Output:

        .. code-block:: none

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
                            "cycles": 30,
                            "steps": [
                                {
                                    "duration": "30:second",
                                    "temperature": "95:celsius"
                                },
                                {
                                    "duration": "20:second",
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
                        },
                        {
                            "cycles": 1,
                            "steps": [
                                {
                                    "duration": "30:second",
                                    "temperature": "4:celsius"
                                }
                            ]
                        }
                    ],
                    "op": "thermocycle"
                }
            ]


        To gradient thermocycle a container according to the protocol:

            * 1 cycle:
                * 95 degrees for 5 minutes
            * 30 cycles:
                * 95 degrees for 30 seconds

                Top Row:
                * 65 degrees for 20 seconds
                Bottom Row:
                * 55 degrees for 20 seconds

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

            p.thermocycle(
                sample_plate,
                [
                    Thermocycle.builders.group(
                        steps=[
                            Thermocycle.builders.step("95:celsius", "5:minute")
                        ]
                    ),
                    Thermocycle.builders.group(
                        steps=[
                            Thermocycle.builders.step("95:celsius", "30:s"),
                            Thermocycle.builders.step(
                                {"top": "65:celsius", "bottom": "55:celsius"},
                                "20:s"
                            ),
                            Thermocycle.builders.step("72:celsius", "20:s"),
                        ],
                        cycles=30
                    ),
                    Thermocycle.builders.group(
                        steps=[
                            Thermocycle.builders.step("72:celsius", "10:minute")
                        ]
                    )
                ]
            )

        To conduct a qPCR, at least one dye type and the dataref field has to
        be specified.
        The example below uses SYBR dye and the following temperature profile:

            * 1 cycle:
                * 95 degrees for 3 minutes
            * 40 cycles:
                * 95 degrees for 10 seconds
                * 60 degrees for 30 seconds (Read during extension)

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-pcr",
                                 storage="warm_37")

            # a plate must be sealed before it can be thermocycled
            p.seal(sample_plate)

            p.thermocycle(
                sample_plate,
                [
                    Thermocycle.builders.group(
                        steps=[
                            Thermocycle.builders.step("95:celsius", "3:minute")
                        ]
                    ),
                    Thermocycle.builders.group(
                        steps=[
                            Thermocycle.builders.step(
                                "95:celsius",
                                "10:second",
                                read=False
                            ),
                            Thermocycle.builders.step(
                                "95:celsius",
                                "10:second",
                                read=True
                            )
                        ],
                        cycles=40
                    )
                ],
                dataref = "my_qpcr_data",
                dyes = {"SYBR": sample_plate.all_wells().indices()}
            )

        Parameters
        ----------
        ref : Container
            Container to be thermocycled.
        groups : list(dict)
            List of thermocycling instructions formatted as above
        volume : str or Unit, optional
            Volume contained in wells being thermocycled
        dataref : str, optional
            Name of dataref representing read data if performing qPCR
        dyes : dict, optional
            Dictionary mapping dye types to the wells they're used in
        melting_start: str or Unit, optional
            Temperature at which to start the melting curve.
        melting_end: str or Unit, optional
            Temperature at which to end the melting curve.
        melting_increment: str or Unit, optional
            Temperature by which to increment the melting curve. Accepted
            increment values are between 0.1 and 9.9 degrees celsius.
        melting_rate: str or Unit, optional
            Specifies the duration of each temperature step in the melting
            curve.
        lid_temperature: str or Unit, optional
            Specifies the lid temperature throughout the duration of the
            thermocycling instruction

        Returns
        -------
        Thermocycle
            Returns the :py:class:`autoprotocol.instruction.Thermocycle`
            instruction created from the specified parameters

        Raises
        ------
        AttributeError
            If groups are not properly formatted
        TypeError
            If ref to thermocycle is not of type Container.
        ValueError
            Container specified cannot be thermocycled
        ValueError
            Lid temperature is not within bounds

        """
        if not isinstance(ref, Container):
            raise TypeError("Ref must be of type Container.")
        if "thermocycle" not in ref.container_type.capabilities:
            raise ValueError(
                f"Container '{ref.name}' type '{ref.container_type.shortname}', cannot be thermocycled."
            )

        groups = [Thermocycle.builders.group(**_) for _ in groups]

        dyes = Thermocycle.builders.dyes(**(dyes or {}))
        melting = Thermocycle.builders.melting(
            melting_start, melting_end, melting_increment, melting_rate
        )

        # Constants are currently based off the Biorad thermocyclers, and
        # assumes that they are generally reflective of other thermocyclers
        _MIN_LID_TEMP = Unit("30:celsius")
        _MAX_LID_TEMP = Unit("110:celsius")
        if lid_temperature is not None:
            lid_temperature = parse_unit(lid_temperature)
            if not (_MIN_LID_TEMP <= lid_temperature <= _MAX_LID_TEMP):
                raise ValueError(
                    f"Lid temperature {lid_temperature} has to be within "
                    f"[{_MIN_LID_TEMP}, {_MAX_LID_TEMP}]"
                )

        self._add_seal(ref, "thermocycle")
        return self._append_and_return(
            Thermocycle(
                object=ref,
                groups=groups,
                volume=volume,
                dataref=dataref,
                dyes=dyes,
                melting=melting,
                lid_temperature=lid_temperature,
            )
        )

    def incubate(
        self,
        ref,
        where,
        duration,
        shaking=False,
        co2=0,
        uncovered=False,
        target_temperature=None,
        shaking_params=None,
    ):
        """
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

        .. code-block:: none

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


        Parameters
        ----------
        ref : Ref or str
            The container to be incubated
        where : Enum({"ambient", "warm_37", "cold_4", "cold_20", "cold_80"})
            Temperature at which to incubate specified container
        duration : Unit or str
            Length of time to incubate container
        shaking : bool, optional
            Specify whether or not to shake container if available at the
            specified temperature
        co2 : Number, optional
            Carbon dioxide percentage
        uncovered: bool, optional
            Specify whether the container should be uncovered during incubation
        target_temperature : Unit or str, optional
            Specify a target temperature for a device (eg. an incubating block)
            to reach during the specified duration.
        shaking_params: dict, optional
            Specify "path" and "frequency" of shaking parameters to be used
            with compatible devices (eg. thermoshakes)

        Returns
        -------
        Incubate
            Returns the :py:class:`autoprotocol.instruction.Incubate`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            Invalid input types given, e.g. ref is not of type Container
        RuntimeError
            Incubating uncovered in a location which is shaking

        """
        if not isinstance(ref, Container):
            raise TypeError("Ref needs to be of type Container")
        allowed_uncovered = ["ambient"]
        if uncovered and (where not in allowed_uncovered or shaking):
            raise RuntimeError(
                f"If incubating uncovered, location must be in "
                f"{', '.join(allowed_uncovered)} and not shaking."
            )

        if not isinstance(co2, Number):
            raise TypeError("co2 must be a number.")

        if target_temperature:
            target_temperature = parse_unit(target_temperature, "celsius")

        if not uncovered:
            self._add_cover(ref, "incubate")
        return self._append_and_return(
            Incubate(
                ref, where, duration, shaking, co2, target_temperature, shaking_params
            )
        )

    def absorbance(
        self,
        ref,
        wells,
        wavelength,
        dataref,
        flashes=25,
        incubate_before=None,
        temperature=None,
        settle_time=None,
    ):
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

        .. code-block:: none

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
        ref : str or Container
            Object to execute the absorbance read on
        wells : list(Well) or WellGroup or Well
            WellGroup of wells to be measured or a list of well references in
            the form of ["A1", "B1", "C5", ...]
        wavelength : str or Unit
            wavelength of light absorbance to be read for the indicated wells
        dataref : str
            name of this specific dataset of measured absorbances
        flashes : int, optional
            number of flashes for the read
        temperature: str or Unit, optional
            set temperature to heat plate reading chamber
        settle_time: Unit, optional
            the time before the start of the measurement, defaults
            to vendor specifications
        incubate_before: dict, optional
            parameters for incubation before executing the plate read
            See Also :meth:`Absorbance.builders.incubate_params`

        Returns
        -------
        Absorbance
            Returns the :py:class:`autoprotocol.instruction.Absorbance`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            Invalid input types, e.g. wells given is of type Well, WellGroup
            or list of wells
        ValueError
            Wells specified are not from the same container
        ValueError
            Settle time has to be greater than 0
        UnitError
            Settle time is not of type Unit

        """
        wells = WellGroup(wells)
        container = set([w.container for w in wells])
        if len(container) > 1:
            raise ValueError(
                "All wells need to be on the same container for Absorbance"
            )
        wells = [str(w.index) for w in wells]

        if incubate_before:
            Absorbance.builders.incubate_params(**incubate_before)

        if settle_time:
            try:
                settle_time = Unit(settle_time)
                if settle_time < Unit(0, "second"):
                    raise ValueError(
                        "'settle_time' must be a time equal " "to or greater than 0."
                    )
            except UnitError:
                raise UnitError("'settle_time' must be of type Unit.")

        return self._append_and_return(
            Absorbance(
                ref,
                wells,
                wavelength,
                dataref,
                flashes,
                incubate_before,
                temperature,
                settle_time,
            )
        )

    def fluorescence(
        self,
        ref,
        wells,
        excitation,
        emission,
        dataref,
        flashes=25,
        temperature=None,
        gain=None,
        incubate_before=None,
        detection_mode=None,
        position_z=None,
        settle_time=None,
        lag_time=None,
        integration_time=None,
    ):
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

        .. code-block:: none

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
        ref : str or Container
            Container to plate read.
        wells : list(Well) or WellGroup or Well
            WellGroup of wells to be measured or a list of well references in
            the form of ["A1", "B1", "C5", ...]
        excitation : str or Unit
            Wavelength of light used to excite the wells indicated
        emission : str or Unit
            Wavelength of light to be measured for the indicated wells
        dataref : str
            Name of this specific dataset of measured fluoresence
        flashes : int, optional
            Number of flashes.
        temperature: str or Unit, optional
            set temperature to heat plate reading chamber
        gain: float, optional
            float between 0 and 1, multiplier, gain=0.2 of maximum signal
            amplification
        incubate_before: dict, optional
            parameters for incubation before executing the plate read
            See Also :meth:`Fluorescence.builders.incubate_params`
        detection_mode: str, optional
            set the detection mode of the optics, ["top", "bottom"],
            defaults to vendor specified defaults.
        position_z: dict, optional
            distance from the optics to the surface of the plate transport,
            only valid for "top" detection_mode and vendor capabilities.
            Specified as either a set distance - "manual", OR calculated from
            a WellGroup - "calculated_from_wells".   Only one position_z
            determination may be specified

            .. code-block:: none

                position_z = {
                    "manual": Unit
                    - OR -
                    "calculated_from_wells": []
                }

        settle_time: Unit, optional
            the time before the start of the measurement, defaults
            to vendor specifications
        lag_time: Unit, optional
            time between flashes and the start of the signal integration,
            defaults to vendor specifications
        integration_time: Unit, optional
            duration of the signal recording, per Well, defaults to vendor
            specifications

        Examples
        --------
        position_z:

            .. code-block:: none

                position_z = {
                    "calculated_from_wells": ["plate/A1", "plate/A2"]
                }

                -OR-

                position_z = {
                    "manual": "20:micrometer"
                }

        Returns
        -------
        Fluorescence
            Returns the :py:class:`autoprotocol.instruction.Fluorescence`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            Invalid input types, e.g. wells given is of type Well, WellGroup
            or list of wells
        ValueError
            Wells specified are not from the same container
        ValueError
            Settle time, integration time or lag time has to be greater than 0
        UnitError
            Settle time, integration time, lag time or position z is not
            of type Unit
        ValueError
            Unknown value given for `detection_mode`
        ValueError
            Position z specified for non-top detection mode
        KeyError
            For position_z, only `manual` and `calculated_from_wells`
            is allowed
        NotImplementedError
            Specifying `calculated_from_wells` as that has not been
            implemented yet

        """
        wells = WellGroup(wells)
        container = set([w.container for w in wells])
        if len(container) > 1:
            raise ValueError(
                "All wells need to be on the same container for Fluorescence"
            )
        wells = [str(w.index) for w in wells]

        if gain is not None and not (0 <= gain <= 1):
            raise ValueError(
                f"fluorescence gain set to {gain} must be between 0 and 1, "
                f"inclusive"
            )

        if incubate_before:
            Fluorescence.builders.incubate_params(**incubate_before)

        valid_detection_modes = ["top", "bottom"]
        if detection_mode and detection_mode not in valid_detection_modes:
            raise ValueError(
                f"Unknown value for 'detection_mode'.  Must be one of "
                f"{valid_detection_modes}."
            )
        if detection_mode == "bottom" and position_z:
            raise ValueError(
                "position_z is only valid for 'top' detection_mode " "measurements."
            )
        if settle_time:
            try:
                settle_time = Unit(settle_time)
                if settle_time < Unit(0, "second"):
                    raise ValueError(
                        "'settle_time' must be a time equal " "to or greater than 0."
                    )
            except UnitError:
                raise UnitError("'settle_time' must be of type Unit.")
        if lag_time:
            try:
                lag_time = Unit(lag_time)
                if lag_time < Unit(0, "second"):
                    raise ValueError(
                        "'lag_time' must be a time equal " "to or greater than 0."
                    )
            except UnitError:
                raise UnitError("'lag_time' must be of type Unit.")
        if integration_time:
            try:
                integration_time = Unit(integration_time)
                if integration_time < Unit(0, "second"):
                    raise ValueError(
                        "'integration_time' must be a time equal "
                        "to or greater than 0."
                    )
            except UnitError:
                raise UnitError("'integration_time' must be of type Unit.")
        if position_z:
            valid_pos_z = ["manual", "calculated_from_wells"]
            if not isinstance(position_z, dict):
                raise TypeError("'position_z' must be of type dict.")
            if len(position_z.keys()) > 1:
                raise ValueError(
                    "'position_z' can only have one mode of calculation "
                    "specified: 'manual' or 'calculated_from_wells'."
                )
            for k in position_z.keys():
                if k not in valid_pos_z:
                    raise KeyError(
                        f"'position_z' keys can only be 'manual' or 'calculated_from_wells'. '{k}' is not a recognized key."
                    )
            if "manual" in position_z.keys():
                try:
                    manual = Unit(position_z["manual"])
                    if manual < Unit(0, "micrometer"):
                        raise ValueError(
                            "'manual' z_position must be a length equal "
                            "to or greater than 0."
                        )
                except UnitError:
                    raise UnitError("'manual' position_z must be of type Unit.")
            if "calculated_from_wells" in position_z.keys():
                # blocking calculated_from_wells until fully implemented
                # remove below RunTimeError to release feature
                raise NotImplementedError(
                    "This feature, 'calculated_from_wells', "
                    "has not been implemented yet.  Please use "
                    "'position_z':{'manual': 'set_value'} to "
                    "specify a position_z."
                )

                # pragma pylint: disable=unreachable, unused-variable
                z_ws = position_z["calculated_from_wells"]
                if isinstance(z_ws, Well):
                    z_ws = [z_ws]
                    position_z["calculated_from_wells"] = z_ws
                elif isinstance(z_ws, list):
                    if not all(isinstance(w, Well) for w in z_ws):
                        raise TypeError(
                            "All elements in list must be wells for "
                            "position_z, 'calculated_from_wells'."
                        )
                else:
                    raise TypeError(
                        "Wells specified for 'calculated_from_wells' "
                        "must be Well, list of wells, WellGroup."
                    )
                # check z_ws against container/ref for measurement
                # if ref is Container
                if isinstance(ref, Container):
                    try:
                        valid_z_ws = ref.wells(z_ws)
                    except ValueError:
                        raise ValueError(
                            "Well indices specified for "
                            "'calculated_from_wells' must "
                            "be valid wells of the ref'd "
                            "container."
                        )
                # pragma pylint: enable=unreachable, unused-variable

        return self._append_and_return(
            Fluorescence(
                ref,
                wells,
                excitation,
                emission,
                dataref,
                flashes,
                incubate_before,
                temperature,
                gain,
                detection_mode,
                position_z,
                settle_time,
                lag_time,
                integration_time,
            )
        )

    def luminescence(
        self,
        ref,
        wells,
        dataref,
        incubate_before=None,
        temperature=None,
        settle_time=None,
        integration_time=None,
    ):
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

        .. code-block:: none

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
        ref : str or Container
            Container to plate read.
        wells : list(Well) or WellGroup or Well
            WellGroup of wells to be measured or a list of well references in
            the form of ["A1", "B1", "C5", ...]
        dataref : str
            Name of this dataset of measured luminescence readings.
        temperature: str or Unit, optional
            set temperature to heat plate reading chamber
        settle_time: Unit, optional
            the time before the start of the measurement, defaults
            to vendor specifications
        incubate_before: dict, optional
            parameters for incubation before executing the plate read
            See Also :meth:`Absorbance.builders.incubate_params`
        integration_time: Unit, optional
            duration of the signal recording, per Well, defaults to vendor
            specifications

        Returns
        -------
        Luminescence
            Returns the :py:class:`autoprotocol.instruction.Luminescence`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            Invalid input types, e.g. wells given is of type Well, WellGroup
            or list of wells
        ValueError
            Wells specified are not from the same container
        ValueError
            Settle time or integration time has to be greater than 0
        UnitError
            Settle time or integration time is not of type Unit

        """
        wells = WellGroup(wells)
        container = set([w.container for w in wells])
        if len(container) > 1:
            raise ValueError(
                "All wells need to be on the same container for Luminescence"
            )
        wells = [str(w.index) for w in wells]

        if incubate_before:
            Luminescence.builders.incubate_params(**incubate_before)

        if settle_time:
            try:
                settle_time = Unit(settle_time)
                if settle_time < Unit(0, "second"):
                    raise ValueError(
                        "'settle_time' must be a time equal " "to or greater than 0."
                    )
            except UnitError:
                raise UnitError("'settle_time' must be of type Unit.")
        if integration_time:
            try:
                integration_time = Unit(integration_time)
                if integration_time < Unit(0, "second"):
                    raise ValueError(
                        "'integration_time' must be a time equal "
                        "to or greater than 0."
                    )
            except UnitError:
                raise UnitError("'integration_time' must be of type Unit.")

        return self._append_and_return(
            Luminescence(
                ref,
                wells,
                dataref,
                incubate_before,
                temperature,
                settle_time,
                integration_time,
            )
        )

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

        .. code-block:: none

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
        wells : list(Well) or WellGroup or Well
            List of wells or WellGroup containing wells to be
            separated on gel.
        volume : str or Unit
            Volume of liquid to be transferred from each well specified to a
            lane of the gel.
        matrix : str
            Matrix (gel) in which to gel separate samples
        ladder : str
            Ladder by which to measure separated fragment size
        duration : str or Unit
            Length of time to run current through gel.
        dataref : str
            Name of this set of gel separation results.

        Returns
        -------
        GelSeparate
            Returns the :py:class:`autoprotocol.instruction.GelSeparate`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            Invalid input types, e.g. wells given is of type Well, WellGroup
            or list of wells
        ValueError
            Specifying more wells than the number of available lanes in
            the selected matrix

        """
        # Check valid well inputs
        if not is_valid_well(wells):
            raise TypeError(
                "Wells must be of type Well, list of Wells, or " "WellGroup."
            )
        if isinstance(wells, Well):
            wells = WellGroup(wells)
        for w in wells:
            self._remove_cover(w.container, "gel separate")
        max_well = int(matrix.split("(", 1)[1].split(",", 1)[0])
        if len(wells) > max_well:
            raise ValueError(
                "Number of wells is greater than available" "lanes in matrix"
            )

        return self._append_and_return(
            GelSeparate(wells, volume, matrix, ladder, duration, dataref)
        )

    def gel_purify(self, extracts, volume, matrix, ladder, dataref):
        """
        Separate nucleic acids on an agarose gel and purify according to
        parameters. If gel extract lanes are not specified, they will be
        sequentially ordered and purified on as many gels as necessary.

        Each element in extracts specifies a source loaded in a single lane of
        gel with a list of bands that will be purified from that lane. If the
        same source is to be run on separate lanes, a new dictionary must be
        added to extracts. It is also possible to add an element to extract
        with a source but without a list of bands. In that case, the source
        will be run in a lane without extraction.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_wells = p.ref("test_plate", None, "96-pcr",
                                 discard=True).wells_from(0, 8)
            extract_wells = [p.ref("extract_" + str(i.index), None,
                                   "micro-1.5", storage="cold_4").well(0)
                             for i in sample_wells]


            extracts = [make_gel_extract_params(
                            w,
                            make_band_param(
                                "TE",
                                "5:microliter",
                                80,
                                79,
                                extract_wells[i]))
                            for i, w in enumerate(sample_wells)]

            p.gel_purify(extracts, "10:microliter",
                         "size_select(8,0.8%)", "ladder1",
                         "gel_purify_example")

        Autoprotocol Output:

        For extracts[0]

        .. code-block:: none

            {
                "band_list": [
                    {
                        "band_size_range": {
                            "max_bp": 80,
                            "min_bp": 79
                        },
                        "destination": Well(Container(extract_0), 0, None),
                        "elution_buffer": "TE",
                        "elution_volume": "Unit(5.0, 'microliter')"
                    }
                ],
                "gel": None,
                "lane": None,
                "source": Well(Container(test_plate), 0, None)
            }


        Parameters
        ----------
        extracts: list(dict)
            List of gel extraction parameters
            See Also :meth:`GelPurify.builders.extract`
        volume: str or Unit
            Volume of liquid to be transferred from each well specified to a
            lane of the gel.
        matrix: str
            Matrix (gel) in which to gel separate samples
        ladder: str
            Ladder by which to measure separated fragment size
        dataref: str
            Name of this set of gel separation results.

        Returns
        -------
        GelPurify
            Returns the :py:class:`autoprotocol.instruction.GelPurify`
            instruction created from the specified parameters

        Raises
        -------
        RuntimeError
            If matrix is not properly formatted.
        AttributeError
            If extract parameters are not a list of dictionaries.
        KeyError
            If extract parameters do not contain the specified parameter keys.
        ValueError
            If min_bp is greater than max_bp.
        ValueError
            If extract destination is not of type Well.
        ValueError
            If extract elution volume is not of type Unit
        ValueError
            if extract elution volume is not greater than 0.
        RuntimeError
            If gel extract lanes are set for some but not all extract wells.
        RuntimeError
            If all samples do not fit on single gel type.
        TypeError
            If lane designated for gel extracts is not an integer.
        RuntimeError
            If designated lane index is outside lanes within the gel.
        RuntimeError
            If lanes not designated and number of extracts not equal to number
            of samples.

        """

        from itertools import groupby
        from operator import itemgetter

        try:
            max_well = int(matrix.split("(", 1)[1].split(",", 1)[0])
        except (AttributeError, IndexError):
            raise RuntimeError("Matrix specified is not properly formatted.")

        volume = Unit(volume)
        if volume <= Unit("0:microliter"):
            raise ValueError(f"Volume: {volume}, must be greater than 0:microliter")

        if not isinstance(ladder, str):
            raise TypeError(f"Ladder: {ladder}, must be a string")

        if not isinstance(dataref, str):
            raise TypeError(f"Datref: {dataref}, must be a string")

        if not isinstance(extracts, list):
            extracts = [extracts]

        extracts = [GelPurify.builders.extract(**_) for _ in extracts]

        gel_set = [e["gel"] for e in extracts]
        lane_set = [e["lane"] for e in extracts]

        if None in gel_set:
            if any(gel_set):
                raise RuntimeError(
                    "If one extract has gel set, all extracts must have " "gel set"
                )
            else:
                if None in lane_set:
                    if any(lane_set):
                        raise RuntimeError(
                            "If one extract has lane set, all extracts must "
                            "have lane set"
                        )
                    else:
                        for i, e in enumerate(extracts):
                            e["gel"] = i // max_well
                            e["lane"] = i % max_well
                else:
                    for e in extracts:
                        e["gel"] = 0

        sort_key = itemgetter("gel")
        parsed_extracts = [
            list(grp)
            for key, grp in groupby(sorted(extracts, key=sort_key), key=sort_key)
        ]

        instructions = []
        for pe in parsed_extracts:

            lane_set = [e["lane"] for e in pe]

            if len(lane_set) > max_well:
                raise RuntimeError(
                    f"The gel is not large enough to accomodate all lanes: gel has {max_well} wells, {len(lane_set)} lanes specified"
                )

            if None in lane_set:
                if any(lane_set):
                    raise RuntimeError(
                        "If one extract has lane set, all extracts must have "
                        "lane set"
                    )
                else:
                    for i, e in enumerate(pe):
                        e["lane"] = i % max_well
                    lane_set = [e["lane"] for e in pe]

            if sorted(lane_set) != list(range(0, max(lane_set) + 1)):
                raise RuntimeError("Lanes must be contiguous, unique, and start from 0")

            if len(parsed_extracts) > 1:
                dataref_gel = f"{dataref}_{pe[0]['gel']}"
            else:
                dataref_gel = dataref

            pe = sorted(pe, key=itemgetter("lane"))

            samples = [e["source"] for e in pe]

            pe_unpacked = []
            for e in pe:
                for b in e["band_list"]:
                    ext = b
                    ext["lane"] = e["lane"]
                    pe_unpacked.append(ext)

            instructions.append(
                self._append_and_return(
                    GelPurify(samples, volume, matrix, ladder, dataref_gel, pe_unpacked)
                )
            )

        return instructions

    def seal(self, ref, type=None, mode=None, temperature=None, duration=None):
        """
        Seal indicated container using the automated plate sealer.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-pcr",
                                 storage="warm_37")

            p.seal(sample_plate, mode="thermal", temperature="160:celsius")

        Autoprotocol Output:

        .. code-block:: none

            "instructions": [
                {
                    "object": "sample_plate",
                    "type": "ultra-clear",
                    "mode": "thermal",
                    "mode_params": {
                        "temperature": "160:celsius"
                    }
                    "op": "seal"
                }
            ]

        Parameters
        ----------
        ref : Container
           Container to be sealed
        type : str, optional
            Seal type to be used, such as "ultra-clear" or "foil".
        mode: str, optional
            Sealing method to be used, such as "thermal" or "adhesive". Defaults
            to None, which is interpreted sensibly based on the execution
            environment.
        temperature: Unit or str, optional
            Temperature at which to melt the sealing film onto the ref. Only
            applicable to thermal sealing; not respected if the sealing mode
            is adhesive. If unspecified, thermal sealing temperature defaults
            correspond with manufacturer-recommended or internally-optimized
            values for the target container type. Applies only to thermal
            sealing.
        duration: Unit or str, optional
            Duration for which to press the (heated, if thermal) seal down on
            the ref. Defaults to manufacturer-recommended or internally-
            optimized seal times for the target container type. Currently
            applies only to thermal sealing.

        Returns
        -------
        Seal
            Returns the :py:class:`autoprotocol.instruction.Seal`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            If ref is not of type Container.
        RuntimeError
            If container type does not have `seal` capability.
        RuntimeError
            If seal is not a valid seal type.
        RuntimeError
            If the sealing mode is invalid, or incompatible with the given ref
        RuntimeError
            If thermal sealing params (temperature and/or duration) are
            specified alongside an adhesive sealing mode.
        RuntimeError
            If specified thermal sealing parameters are invalid
        RuntimeError
            If container is already covered with a lid.

        """
        SEALING_MODES = ["thermal", "adhesive"]

        if not isinstance(ref, Container):
            raise TypeError("Container to seal must be of type Container.")
        if "seal" not in ref.container_type.capabilities:
            raise RuntimeError(
                f"Container '{ref.name}' type '{ref.container_type.shortname}',"
                f" cannot be sealed."
            )
        if type is None:
            type = ref.container_type.seal_types[0]
        if type not in SEAL_TYPES:
            raise RuntimeError(f"{type} is not a valid seal type")
        if ref.is_covered():
            raise RuntimeError("A container cannot be sealed over a lid.")
        if not (mode is None or mode in SEALING_MODES):
            raise RuntimeError(f"{mode} is not a valid sealing mode")
        if temperature is not None or duration is not None:
            if mode == "adhesive":
                raise RuntimeError(
                    "Thermal sealing parameters `temperature` and `duration` "
                    "are incompatible with the chosen adhesive sealing mode."
                )
            mode = "thermal"
            mode_params = dict()

            if temperature is not None:
                mode_params["temperature"] = parse_unit(temperature, "celsius")
            if duration is not None:
                mode_params["duration"] = parse_unit(duration, "second")
        else:
            mode_params = None

        if not ref.is_sealed():
            ref.cover = type
            return self._append_and_return(Seal(ref, type, mode, mode_params))

    def unseal(self, ref):
        """
        Remove seal from indicated container using the automated plate
        unsealer.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_plate = p.ref("sample_plate",
                                 None,
                                 "96-pcr",
                                 storage="warm_37")
            # a plate must be sealed to be unsealed
            p.seal(sample_plate)

            p.unseal(sample_plate)

        Autoprotocol Output:

        .. code-block:: none

            "instructions": [
                {
                  "object": "sample_plate",
                  "op": "seal",
                  "type": "ultra-clear"
                },
                {
                  "object": "sample_plate",
                  "op": "unseal"
                }
              ]

        Parameters
        ----------
        ref : Container
            Container to be unsealed.

        Returns
        -------
        Unseal
            Returns the :py:class:`autoprotocol.instruction.Unseal`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
          If ref is not of type Container.
        RuntimeError
          If container is covered with a lid not a seal.

        """
        if not isinstance(ref, Container):
            raise TypeError("Container to unseal must be of type Container.")
        if ref.is_covered():
            raise RuntimeError(
                "A container with a cover cannot be unsealed, "
                "use the instruction uncover."
            )
        if ref.is_sealed():
            ref.cover = None
            unseal_inst = Unseal(ref)
            return self._append_and_return(unseal_inst)

    def cover(self, ref, lid=None, retrieve_lid=None):
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

        .. code-block:: none

            "instructions": [
                {
                    "lid": "universal",
                    "object": "sample_plate",
                    "op": "cover"
                }
            ]

        Parameters
        ----------
        ref : Container
            Container to be convered.
        lid : str, optional
            Type of lid to cover the container. Must be a valid lid type for
            the container type.
        retrieve_lid: bool, optional
            Flag to retrieve lid from previously stored location (see uncover).

        Returns
        -------
        Cover
            Returns the :py:class:`autoprotocol.instruction.Cover`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            If ref is not of type Container.
        RuntimeError
            If container type does not have `cover` capability.
        RuntimeError
            If lid is not a valid lid type.
        RuntimeError
            If container is already sealed with a seal.
        TypeError
            If retrieve_lid is not a boolean.

        """
        if not isinstance(ref, Container):
            raise TypeError("Container to cover must be of type Container.")
        if "cover" not in ref.container_type.capabilities:
            raise RuntimeError(
                f"Container '{ref.name}' type '{ref.container_type.shortname}',"
                f" cannot be covered."
            )
        if lid is None:
            lid = ref.container_type.cover_types[0]
        if lid not in COVER_TYPES:
            raise RuntimeError(f"{lid} is not a valid lid type")
        if ref.is_sealed():
            raise RuntimeError("A container cannot be covered over a seal.")
        if retrieve_lid is not None and not isinstance(retrieve_lid, bool):
            raise TypeError("Cover: retrieve_lid must be of type bool")
        if not ref.is_covered():
            ref.cover = lid
            return self._append_and_return(Cover(ref, lid, retrieve_lid))

    def uncover(self, ref, store_lid=None):
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

        .. code-block:: none

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
        ref : Container
            Container to remove lid.
        store_lid: bool, optional
            Flag to store the uncovered lid.

        Returns
        -------
        Uncover
            Returns the :py:class:`autoprotocol.instruction.Uncover`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            If ref is not of type Container.
        RuntimeError
            If container is sealed with a seal not covered with a lid.
        TypeError
            If store_lid is not a boolean.

        """
        if not isinstance(ref, Container):
            raise TypeError("Container to uncover must be of type Container.")
        if ref.is_sealed():
            raise RuntimeError(
                "A container with a seal cannot be uncovered, "
                "use the instruction unseal."
            )
        if store_lid is not None and not isinstance(store_lid, bool):
            raise TypeError("Uncover: store_lid must be of type bool")
        if ref.is_covered():
            ref.cover = None
            return self._append_and_return(Uncover(ref, store_lid))

    def flow_cytometry(
        self,
        dataref,
        samples,
        lasers,
        collection_conditions,
        width_threshold=None,
        window_extension=None,
        remove_coincident_events=None,
    ):
        """
        A non-ambiguous set of parameters for performing flow cytometry.

        Parameters
        ----------
        dataref : str
            Name of dataset that will be returned.
        samples : list(Well) or Well or WellGroup
            Wells to be analyzed
        lasers : list(dict)
            See FlowCytometryBuilders.laser.
        collection_conditions : dict
            See FlowCytometryBuilders.collection_conditions.
        width_threshold : int or float, optional
            Threshold to determine width measurement.
        window_extension : int or float, optional
            Front and rear window extension.
        remove_coincident_events : bool, optional
            Remove coincident events.

        Returns
        -------
        FlowCytometry
            Returns a :py:class:`autoprotocol.instruction.FlowCytometry`
            instruction created from the specified parameters.

        Raises
        ------
        TypeError
            If `lasers` is not of type list.
        TypeError
            If `samples` is not of type Well, list of Well, or WellGroup.
        TypeError
            If `width_threshold` is not a number.
        TypeError
            If `window_extension` is not a number.
        TypeError
            If `remove_coincident_events` is not of type bool.

        Examples
        --------
        Example flow cytometry protocol

        .. code-block:: python

            p = Protocol()
            plate = p.ref("sample-plate", cont_type="384-flat", discard=True)

            lasers = [FlowCytometry.builders.laser(
                excitation="405:nanometers",
                channels=[
                    FlowCytometry.builders.channel(
                        emission_filter=FlowCytometry.builders.emission_filter(
                            channel_name="VL1",
                            shortpass="415:nanometers",
                            longpass="465:nanometers"
                        ),
                        detector_gain="10:millivolts"
                    )
                ]
            )]

            collection_conds = FlowCytometry.builders.collection_conditions(
                acquisition_volume="5.0:ul",
                flowrate="12.5:ul/min",
                wait_time="10:seconds",
                mix_cycles=10,
                mix_volume="10:ul",
                rinse_cycles=10
            )

            p.flow_cytometry("flow-1234", plate.wells_from(0, 3), lasers,
                             collection_conds)

        Autoprotocol Output:

        .. code-block:: json

            {
              "op": "flow_cytometry",
              "dataref": "flow-1234",
              "samples": [
                "sample-plate/0",
                "sample-plate/1",
                "sample-plate/2"
              ],
              "lasers": [
                {
                  "excitation": "405:nanometer",
                  "channels": [
                    {
                      "emission_filter": {
                        "channel_name": "VL1",
                        "shortpass": "415:nanometer",
                        "longpass": "465:nanometer"
                      },
                      "detector_gain": "10:millivolt"
                    }
                  ]
                }
              ],
              "collection_conditions": {
                "acquisition_volume": "5:microliter",
                "flowrate": "12.5:microliter/minute",
                "stop_criteria": {
                  "volume": "5:microliter"
                },
                "wait_time": "10:second",
                "mix_cycles": 10,
                "mix_volume": "10:microliter",
                "rinse_cycles": 10
              }
            }

        """
        if not isinstance(lasers, list):
            raise TypeError("lasers must be of type list.")

        if not is_valid_well(samples):
            raise TypeError(
                "samples must be of type Well, list of Well, " "or WellGroup."
            )

        if width_threshold is not None:
            if not isinstance(width_threshold, Number):
                raise TypeError("width_threshold must be a number.")

        if window_extension is not None:
            if not isinstance(window_extension, Number):
                raise TypeError("window_extension must be a number.")

        if remove_coincident_events is not None:
            if not isinstance(remove_coincident_events, bool):
                raise TypeError("remove_coincident_events must be of type " "bool.")

        lasers = [FlowCytometry.builders.laser(**_) for _ in lasers]

        collection_conditions = FlowCytometry.builders.collection_conditions(
            **collection_conditions
        )

        return self._append_and_return(
            FlowCytometry(
                dataref,
                samples,
                lasers,
                collection_conditions,
                width_threshold,
                window_extension,
                remove_coincident_events,
            )
        )

    def flow_analyze(
        self, dataref, FSC, SSC, neg_controls, samples, colors=None, pos_controls=None
    ):
        """
        Perform flow cytometry. The instruction will be executed within the
        voltage range specified for each channel, optimized for the best sample
        separation/distribution that can be achieved within these limits. The
        vendor will specify the device that this instruction is executed on and
        which excitation and emission spectra are available. At least one
        negative control is required, which will be used to define data
        acquisition parameters as well as to determine any autofluorescent
        properties for the sample set. Additional negative positive control
        samples are optional. Positive control samples will be used to
        optimize single color signals and, if desired, to minimize bleed into
        other channels.


        For each sample this instruction asks you to specify the `volume`
        and/or `captured_events`. Vendors might also require `captured_events`
        in case their device does not support volumetric sample intake. If
        both conditions are supported, the vendor will specify if data will be
        collected only until the first one is met or until both conditions are
        fulfilled.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            dataref = "test_ref"
            FSC = {"voltage_range": {"low": "230:volt", "high": "280:volt"},
                   "area": True, "height": True, "weight": False}
            SSC = {"voltage_range": {"low": "230:volt", "high": "280:volt"},
                   "area": True, "height": True, "weight": False}
            neg_controls = {"well": "well0", "volume": "100:microliter",
                            "captured_events": 5, "channel": "channel0"}
            samples = [
                {
                    "well": "well0",
                    "volume": "100:microliter",
                    "captured_events": 9
                }
            ]

            p.flow_analyze(dataref, FSC, SSC, neg_controls,
                           samples, colors=None, pos_controls=None)


        Autoprotocol Output:

        .. code-block:: json

            {
                "channels": {
                    "FSC": {
                        "voltage_range": {
                            "high": "280:volt",
                            "low": "230:volt"
                        },
                        "area": true,
                        "height": true,
                        "weight": false
                    },
                    "SSC": {
                        "voltage_range": {
                            "high": "280:volt",
                            "low": "230:volt"
                        },
                        "area": true,
                        "height": true,
                        "weight": false
                    }
                },
                "op": "flow_analyze",
                "negative_controls": {
                    "channel": "channel0",
                    "well": "well0",
                    "volume": "100:microliter",
                    "captured_events": 5
                },
                "dataref": "test_ref",
                "samples": [
                    {
                        "well": "well0",
                        "volume": "100:microliter",
                        "captured_events": 9
                    }
                ]
            }

        Parameters
        ----------
        dataref : str
            Name of flow analysis dataset generated.
        FSC : dict
            Dictionary containing FSC channel parameters in the form of:

            .. code-block:: none

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

            .. code-block:: none

                {
                    "voltage_range": {
                        "low": <voltage>,
                        "high": <voltage>"
                    },
                    "area": true,             //default: true
                    "height": true,           //default: false
                    "weight": false           //default: false
                }

        neg_controls : list(dict)
            List of negative control wells in the form of:

            .. code-block:: none

                {
                    "well": well,
                    "volume": volume,
                    "captured_events": integer,    // optional, default infinity
                    "channel": [channel_name]
                }

            at least one negative control is required.
        samples : list(dict)
            List of samples in the form of:

            .. code-block:: none

                {
                    "well": well,
                    "volume": volume,
                    "captured_events": integer     // optional, default infinity
                }

            at least one sample is required
        colors : list(dict), optional
            Optional list of colors in the form of:

            .. code-block:: none

                [
                    {
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
                    }, ...
                ]

        pos_controls : list(dict), optional
            Optional list of positive control wells in the form of:

            .. code-block:: none

                [
                    {
                        "well": well,
                        "volume": volume,
                        "captured_events": integer,      // default: infinity
                        "channel": [channel_name],
                        "minimize_bleed": [{             // optional
                          "from": color,
                          "to": [color]
                    }, ...
                ]

        Returns
        -------
        FlowAnalyze
            Returns the :py:class:`autoprotocol.instruction.FlowAnalyze`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            If inputs are not of the correct type.
        UnitError
            If unit inputs are not properly formatted.
        AssertionError
            If required parameters are missing.
        ValueError
            If volumes are not correctly formatted or present.

      """
        sources = []
        controls = []
        if not isinstance(samples, list):
            raise TypeError("Samples must be of type list.")
        else:
            sources.extend(samples)
        if not isinstance(neg_controls, list):
            raise TypeError("Neg_controls must be of type list.")
        else:
            sources.extend(neg_controls)
            controls.extend(neg_controls)
        if pos_controls and not isinstance(pos_controls, list):
            raise TypeError("Pos_controls must be of type list.")
        elif pos_controls:
            sources.extend(pos_controls)
            controls.extend(neg_controls)

        for s in sources:
            if not isinstance(s.get("well"), Well):
                raise TypeError(
                    "The well for each sample or control must " "be of type Well."
                )
            try:
                Unit(s.get("volume"))
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Each sample or control must indicate a "
                    f"volume of type unit. {e}"
                )
            if s.get("captured_events") and not isinstance(
                s.get("captured_events"), int
            ):
                raise TypeError(
                    "captured_events is optional, if given it"
                    " must be of type integer."
                )
        for c in controls:
            if not isinstance(c.get("channel"), list):
                raise TypeError(
                    "Channel must be a list of strings "
                    "indicating the colors/channels that this"
                    " control is to be used for."
                )
            if c.get("minimize_bleed") and not isinstance(
                c.get("minimize_bleed"), list
            ):
                raise TypeError("Minimize_bleed must be of type list.")
            elif c.get("minimize_bleed"):
                for b in c["minimize_bleed"]:
                    if not isinstance(b, dict):
                        raise TypeError(
                            "Minimize_bleed must be a list of "
                            "dictonaries. Dictonary was not found"
                        )
                    else:
                        if not b.get("from"):
                            raise ValueError(
                                "Minimize_bleed dictonaries must" " have a key `from`"
                            )
                        else:
                            if not isinstance(b["from"], str):
                                raise TypeError(
                                    "Minimize_bleed `from` must "
                                    "have a string as value"
                                )
                        if not b.get("to"):
                            raise ValueError(
                                "Minimize_bleed dictonaries must" " have a key `to`"
                            )
                        else:
                            if not isinstance(b["to"], list):
                                raise ValueError(
                                    "Minimize_bleed `to` must " "have a list as value"
                                )
                            else:
                                for t in b["to"]:
                                    if not isinstance(t, str):
                                        raise TypeError(
                                            "Minimize_bleed `to` "
                                            "list must contain "
                                            "strings."
                                        )
        assert FSC and SSC, "You must include parameters for FSC and SSC " "channels."
        channels = {}
        channels["FSC"] = FSC
        channels["SSC"] = SSC
        for c in channels.values():
            if not isinstance(c, dict):
                raise TypeError("Each channel must be of type dict.")
            assert c["voltage_range"], (
                "You must include a voltage_range for" " each channel."
            )
            assert c["voltage_range"]["high"], (
                "You must include an upper "
                "limit for the volage range"
                "in each channel."
            )
            assert c["voltage_range"]["low"], (
                "You must include a lower "
                "limit for the volage range "
                "in each channel."
            )
        if colors:
            if not isinstance(colors, list):
                raise TypeError("Colors must be of type list.")
            else:
                for c in colors:
                    if not isinstance(c, dict):
                        raise TypeError("Colors must contain elements of " "type dict.")
                    else:
                        if not c.get("name") or not isinstance(c.get("name"), str):
                            raise TypeError(
                                "Each color must have a `name` "
                                "that is of type string."
                            )
                        if c.get("emission_wavelength"):
                            try:
                                Unit(c.get("emission_wavelength"))
                            except (UnitError):
                                raise UnitError(
                                    "Each `emission_wavelength` "
                                    "must be of type unit."
                                )
                        else:
                            raise ValueError(
                                "Each color must have an " "`emission_wavelength`."
                            )
                        if c.get("excitation_wavelength"):
                            try:
                                Unit(c.get("excitation_wavelength"))
                            except (UnitError):
                                raise UnitError(
                                    "Each `excitation_wavelength` "
                                    "must be of type unit."
                                )
                        else:
                            raise ValueError(
                                "Each color must have an " "`excitation_wavelength`."
                            )

        for s in sources:
            self._remove_cover(s["well"].container, "flow_analyze")

        return self._append_and_return(
            FlowAnalyze(dataref, FSC, SSC, neg_controls, samples, colors, pos_controls)
        )

    def oligosynthesize(self, oligos):
        """
        Specify a list of oligonucleotides to be synthesized and a destination
        for each product.

        Example Usage:

        .. code-block:: python

            oligo_1 = p.ref("oligo_1", None, "micro-1.5", discard=True)

            p.oligosynthesize([{"sequence": "CATGGTCCCCTGCACAGG",
                                "destination": oligo_1.well(0),
                                "scale": "25nm",
                                "purification": "standard"}])

        Autoprotocol Output:

        .. code-block:: none

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
        oligos : list(dict)
            List of oligonucleotides to synthesize.  Each dictionary should
            contain the oligo's sequence, destination, scale and purification

            .. code-block:: none

                [
                    {
                        "destination": "my_plate/A1",
                        "sequence": "GATCRYMKSWHBVDN",
                        // - standard IUPAC base codes
                        // - IDT also allows rX (RNA), mX (2' O-methyl RNA), and
                        //   X*/rX*/mX* (phosphorothioated)
                        // - they also allow inline annotations for
                        //   modifications,
                        //   e.g. "GCGACTC/3Phos/" for a 3' phosphorylation
                        //   e.g. "aggg/iAzideN/cgcgc" for an
                        //   internal modification
                        "scale": "25nm" | "100nm" | "250nm" | "1um",
                        "purification": "standard" | "page" | "hplc",
                        // default: standard
                    }, ...
                ]

        Returns
        -------
        Oligosynthesize
            Returns the :py:class:`autoprotocol.instruction.Oligosynthesize`
            instruction created from the specified parameters

        """
        return self._append_and_return(Oligosynthesize(oligos))

    def autopick(self, sources, dests, min_abort=0, criteria=None, dataref="autopick"):
        """

        Pick colonies from the agar-containing location(s) specified in
        `sources` to the location(s) specified in `dests` in highest to lowest
        rank order until there are no more colonies available.  If fewer than
        min_abort pickable colonies have been identified from the location(s)
        specified in `sources`, the run will stop and no further instructions
        will be executed.

        Example Usage:

        Autoprotocol Output:

        Parameters
        ----------
        sources : Well or WellGroup or list(Well)
            Reference wells containing agar and colonies to pick
        dests : Well or WellGroup or list(Well)
            List of destination(s) for picked colonies
        criteria : dict
            Dictionary of autopicking criteria.
        min_abort : int, optional
            Total number of colonies that must be detected in the aggregate
            list of `from` wells to avoid aborting the entire run.
        dataref: str
            Name of dataset to save the picked colonies to

        Returns
        -------
        Autopick
            Returns the :py:class:`autoprotocol.instruction.Autopick`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            Invalid input types for sources and dests
        ValueError
            Source wells are not all from the same container

        """
        # Check valid well inputs
        if not is_valid_well(sources):
            raise TypeError(
                "Source must be of type Well, list of Wells, or " "WellGroup."
            )
        if not is_valid_well(dests):
            raise TypeError(
                "Destinations (dests) must be of type Well, "
                "list of Wells, or WellGroup."
            )
        pick = {}

        sources = WellGroup(sources)
        pick["from"] = sources
        if len(set([s.container for s in pick["from"]])) > 1:
            raise ValueError(
                "All source wells for autopick must exist " "on the same container"
            )
        dests = WellGroup(dests)
        pick["to"] = dests
        pick["min_abort"] = min_abort

        group = [pick]

        for s in pick["from"]:
            self._remove_cover(s.container, "autopick")
        for d in pick["to"]:
            self._remove_cover(d.container, "autopick")

        criteria = {} if criteria is None else criteria

        return self._append_and_return(Autopick(group, criteria, dataref))

    def mag_dry(self, head, container, duration, new_tip=False, new_instruction=False):
        """

        Dry beads with magnetized tips above and outside a container for a set
        time.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            plate = p.ref("plate_0", None, "96-pcr", storage="cold_20")

            p.mag_dry("96-pcr", plate, "30:minute", new_tip=False,
                      new_instruction=False)

        Autoprotocol Output:

        .. code-block:: none

            "instructions": [
                {
                  "groups": [
                    [
                      {
                        "dry": {
                          "duration": "30:minute",
                          "object": "plate_0"
                        }
                      }
                    ]
                  ],
                  "magnetic_head": "96-pcr",
                  "op": "magnetic_transfer"
                }
              ]

        Parameters
        ----------
        head : str
            Magnetic head to use for the magnetic bead transfers
        container : Container
            Container to dry beads above
        duration : str or Unit
            Time for drying
        new_tip : bool
            Specify whether to use a new tip to complete the step
        new_instruction: bool
            Specify whether to create a new magnetic_transfer instruction

        Returns
        -------
        MagneticTransfer
            Returns the :py:class:`autoprotocol.instruction.MagneticTransfer`
            instruction created from the specified parameters

        """
        mag = MagneticTransfer.builders.mag_dry(object=container, duration=duration)
        self._remove_cover(container, "mag_dry")
        return self._add_mag(mag, head, new_tip, new_instruction, "dry")

    def mag_incubate(
        self,
        head,
        container,
        duration,
        magnetize=False,
        tip_position=1.5,
        temperature=None,
        new_tip=False,
        new_instruction=False,
    ):
        """

        Incubate the container for a set time with tips set at `tip_position`.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            plate = p.ref("plate_0", None, "96-pcr", storage="cold_20")

            p.mag_incubate("96-pcr", plate, "30:minute", magnetize=False,
                           tip_position=1.5, temperature=None, new_tip=False)

        Autoprotocol Output:

        .. code-block:: none

            "instructions": [
                {
                    "groups": [
                        [
                            {
                                "incubate": {
                                    "duration": "30:minute",
                                    "tip_position": 1.5,
                                    "object": "plate_0",
                                    "magnetize": false,
                                    "temperature": null
                                }
                            }
                        ]
                    ],
                    "magnetic_head": "96-pcr",
                    "op": "magnetic_transfer"
                }
            ]

        Parameters
        ----------
        head : str
            Magnetic head to use for the magnetic bead transfers
        container : Container
            Container to incubate beads
        duration : str or Unit
            Time for incubation
        magnetize : bool
            Specify whether to magnetize the tips
        tip_position : float
            Position relative to well height that tips are held
        temperature: str or Unit, optional
            Temperature heat block is set at
        new_tip : bool
            Specify whether to use a new tip to complete the step
        new_instruction: bool
            Specify whether to create a new magnetic_transfer instruction

        Returns
        -------
        MagneticTransfer
            Returns the :py:class:`autoprotocol.instruction.MagneticTransfer`
            instruction created from the specified parameters

        """
        mag = MagneticTransfer.builders.mag_incubate(
            object=container,
            duration=duration,
            magnetize=magnetize,
            tip_position=tip_position,
            temperature=temperature,
        )
        self._remove_cover(container, "mag_incubate")
        return self._add_mag(mag, head, new_tip, new_instruction, "incubate")

    def mag_collect(
        self,
        head,
        container,
        cycles,
        pause_duration,
        bottom_position=0.0,
        temperature=None,
        new_tip=False,
        new_instruction=False,
    ):
        """

        Collect beads from a container by cycling magnetized tips in and out
        of the container with an optional pause at the bottom of the insertion.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            plate = p.ref("plate_0", None, "96-pcr", storage="cold_20")

            p.mag_collect("96-pcr", plate, 5, "30:second", bottom_position=
                          0.0, temperature=None, new_tip=False,
                          new_instruction=False)

        Autoprotocol Output:

        .. code-block:: none

            "instructions": [
                {
                    "groups": [
                        [
                            {
                                "collect": {
                                    "bottom_position": 0,
                                    "object": "plate_0",
                                    "temperature": null,
                                    "cycles": 5,
                                    "pause_duration": "30:second"
                                }
                            }
                        ]
                    ],
                    "magnetic_head": "96-pcr",
                    "op": "magnetic_transfer"
                }
            ]

        Parameters
        ----------
        head : str
            Magnetic head to use for the magnetic bead transfers
        container : Container
            Container to incubate beads
        cycles: int
            Number of cycles to raise and lower tips
        pause_duration : str or Unit
            Time tips are paused in bottom position each cycle
        bottom_position : float
            Position relative to well height that tips are held during pause
        temperature: str or Unit
            Temperature heat block is set at
        new_tip : bool
            Specify whether to use a new tip to complete the step
        new_instruction: bool
            Specify whether to create a new magnetic_transfer instruction

        Returns
        -------
        MagneticTransfer
            Returns the :py:class:`autoprotocol.instruction.MagneticTransfer`
            instruction created from the specified parameters

        """

        mag = MagneticTransfer.builders.mag_collect(
            object=container,
            cycles=cycles,
            pause_duration=pause_duration,
            bottom_position=bottom_position,
            temperature=temperature,
        )
        self._remove_cover(container, "mag_collect")
        return self._add_mag(mag, head, new_tip, new_instruction, "collect")

    def mag_release(
        self,
        head,
        container,
        duration,
        frequency,
        center=0.5,
        amplitude=0.5,
        temperature=None,
        new_tip=False,
        new_instruction=False,
    ):
        """

        Release beads into a container by cycling tips in and out of the
        container with tips unmagnetized.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            plate = p.ref("plate_0", None, "96-pcr", storage="cold_20")

            p.mag_release("96-pcr", plate, "30:second", "60:hertz", center=0.75,
                          amplitude=0.25, temperature=None, new_tip=False,
                          new_instruction=False)

        Autoprotocol Output:

        .. code-block:: none

            "instructions": [
                {
                    "groups": [
                        [
                            {
                                "release": {
                                    "center": 0.75,
                                    "object": "plate_0",
                                    "frequency": "2:hertz",
                                    "amplitude": 0.25,
                                    "duration": "30:second",
                                    "temperature": null
                                }
                            }
                        ]
                    ],
                    "magnetic_head": "96-pcr",
                    "op": "magnetic_transfer"
                }
            ]

        Parameters
        ----------
        head : str
            Magnetic head to use for the magnetic bead transfers
        container : Container
            Container to incubate beads
        duration : str or Unit
            Total time for this sub-operation
        frequency : str or Unit
            Cycles per second (hertz) that tips are raised and lowered
        center : float
            Position relative to well height where oscillation is centered
        amplitude : float
            Distance relative to well height to oscillate around "center"
        temperature: str or Unit
            Temperature heat block is set at
        new_tip : bool
            Specify whether to use a new tip to complete the step
        new_instruction: bool
            Specify whether to create a new magnetic_transfer instruction

        Returns
        -------
        MagneticTransfer
            Returns the :py:class:`autoprotocol.instruction.MagneticTransfer`
            instruction created from the specified parameters

        """

        mag = MagneticTransfer.builders.mag_release(
            object=container,
            duration=duration,
            frequency=frequency,
            center=center,
            amplitude=amplitude,
            temperature=temperature,
        )
        self._remove_cover(container, "mag_release")
        return self._add_mag(mag, head, new_tip, new_instruction, "release")

    def mag_mix(
        self,
        head,
        container,
        duration,
        frequency,
        center=0.5,
        amplitude=0.5,
        magnetize=False,
        temperature=None,
        new_tip=False,
        new_instruction=False,
    ):
        """

        Mix beads in a container by cycling tips in and out of the
        container.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            plate = p.ref("plate_0", None, "96-pcr", storage="cold_20")

            p.mag_mix("96-pcr", plate, "30:second", "60:hertz", center=0.75,
                      amplitude=0.25, magnetize=True, temperature=None,
                      new_tip=False, new_instruction=False)

        Autoprotocol Output:

        .. code-block:: none

            "instructions": [
                {
                    "groups": [
                        [
                            {
                                "mix": {
                                    "center": 0.75,
                                    "object": "plate_0",
                                    "frequency": "2:hertz",
                                    "amplitude": 0.25,
                                    "duration": "30:second",
                                    "magnetize": true,
                                    "temperature": null
                                }
                            }
                        ]
                    ],
                    "magnetic_head": "96-pcr",
                    "op": "magnetic_transfer"
                }
            ]

        Parameters
        ----------
        head : str
            Magnetic head to use for the magnetic bead transfers
        container : Container
            Container to incubate beads
        duration : str or Unit
            Total time for this sub-operation
        frequency : str or Unit
            Cycles per second (hertz) that tips are raised and lowered
        center : float
            Position relative to well height where oscillation is centered
        amplitude : float
            Distance relative to well height to oscillate around "center"
        magnetize : bool
            Specify whether to magnetize the tips
        temperature: str or Unit
            Temperature heat block is set at
        new_tip : bool
            Specify whether to use a new tip to complete the step
        new_instruction: bool
            Specify whether to create a new magnetic_transfer instruction

        Returns
        -------
        MagneticTransfer
            Returns the :py:class:`autoprotocol.instruction.MagneticTransfer`
            instruction created from the specified parameters

        """

        mag = MagneticTransfer.builders.mag_mix(
            object=container,
            duration=duration,
            frequency=frequency,
            center=center,
            amplitude=amplitude,
            magnetize=magnetize,
            temperature=temperature,
        )
        self._remove_cover(container, "mag_mix")
        return self._add_mag(mag, head, new_tip, new_instruction, "mix")

    def image_plate(self, ref, mode, dataref):

        """
        Capture an image of the specified container.

        Example Usage:

        .. code-block:: python

            p = Protocol()

            agar_plate = p.ref("agar_plate", None, "1-flat", discard=True)
            bact = p.ref("bacteria", None, "micro-1.5", discard=True)

            p.spread(bact.well(0), agar_plate.well(0), "55:microliter")
            p.incubate(agar_plate, "warm_37", "18:hour")
            p.image_plate(agar_plate, mode="top", dataref="my_plate_image_1")


        Autoprotocol Output:

        .. code-block:: json

            {
              "refs": {
                "bacteria": {
                  "new": "micro-1.5",
                  "discard": true
                },
                "agar_plate": {
                  "new": "1-flat",
                  "discard": true
                }
              },
              "instructions": [
                {
                  "volume": "55.0:microliter",
                  "to": "agar_plate/0",
                  "from": "bacteria/0",
                  "op": "spread"
                },
                {
                  "where": "warm_37",
                  "object": "agar_plate",
                  "co2_percent": 0,
                  "duration": "18:hour",
                  "shaking": false,
                  "op": "incubate"
                },
                {
                  "dataref": "my_plate_image_1",
                  "object": "agar_plate",
                  "mode": "top",
                  "op": "image_plate"
                }
              ]
            }


        Parameters
        ----------
        ref : str or Container
            Container to take image of
        mode : str
            Imaging mode (currently supported: "top")
        dataref : str
            Name of data reference of resulting image

        Returns
        -------
        ImagePlate
            Returns the :py:class:`autoprotocol.instruction.ImagePlate`
            instruction created from the specified parameters

        """
        return self._append_and_return(ImagePlate(ref, mode, dataref))

    def provision(self, resource_id, dests, amounts=None, volumes=None):
        """
        Provision a commercial resource from a catalog into the specified
        destination well(s).  A new tip is used for each destination well
        specified to avoid contamination.

        Parameters
        ----------
        resource_id : str
          Resource ID from catalog.
        dests : Well or WellGroup or list(Well)
          Destination(s) for specified resource.
        amounts : str or Unit or list(str) or list(Unit)
          Volume(s) or Mass(es) to transfer of the resource to each destination well.  If
          one volume or mass is specified, each destination well receive that volume or mass of
          the resource.  If destinations should receive different volume or mass, each
          one should be specified explicitly in a list matching the order of the
          specified destinations.
          Note:  Volumes and amounts arguments are mutually exclusive. Only one is required
        volumes : str or Unit or list(str) or list(Unit)
          Volume to transfer of the resource to each destination well.  If
          one volume is specified, each destination well receive that volume of the resource.
          If destinations should receive different volumes, each
          one should be specified explicitly in a list matching the order of the
          specified destinations.
          Note:  Volumes and amounts arguments are mutually exclusive. Only one is required

        Raises
        ------
        TypeError
            If resource_id is not a string.
        TypeError
            If the unit provided is not supported
        TypeError
            If volume or mass is not specified as a string or Unit (or a list of either)
        RuntimeError
            If length of the list of volumes or masses specified does not match the number
            of destination wells specified.
        ValueError
            If the resource measurement mode is volume and the provision exceeds max capacity of well.
        ValueError
            If the provisioning of volumes or amounts are not supported.

        Returns
        -------
        list(Provision)
            :py:class:`autoprotocol.instruction.Provision` instruction object(s) to be appended and returned

        """

        # Check valid well inputs
        if not is_valid_well(dests):
            raise TypeError(
                "Destinations (dests) must be of type Well, "
                "list of Wells, or WellGroup."
            )
        dests = WellGroup(dests)

        if not isinstance(resource_id, str):
            raise TypeError("Resource ID must be a string.")

        if (volumes is None and amounts is None) or (volumes and amounts):
            raise ValueError(
                "Either volumes or amounts should have value(s), but not both."
            )

        if volumes:
            provision_amounts = volumes
        else:
            provision_amounts = amounts

        if not isinstance(provision_amounts, list):
            provision_amounts = [Unit(provision_amounts)] * len(dests)
        else:
            if len(provision_amounts) != len(dests):
                raise RuntimeError(
                    "To provision a resource into multiple "
                    "destinations with multiple volumes or masses, the  "
                    "list of volumes or masses must correspond with the "
                    "destinations in length and in order."
                )
            provision_amounts = [
                parse_unit(v, ["liter", "gram"]) for v in provision_amounts
            ]

        measurement_mode = self._identify_provision_mode(provision_amounts)

        provision_instructions_to_return: Provision = []
        for d, amount in zip(dests, provision_amounts):
            if d.container.is_covered() or d.container.is_sealed():
                self._remove_cover(d.container, "provision")

            xfer = {"well": d, measurement_mode: amount}

            if measurement_mode == "volume":
                d_max_vol = d.container.container_type.true_max_vol_ul
                if amount > d_max_vol:
                    raise ValueError(
                        f"The volume you are trying to provision ({amount}) exceeds the "
                        f"maximum capacity of this well ({d_max_vol})."
                    )
                if amount > Unit(900, "microliter"):
                    diff = amount - Unit(900, "microliter")
                    provision_instructions_to_return.append(
                        self.provision(resource_id, d, Unit(900, "microliter"))
                    )
                    while diff > Unit(0.0, "microliter"):
                        provision_instructions_to_return.append(
                            self.provision(resource_id, d, diff)
                        )
                        diff -= diff
                    continue

                if d.volume:
                    d.volume += amount
                else:
                    d.set_volume(amount)

            dest_group = [xfer]

            if (
                self.instructions
                and self.instructions[-1].op == "provision"
                and self.instructions[-1].resource_id == resource_id
                and self.instructions[-1].to[-1]["well"].container == d.container
            ):
                self.instructions[-1].to.append(xfer)
            else:
                provision_instructions_to_return.append(
                    self._append_and_return(
                        Provision(resource_id, dest_group, measurement_mode)
                    )
                )
        return provision_instructions_to_return

    def _identify_provision_mode(self, provision_amounts):
        unique_measure_modes = set()
        for amount in provision_amounts:
            if not isinstance(amount, Unit):
                raise TypeError(f"Provided amount {amount} is not supported.")
            if amount.dimensionality == Unit(1, "liter").dimensionality:
                unique_measure_modes.add("volume")
            elif amount.dimensionality == Unit(1, "gram").dimensionality:
                unique_measure_modes.add("mass")
            else:
                raise ValueError(
                    f"Provisioning of resources with measurement unit of {amount.unit} is not supported."
                )
        if len(unique_measure_modes) != 1:
            raise ValueError("Received amounts with more than one measurement mode")
        measurement_mode = unique_measure_modes.pop()
        return measurement_mode

    def flash_freeze(self, container, duration):
        """
        Flash freeze the contents of the specified container by submerging it
        in liquid nitrogen for the specified amount of time.

        Example Usage:

        .. code-block:: python

            p = Protocol()

            sample = p.ref("liquid_sample", None, "micro-1.5", discard=True)
            p.flash_freeze(sample, "25:second")


        Autoprotocol Output:

        .. code-block:: json

            {
              "refs": {
                "liquid_sample": {
                  "new": "micro-1.5",
                  "discard": true
                }
              },
              "instructions": [
                {
                  "duration": "25:second",
                  "object": "liquid_sample",
                  "op": "flash_freeze"
                }
              ]
            }


        Parameters
        ----------
        container : Container or str
          Container to be flash frozen.
        duration : str or Unit
          Duration to submerge specified container in liquid nitrogen.

        Returns
        -------
        FlashFreeze
            Returns the :py:class:`autoprotocol.instruction.FlashFreeze`
            instruction created from the specified parameters
        """

        return self._append_and_return(FlashFreeze(container, duration))

    def sonicate(
        self, wells, duration, mode, mode_params, frequency=None, temperature=None
    ):
        """
        Sonicate wells using high intensity ultrasonic vibrations.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            sample_wells = p.ref("sample_plate",
                                 None,
                                 "96-pcr",
                                 storage="warm_37").wells_from(0,2)

            p.sonicate(sample_wells, duration="1:minute",
                       mode="bath",
                       mode_params={"sample_holder": "suspender"})

        Autoprotocol Output:

        .. code-block:: json

            {
                "op": "sonicate",
                "wells": ["sample_plate/0", "sample_plate/1"],
                "mode": "bath",
                "duration": "1:minute",
                "temperature": "ambient",
                "frequency": "40:kilohertz"
                "mode_params": {
                    "sample_holder": "suspender"
                }
            }

        Parameters
        ----------
        wells : Well or WellGroup or list(Well)
           Wells to be sonicated
        duration : Unit or str
            Duration for which to sonicate wells
        mode: Enum({"bath", "horn"})
            Sonicating method to be used, must be "horn" or "bath". Sonicate
            mode "horn" uses metal probe to create a localized shear force
            directly in the sample media; "bath" mode applies ultrasound to
            wells held inside a bath.
        temperature: Unit or str, optional
            Temperature at which the sample is kept during sonication. Optional,
            defaults to ambient
        frequency: Unit or str, optional
            Frequency of the ultrasonic wave, usually indicated in kHz.
            Optional; defaults to the most commonly used frequency for each
            mode: 20 kHz for `horn`, and 40 kHz for `bath` mode
        mode_params: Dict
            Dictionary containing mode parameters for the specified mode.

            .. code-block:: none

                {
                    "mode": "bath",
                    "mode_params":
                        {
                            "sample_holder": Enum({"suspender",
                                                   "perforated_container",
                                                   "solid_container"})
                            "power": Unit or str, optional
                        }
                }
                - or -
                {
                    "mode": "horn",
                    "mode_params":
                        {
                            "duty_cycle": Float, 0 < value <=1
                            "amplitude": Unit or str
                        }
                }


        Returns
        -------
        Sonicate
            Returns the :py:class:`autoprotocol.instruction.Sonicate`
            instruction created from the specified parameters

        Raises
        ------
        RuntimeError
            If valid mode is not specified.
        TypeError
            If wells not of type WellGroup or List of Wells.
        ValueError
            If invalid `mode_params` for specified mode.
        TypeError
            If invalid `mode_params` type for specified mode.

        """
        sonic_modes = ["bath", "horn"]
        if mode not in sonic_modes:
            raise RuntimeError(f"{mode} is not a valid sonication mode")
        if not isinstance(mode_params, dict):
            raise TypeError(f"Invalid mode_params {mode_params}, must be a dict")

        parsed_mode_params = {}
        if mode == "bath":
            valid_sample_holders = [
                "suspender",
                "perforated_container",
                "solid_container",
            ]
            valid_mode_params = ["sample_holder", "power"]
            sample_holder = mode_params.get("sample_holder")
            if sample_holder not in valid_sample_holders:
                raise ValueError(
                    f"'sample_holder' must be specified in 'mode_params' mode: "
                    f"{mode} and must be one of {valid_sample_holders}."
                )
            parsed_mode_params["sample_holder"] = sample_holder
            power = mode_params.get("power")
            if power:
                parsed_power = parse_unit(power, "power-watt")
                parsed_mode_params["power"] = parsed_power
            frequency = frequency or "40:kilohertz"
        if mode == "horn":
            valid_mode_params = ["duty_cycle", "amplitude"]
            if not all(k in mode_params for k in valid_mode_params):
                raise ValueError(
                    f"Incorrect mode_params.  All of "
                    f"{valid_mode_params} must be included in "
                    f"mode: {mode}"
                )
            duty_cycle = mode_params["duty_cycle"]
            amplitude = mode_params["amplitude"]
            if not isinstance(duty_cycle, (int, float)):
                raise TypeError(f"Invalid duty_cycle {duty_cycle}, must be a decimal")
            duty_cycle = float(duty_cycle)
            if not 0 <= duty_cycle <= 1:
                raise ValueError(
                    f"Invalid duty_cycle {duty_cycle}, must be between 0 and "
                    f"1 (inclusive)."
                )
            parsed_mode_params["duty_cycle"] = duty_cycle
            parsed_amplitude = parse_unit(amplitude, "micrometer")
            parsed_mode_params["amplitude"] = parsed_amplitude
            frequency = frequency or "20:kilohertz"
        if not is_valid_well(wells):
            raise TypeError("Wells must be of type Well, list of Wells, or WellGroup.")
        wells = WellGroup(wells)
        parsed_duration = parse_unit(duration, "seconds")
        parsed_frequency = parse_unit(frequency, "hertz")
        if temperature:
            parsed_temperature = parse_unit(temperature, "celsius")
        else:
            parsed_temperature = None
        return self._append_and_return(
            Sonicate(
                wells,
                parsed_duration,
                mode,
                parsed_mode_params,
                parsed_frequency,
                parsed_temperature,
            )
        )

    def spe(
        self,
        well,
        cartridge,
        pressure_mode,
        load_sample,
        elute,
        condition=None,
        equilibrate=None,
        rinse=None,
    ):
        """
        Apply a solid phase extraction (spe) technique to a sample.

        Example Usage:

        .. code-block:: python

            p = Protocol()

            elute_params = [
                SPE.builders.mobile_phase_params(
                    is_elute=True,
                    volume="2:microliter",
                    loading_flowrate="100:ul/second",
                    settle_time="2:minute",
                    processing_time="3:minute",
                    flow_pressure="2:bar",
                    resource_id="solvent_a",
                    destination_well=p.ref("Elute %s" % i, None,
                                           "micro-1.5",
                                           discard=True).well(0))
                for i in range(3)
            ]

            sample_loading_params = SPE.builders.mobile_phase_params(
                volume="10:microliter", loading_flowrate="1:ul/second",
                settle_time="2:minute", processing_time="3:minute",
                flow_pressure="2:bar", is_sample=True)

            cartridge = "spe_cartridge"
            sample = p.ref("Sample", None, "micro-1.5", discard=True).well(0)

            p.spe(sample, cartridge, "positive",
                  load_sample=sample_loading_params, elute=elute_params)

        Autoprotocol Output:

        .. code-block:: none

          "instructions": [
                {
                  "op": "spe",
                  "elute": [
                    {
                      "loading_flowrate": "100:microliter/second",
                      "resource_id": "solvent_a",
                      "settle_time": "2:minute",
                      "volume": "2:microliter",
                      "flow_pressure": "2:bar",
                      "destination_well": "Elute 0/0",
                      "processing_time": "3:minute"
                    },
                    {
                      "loading_flowrate": "100:microliter/second",
                      "resource_id": "solvent_a",
                      "settle_time": "2:minute",
                      "volume": "2:microliter",
                      "flow_pressure": "2:bar",
                      "destination_well": "Elute 1/0",
                      "processing_time": "3:minute"
                    },
                    {
                      "loading_flowrate": "100:microliter/second",
                      "resource_id": "solvent_a",
                      "settle_time": "2:minute",
                      "volume": "2:microliter",
                      "flow_pressure": "2:bar",
                      "destination_well": "Elute 2/0",
                      "processing_time": "3:minute"
                    }
                  ],
                  "cartridge": "spe_cartridge",
                  "well": "Sample/0",
                  "load_sample": {
                    "flow_pressure": "2:bar",
                    "loading_flowrate": "1:microliter/second",
                    "settle_time": "2:minute",
                    "processing_time": "3:minute",
                    "volume": "10:microliter"
                  },
                  "pressure_mode": "positive"
                }
              ]

        Parameters
        ----------
        well : Well
            Well to solid phase extract.
        cartridge : str
            Cartridge to use for solid phase extraction.
        pressure_mode : str
            The direction of pressure applied to the cartridge to force
            liquid flow. One of "positive", "negative".
        load_sample: dict
            Parameters for applying the sample to the cartridge.
            Single 'mobile_phase_param'.
        elute: list(dict)
            Parameters for applying a mobile phase to the cartridge
            with one or more solvents. List of 'mobile_phase_params'.
            Requires `destination_well`.
        condition: list(dict), optional
            Parameters for applying a mobile phase to the cartridge
            with one or more solvents. List of 'mobile_phase_params'.
        equilibrate: list(dict), optional
            Parameters for applying a mobile phase to the cartridge
            with one or more solvents. List of 'mobile_phase_params'.
        rinse: list(dict), optional
            Parameters for applying a mobile phase to the cartridge
            with one or more solvents. List of 'mobile_phase_params'.

            mobile_phase_params:
                resource_id: str
                    Resource ID of desired solvent.
                volume: volume
                    Volume added to the cartridge.
                loading_flowrate: Unit
                    Speed at which volume is added to cartridge.
                settle_time: Unit
                    Duration for which the solvent remains on the cartridge
                    before a pressure mode is applied.
                processing_time: Unit
                    Duration for which pressure is applied to the cartridge
                    after `settle_time` has elapsed.
                flow_pressure: Unit
                    Pressure applied to the column.
                destination_well: Well
                    Destination well for eluate.  Required parameter for
                    each `elute` mobile phase parameter

        Returns
        -------
        SPE
            Returns the :py:class:`autoprotocol.instruction.SPE`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            Invalid input types, e.g. well given is not of type Well
        ValueError
            Wells specified are not from the same container
        ValueError
            Invalid pressure_mode
        ValueError
            settle_time, processing_time, flow_pressure not greater than 0
        ValueError
            If not exactly one elution parameter for each elution container
        UnitError
            Improperly formatted units for mobile phase parameters

        """
        if not is_valid_well(well):
            raise TypeError("Well must be of type Well.")
        if not isinstance(cartridge, str):
            raise TypeError("Cartrige must be of type string.")
        valid_pressure_modes = ["positive", "negative"]
        if pressure_mode not in valid_pressure_modes:
            raise ValueError(
                f"'pressure_mode': {pressure_mode} has to be one "
                f"of {valid_pressure_modes}"
            )
        load_sample = SPE.builders.mobile_phase_params(is_sample=True, **load_sample)
        SPE.builders.spe_params(elute, is_elute=True)
        if condition:
            SPE.builders.spe_params(condition)
        if equilibrate:
            SPE.builders.spe_params(equilibrate)
        if rinse:
            SPE.builders.spe_params(rinse)

        return self._append_and_return(
            SPE(
                well,
                cartridge,
                pressure_mode,
                load_sample,
                elute,
                condition,
                equilibrate,
                rinse,
            )
        )

    def image(
        self,
        ref,
        mode,
        dataref,
        num_images=1,
        backlighting=None,
        exposure=None,
        magnification=1.0,
    ):
        """
        Capture an image of the specified container.

                Example Usage:

                .. code-block:: python

                    p = Protocol()

                    sample = p.ref("Sample", None, "micro-1.5", discard=True)
                    p.image(sample, "top", "image_1", num_images=3,
                            backlighting=False, exposure={"iso": 4},
                            magnification=1.0)


                Autoprotocol Output:

                .. code-block:: json

                    {
                      "refs": {
                        "Sample": {
                          "new": "micro-1.5",
                          "discard": true
                        }
                      },
                      "instructions": [
                        {
                          "magnification": 1.0,
                          "backlighting": false,
                          "mode": "top",
                          "dataref": "image_1",
                          "object": "Sample",
                          "num_images": 3,
                          "op": "image",
                          "exposure": {
                            "iso": 4
                          }
                        }
                      ]
                    }


        Parameters
        ----------
        ref : Container
            Container of which to take image.
        mode : Enum("top", "bottom", "side")
            Angle of image.
        num_images : int
            Number of images taken of the container. Defaults to 1.
        dataref : str
            Name of data reference of resulting image
        backlighting : Bool, optional
            Whether back-lighting is desired.
        magnification : float
            Ratio of sizes of the image projected on the camera
            sensor compared to the actual size of the object
            captured. Defaults to 1.0.
        exposure : dict, optional
            Parameters to control exposure: "aperture", "iso",
            and "shutter_speed".

            shutter_speed: Unit, optional
                Duration that the imaging sensor is exposed.
            iso : Float, optional
                Light sensitivity of the imaging sensor.
            aperture: Float, optional
                Diameter of the lens opening.


        Returns
        -------
        Image
            Returns the :py:class:`autoprotocol.instruction.Image`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            Invalid input types, e.g. num_images is not a positive integer
        ValueError
            Invalid exposure parameter supplied
        """
        valid_image_modes = ["top", "bottom", "side"]
        if not isinstance(ref, Container):
            raise TypeError(f"image ref: {ref} has to be of type Container")
        if mode not in valid_image_modes:
            raise ValueError(
                f"specified mode: {mode} must be one of " f"{valid_image_modes}"
            )
        if not isinstance(dataref, str):
            raise TypeError("dataref must be of type String.")
        if not isinstance(num_images, int) or num_images <= 0:
            raise TypeError("num_images must be a positive integer.")
        if magnification:
            if not isinstance(magnification, (float, int)) or magnification <= 0:
                raise TypeError("magnification must be a number.")
        if backlighting:
            if not isinstance(backlighting, bool):
                raise TypeError("backlighting must be a boolean.")
        if exposure:
            valid_exposure_params = ["shutter_speed", "iso", "aperture"]
            if not isinstance(exposure, dict):
                raise TypeError(
                    f"exposure must be a dict with optional keys: "
                    f"{valid_exposure_params}."
                )
            if not all(k in valid_exposure_params for k in exposure):
                raise ValueError(
                    f"Invalid exposure param.  Valid params: "
                    f"{valid_exposure_params}."
                )
            shutter_speed = exposure.get("shutter_speed")
            if shutter_speed:
                shutter_speed = parse_unit(shutter_speed, "millimeter/s")
            iso = exposure.get("iso")
            if iso:
                if not isinstance(iso, (float, int)):
                    raise TypeError("iso must be a number.")
            aperture = exposure.get("aperture")
            if aperture:
                if not isinstance(aperture, (float, int)):
                    raise TypeError("aperture must be a number.")

        return self._append_and_return(
            Image(ref, mode, dataref, num_images, backlighting, exposure, magnification)
        )

    def _ref_for_well(self, well):
        return "%s/%d" % (self._ref_for_container(well.container), well.index)

    def _ref_for_container(self, container):
        for k in self.refs:
            v = self.refs[k]
            if v.container is container:
                return k

    def _remove_cover(self, container, action):
        if not container.container_type.is_tube:
            if not (container.is_covered() or container.is_sealed()):
                return
            elif container.cover in COVER_TYPES:
                self.uncover(container)
            elif container.cover in SEAL_TYPES:
                self.unseal(container)
            else:
                raise RuntimeError(
                    f"The operation {action} requires an uncovered container, "
                    f"however, {container.cover} is not a recognized cover or "
                    f"seal type."
                )

    def _add_cover(self, container, action):
        if not container.container_type.is_tube:
            if container.is_covered() or container.is_sealed():
                return
            elif "cover" in container.container_type.capabilities:
                self.cover(container, container.container_type.cover_types[0])
            elif "seal" in container.container_type.capabilities:
                self.seal(container, container.container_type.seal_types[0])
            else:
                raise RuntimeError(
                    f"The operation {action} requires a covered container, "
                    f"however, {container.container_type.name} does not have "
                    f"a recognized cover or seal type."
                )

    def _add_seal(self, container, action):
        if not container.container_type.is_tube:
            if container.is_sealed():
                return
            elif container.is_covered():
                raise RuntimeError(
                    f"The operation {action} requires a sealed container, "
                    f"however, {container.name} currently hasa lid which needs "
                    f"to be first removed."
                )
            if "seal" in container.container_type.capabilities:
                self.seal(container, container.container_type.seal_types[0])
            else:
                raise RuntimeError(
                    f"The operation {action} requires a sealed container, "
                    f"however, {container.container_type.name} does not have "
                    f"a recognized seal type."
                )

    def _add_mag(self, sub_op, head, new_tip, new_instruction, sub_op_name):
        """
        Append given magnetic_transfer groups to protocol
        """
        last_instruction = self.instructions[-1] if self.instructions else None
        maybe_same_instruction = (
            new_instruction is False
            and last_instruction
            and isinstance(last_instruction, MagneticTransfer)
            and last_instruction.data.get("magnetic_head") == head
        )
        # Overwriting __dict__ since that's edited on __init__ and we use it
        # for downstream checks
        if maybe_same_instruction and new_tip is True:
            new_groups = last_instruction.data.get("groups")
            new_groups.append([{sub_op_name: sub_op}])
            last_instruction.__dict__ = MagneticTransfer(
                groups=new_groups, magnetic_head=head
            ).__dict__
            return last_instruction
        elif maybe_same_instruction and new_tip is False:
            new_groups = last_instruction.data.get("groups")
            new_groups[-1].append({sub_op_name: sub_op})
            last_instruction.__dict__ = MagneticTransfer(
                groups=new_groups, magnetic_head=head
            ).__dict__
            return last_instruction
        else:
            return self._append_and_return(
                MagneticTransfer(groups=[[{sub_op_name: sub_op}]], magnetic_head=head)
            )

    # pylint: disable=protected-access
    def _refify(self, op_data):
        """
        Unpacks protocol objects into Autoprotocol compliant ones

        Used by as_dict().

        Parameters
        ----------
        op_data: any protocol object

        Returns
        -------
        dict or str or list or any
            Autoprotocol compliant objects

        """
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
        elif isinstance(op_data, Instruction):
            return self._refify(op_data._as_AST())
        elif isinstance(op_data, Ref):
            return op_data.opts
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

        Returns
        -------
        dict
            Dictionary of containers and wells

        Raises
        ------
        RuntimeError
            Invalid parameters

        """
        parameters = {}
        containers = {}

        # ref containers
        for k, v in params.items():
            if isinstance(v, dict):
                parameters[str(k)] = self._ref_containers_and_wells(v)
            if isinstance(v, list) and isinstance(v[0], dict):
                for cont in v:
                    self._ref_containers_and_wells(cont.encode("utf-8"))
            elif isinstance(v, dict) and "type" in v:
                if "discard" in v:
                    discard = v["discard"]
                    if discard and v.get("storage"):
                        raise RuntimeError(
                            "You must either specify a storage "
                            "condition or set discard to true, "
                            "not both."
                        )
                else:
                    discard = False
                containers[str(k)] = self.ref(
                    k, v["id"], v["type"], storage=v.get("storage"), discard=discard
                )
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

                if ref_name not in self.refs:
                    raise RuntimeError(
                        f"Parameters contain well references to a container that isn't referenced in this protocol: '{ref_name}'."
                    )

                if v.rsplit("/")[1] == "all_wells":
                    parameters[str(k)] = self.refs[ref_name].container.all_wells()
                else:
                    parameters[str(k)] = self.refs[ref_name].container.well(
                        v.rsplit("/")[1]
                    )
            else:
                parameters[str(k)] = v

        return parameters

    def measure_concentration(self, wells, dataref, measurement, volume="2:microliter"):
        """
        Measure the concentration of DNA, ssDNA, RNA or protein in the
        specified volume of the source aliquots.

        Example Usage:

        .. code-block:: python

            p = Protocol()

            test_plate = p.ref("test_plate", id=None, cont_type="96-flat",
                storage=None, discard=True)
            p.measure_concentration(test_plate.wells_from(0, 3), "mc_test",
                "DNA")
            p.measure_concentration(test_plate.wells_from(3, 3),
                dataref="mc_test2", measurement="protein",
                volume="4:microliter")


        Autoprotocol Output:

        .. code-block:: none

            {
                "refs": {
                    "test_plate": {
                        "new": "96-flat",
                        "discard": true
                    }
                },
                "instructions": [
                    {
                        "volume": "2.0:microliter",
                        "dataref": "mc_test",
                        "object": [
                            "test_plate/0",
                            "test_plate/1",
                            "test_plate/2"
                        ],
                        "op": "measure_concentration",
                        "measurement": "DNA"
                    }, ...
                ]
            }


        Parameters
        ----------
        wells : list(Well) or WellGroup or Well
            WellGroup of wells to be measured
        volume : str or Unit
            Volume of sample required for analysis
        dataref : str
            Name of this specific dataset of measurements
        measurement : str
            Class of material to be measured. One of ["DNA", "ssDNA", "RNA",
            "protein"].

        Returns
        -------
        MeasureConcentration
            Returns the
            :py:class:`autoprotocol.instruction.MeasureConcentration`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            `wells` specified is not of a valid input type

        """
        if not is_valid_well(wells):
            raise TypeError("Wells must be of type Well, list of Wells, or WellGroup.")
        wells = WellGroup(wells)
        return self._append_and_return(
            MeasureConcentration(wells, volume, dataref, measurement)
        )

    def measure_mass(self, container, dataref):
        """
        Measure the mass of a container.

        Example Usage:

        .. code-block:: python

            p = Protocol()

            test_plate = p.ref("test_plate", id=None, cont_type="96-flat",
                storage=None, discard=True)
            p.measure_mass(test_plate, "test_data")


        Autoprotocol Output:

        .. code-block:: json

            {
                "refs": {
                    "test_plate": {
                        "new": "96-flat",
                        "discard": true
                    }
                },
                "instructions": [
                    {
                        "dataref": "test_data",
                        "object": [
                            "test_plate"
                        ],
                        "op": "measure_mass"
                    }
                ]
            }


        Parameters
        ----------
        container : Container
            container to be measured
        dataref : str
            Name of this specific dataset of measurements

        Returns
        -------
        MeasureMass
            Returns the :py:class:`autoprotocol.instruction.MeasureMass`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            Input given is not of type Container

        """
        if not isinstance(container, Container):
            raise TypeError(f"{container} has to be of type Container")

        return self._append_and_return(MeasureMass(container, dataref))

    def measure_volume(self, wells, dataref):
        """
        Measure the volume of each well in wells.

        Example Usage:

        .. code-block:: python

            p = Protocol()

            test_plate = p.ref("test_plate", id=None, cont_type="96-flat",
                storage=None, discard=True)
            p.measure_volume(test_plate.from_wells(0,2), "test_data")


        Autoprotocol Output:

        .. code-block:: json

            {
                "refs": {
                    "test_plate": {
                        "new": "96-flat",
                        "discard": true
                    }
                },
                "instructions": [
                    {
                        "dataref": "test_data",
                        "object": [
                            "test_plate/0",
                            "test_plate/1"
                        ],
                        "op": "measure_volume"
                    }
                ]
            }


        Parameters
        ----------
        wells : list(Well) or WellGroup or Well
            list of wells to be measured
        dataref : str
            Name of this specific dataset of measurements

        Returns
        -------
        MeasureVolume
            Returns the :py:class:`autoprotocol.instruction.MeasureVolume`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            `wells` specified is not of a valid input type

        """
        if not is_valid_well(wells):
            raise TypeError("Wells must be of type Well, list of Wells, or WellGroup.")
        wells = WellGroup(wells)
        return self._append_and_return(MeasureVolume(wells, dataref))

    def count_cells(self, wells, volume, dataref, labels=None):
        """
        Count the number of cells in a sample that are positive/negative
        for a given set of labels.

        Example Usage:

        .. code-block:: python

            p = Protocol()

            cell_suspension = p.ref(
                "cells_with_trypan_blue",
                id=None,
                cont_type="micro-1.5",
                discard=True
            )
            p.count_cells(
                cell_suspension.well(0),
                "10:microliter",
                "my_cell_count",
                ["trypan_blue"]
            )


        Autoprotocol Output:

        .. code-block:: json

            {
                "refs": {
                    "cells_with_trypan_blue": {
                        "new": "micro-1.5",
                        "discard": true
                    }
                },
                "instructions": [
                    {
                        "dataref": "my_cell_count",
                        "volume": "10:microliter",
                        "wells": [
                            "cells_with_trypan_blue/0"
                        ],
                        "labels": [
                            "trypan_blue"
                        ],
                        "op": "count_cells"
                    }
                ]
            }


        Parameters
        ----------
        wells: Well or list(Well) or WellGroup
            List of wells that will be used for cell counting.
        volume: Unit
            Volume that should be consumed from each well for the purpose
            of cell counting.
        dataref: str
            Name of dataset that will be returned.
        labels: list(string), optional
            Cells will be scored for presence or absence of each label
            in this list. If staining is required to visualize these labels,
            they must be added before execution of this instruction.

        Returns
        -------
        CountCells
            Returns the :py:class:`autoprotocol.instruction.CountCells`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            `wells` specified is not of a valid input type

        """
        # Check valid well inputs
        if not is_valid_well(wells):
            raise TypeError("Wells must be of type Well, list of Wells, or WellGroup.")
        wells = WellGroup(wells)

        # Parse volume
        parsed_volume = parse_unit(volume, "microliter")

        # Eliminate duplicates from labels
        parsed_labels = list(set(labels))

        return self._append_and_return(
            CountCells(wells, parsed_volume, dataref, parsed_labels)
        )

    def spectrophotometry(
        self,
        dataref,
        obj,
        groups,
        interval=None,
        num_intervals=None,
        temperature=None,
        shake_before=None,
    ):
        """
        Generates an instruction with one or more plate reading steps
        executed on a single plate with the same device. This could be
        executed once, or at a defined interval, across some total duration.


        Example Usage:

        .. code-block:: python

            p = Protocol()
            read_plate = p.ref("read plate", cont_type="96-flat", discard=True)

            groups = Spectrophotometry.builders.groups(
                [
                    Spectrophotometry.builders.group(
                        "absorbance",
                        Spectrophotometry.builders.absorbance_mode_params(
                            wells=read_plate.wells(0, 1),
                            wavelength=["100:nanometer", "200:nanometer"],
                            num_flashes=15,
                            settle_time="1:second"
                        )
                    ),
                    Spectrophotometry.builders.group(
                        "fluorescence",
                        Spectrophotometry.builders.fluorescence_mode_params(
                            wells=read_plate.wells(0, 1),
                            excitation=[
                                Spectrophotometry.builders.wavelength_selection(
                                    ideal="650:nanometer"
                                )
                            ],
                            emission=[
                                Spectrophotometry.builders.wavelength_selection(
                                    shortpass="600:nanometer",
                                    longpass="700:nanometer"
                                )
                            ],
                            num_flashes=15,
                            settle_time="1:second",
                            lag_time="9:second",
                            integration_time="2:second",
                            gain=0.3,
                            read_position="top"
                        )
                    ),
                    Spectrophotometry.builders.group(
                        "luminescence",
                        Spectrophotometry.builders.luminescence_mode_params(
                            wells=read_plate.wells(0, 1),
                            num_flashes=15,
                            settle_time="1:second",
                            integration_time="2:second",
                            gain=0.3
                        )
                    ),
                    Spectrophotometry.builders.group(
                        "shake",
                        Spectrophotometry.builders.shake_mode_params(
                            duration="1:second",
                            frequency="9:hertz",
                            path="ccw_orbital",
                            amplitude="1:mm"
                        )
                    ),
                ]
            )

            shake_before = Spectrophotometry.builders.shake_before(
                duration="10:minute",
                frequency="5:hertz",
                path="ccw_orbital",
                amplitude="1:mm"
            )

            p.spectrophotometry(
                dataref="test data",
                obj=read_plate,
                groups=groups,
                interval="10:minute",
                num_intervals=2,
                temperature="37:celsius",
                shake_before=shake_before
            )


        Autoprotocol Output:

        .. code-block:: json

            {
              "op": "spectrophotometry",
              "dataref": "test data",
              "object": "read plate",
              "groups": [
                {
                  "mode": "absorbance",
                  "mode_params": {
                    "wells": [
                      "read plate/0",
                      "read plate/1"
                    ],
                    "wavelength": [
                      "100:nanometer",
                      "200:nanometer"
                    ],
                    "num_flashes": 15,
                    "settle_time": "1:second"
                  }
                },
                {
                  "mode": "fluorescence",
                  "mode_params": {
                    "wells": [
                      "read plate/0",
                      "read plate/1"
                    ],
                    "excitation": [
                      {
                        "ideal": "650:nanometer"
                      }
                    ],
                    "emission": [
                      {
                        "shortpass": "600:nanometer",
                        "longpass": "700:nanometer"
                      }
                    ],
                    "num_flashes": 15,
                    "settle_time": "1:second",
                    "lag_time": "9:second",
                    "integration_time": "2:second",
                    "gain": 0.3,
                    "read_position": "top"
                  }
                },
                {
                  "mode": "luminescence",
                  "mode_params": {
                    "wells": [
                      "read plate/0",
                      "read plate/1"
                    ],
                    "num_flashes": 15,
                    "settle_time": "1:second",
                    "integration_time": "2:second",
                    "gain": 0.3
                  }
                },
                {
                  "mode": "shake",
                  "mode_params": {
                    "duration": "1:second",
                    "frequency": "9:hertz",
                    "path": "ccw_orbital",
                    "amplitude": "1:millimeter"
                  }
                }
              ],
              "interval": "10:minute",
              "num_intervals": 2,
              "temperature": "37:celsius",
              "shake_before": {
                "duration": "10:minute",
                "frequency": "5:hertz",
                "path": "ccw_orbital",
                "amplitude": "1:millimeter"
              }
            }


        Parameters
        ----------
        dataref : str
            Name of the resultant dataset to be returned.
        obj : Container or str
            Container to be read.
        groups : list
            A list of groups generated by SpectrophotometryBuilders groups
            builders, any of absorbance_mode_params, fluorescence_mode_params,
            luminescence_mode_params, or shake_mode_params.
        interval : Unit or str, optional
            The time between each of the read intervals.
        num_intervals : int, optional
            The number of times that the groups should be executed.
        temperature : Unit or str, optional
            The temperature that the entire instruction should be executed at.
        shake_before : dict, optional
            A dict of params generated by SpectrophotometryBuilders.shake_before
            that dictates how the obj should be incubated with shaking before
            any of the groups are executed.

        Returns
        -------
        Spectrophotometry
            Returns the :py:class:`autoprotocol.instruction.Spectrophotometry`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            Invalid num_intervals specified, must be an int
        ValueError
            No interval specified but shake groups specified with no duration

        """

        groups = Spectrophotometry.builders.groups(groups)

        if interval is not None:
            interval = parse_unit(interval, "seconds")

        if num_intervals and not isinstance(num_intervals, int):
            raise TypeError(f"Invalid num_intervals {num_intervals}, must be an int.")

        if temperature is not None:
            temperature = parse_unit(temperature, "celsius")

        if shake_before is not None:
            shake_before = Spectrophotometry.builders.shake_before(**shake_before)

        shake_groups = [_ for _ in groups if _["mode"] == "shake"]

        any_shake_duration_undefined = any(
            _["mode_params"].get("duration") is None for _ in shake_groups
        )

        if any_shake_duration_undefined and interval is None:
            raise ValueError(
                "If no interval is specified, then every shake group must "
                "include a defined duration."
            )

        return self._append_and_return(
            Spectrophotometry(
                dataref=dataref,
                object=obj,
                groups=groups,
                interval=interval,
                num_intervals=num_intervals,
                temperature=temperature,
                shake_before=shake_before,
            )
        )

    # pylint: disable=protected-access
    def transfer(
        self,
        source,
        destination,
        volume,
        rows=1,
        columns=1,
        source_liquid=LiquidClass,
        destination_liquid=LiquidClass,
        method=Transfer,
        one_tip=False,
        density=None,
        mode=None,
    ):
        """Generates LiquidHandle instructions between wells

        Transfer liquid between specified pairs of source & destination wells.

        Parameters
        ----------
        source : Well or WellGroup or list(Well)
            Well(s) to transfer liquid from.
        destination : Well or WellGroup or list(Well)
            Well(s) to transfer liquid to.
        volume : str or Unit or list(str) or list(Unit)
            Volume(s) of liquid to be transferred from source wells to
            destination wells. The number of volumes specified must
            correspond to the number of destination wells.
        rows : int, optional
            Number of rows to be concurrently transferred
        columns : int, optional
            Number of columns to be concurrently transferred
        source_liquid : LiquidClass or list(LiquidClass), optional
            Type(s) of liquid contained in the source Well. This affects the
            aspirate and dispense behavior including the flowrates,
            liquid level detection thresholds, and physical movements.
        destination_liquid : LiquidClass or list(LiquidClass), optional
            Type(s) of liquid contained in the destination Well. This affects
            liquid level detection thresholds.
        method : Transfer or list(Transfer), optional
            Integrates with the specified source_liquid and destination_liquid
            to define a set of physical movements.
        one_tip : bool, optional
            If True then a single tip will be used for all operations
        density : Unit or str, optional
            Density of the liquid to be aspirated/dispensed
        mode : str, optional
            The liquid handling mode

        Returns
        -------
        list(LiquidHandle)
            Returns a list of :py:class:`autoprotocol.instruction.LiquidHandle`
            instructions created from the specified parameters

        Raises
        ------
        ValueError
            if the specified parameters can't be interpreted as lists of
            equal length
        ValueError
            if one_tip is true, but not all transfer methods have a tip_type

        Examples
        --------
        Transfer between two single wells

        .. code-block:: python

            from autoprotocol import Protocol, Unit

            p = Protocol()
            source = p.ref("source", cont_type="384-flat", discard=True)
            destination = p.ref(
                "destination", cont_type="394-pcr", discard=True
            )
            p.transfer(source.well(0), destination.well(1), "5:ul")

        Sequential transfers between two groups of wells

        .. code-block:: python

            sources = source.wells_from(0, 8, columnwise=True)
            dests = destination.wells_from(1, 8, columnwise=True)
            volumes = [Unit(x, "ul") for x in range(1, 9)]
            p.transfer(sources, dests, volumes)

        Concurrent transfers between two groups of wells

        .. code-block:: python

            # single-column concurrent transfer
            p.transfer(
                source.well(0), destination.well(1), "5:ul", rows=8
            )

            # 96-well concurrent transfer from the A1 to B2 quadrants
            p.transfer(
                source.well(0), destination.well(13), "5:ul", rows=8, columns=12
            )

            # 384-well concurrent transfer
            p.transfer(
                source.well(0), destination.well(0), "5:ul", rows=16, columns=24
            )

        Transfer with extra parameters

        .. code-block:: python

            from autoprotocol.liquid_handle import Transfer
            from autoprotocol.instruction import LiquidHandle

            p.transfer(
                source.well(0), destination.well(0), "5:ul",
                method=Transfer(
                    mix_before=True,
                    dispense_z=LiquidHandle.builders.position_z(
                       reference="well_top"
                    )
                )
            )

        Transfer using other built in Transfer methods

        .. code-block:: python

            from autoprotocol.liquid_handle import DryWellTransfer

            p.transfer(
                source.well(0), destination.well(1), "5:ul",
                method=DryWellTransfer
            )

        For examples of other more complicated behavior, see the
        documentation for LiquidHandleMethod.

        See Also
        --------
        Transfer : base LiquidHandleMethod for transfer operations
        """

        def location_helper(source, destination, volume, method, density):
            """Generates LiquidHandle transfer locations

            Parameters
            ----------
            source : Well
                Well to transfer liquid from.
            destination : Well
                Well to transfer liquid to.
            volume : Unit
                The volume of liquid to be transferred from source well to
                destination well.
            method : Transfer
                Integrates the two input liquid classes and defines a set of
                transfers based on their attributes and methods.
            density : Unit
                The density of liquid to be aspirated/dispensed.

            Returns
            -------
            list(dict)
                LiquidHandle locations
            """
            self._remove_cover(source.container, "liquid_handle from")
            self._remove_cover(destination.container, "liquid_handle into")
            self._transfer_volume(source, destination, volume, method._shape)

            return [
                LiquidHandle.builders.location(
                    location=source,
                    # pylint: disable=protected-access
                    transports=method._aspirate_transports(volume, density),
                ),
                LiquidHandle.builders.location(
                    location=destination,
                    # pylint: disable=protected-access
                    transports=method._dispense_transports(volume, density),
                ),
            ]

        # validate parameter types
        source = WellGroup(source)
        destination = WellGroup(destination)
        count = max((len(source), len(destination)))

        if len(source) == 1:
            source = WellGroup([source[0]] * count)

        if len(destination) == 1:
            destination = WellGroup([destination[0]] * count)

        if not isinstance(volume, list):
            volume = [volume] * count
        volume = [parse_unit(_, "uL") for _ in volume]

        if density:
            if not isinstance(density, list):
                density = [density] * count
            elif len(density) != count:
                raise ValueError(
                    f"the length of provided density: {len(density)} does not match the number of transports."
                )
            density = [parse_unit(d, "mg/ml") for d in density]
            for d in density:
                if d.magnitude <= 0:
                    raise ValueError(f"Density: {d} must be a value larger than 0.")
        else:
            # if density is None, it should still be a list of None
            density = [density] * count

        if not isinstance(source_liquid, list):
            source_liquid = [source_liquid] * count
        source_liquid = [_validate_as_instance(_, LiquidClass) for _ in source_liquid]

        if not isinstance(destination_liquid, list):
            destination_liquid = [destination_liquid] * count
        destination_liquid = [
            _validate_as_instance(_, LiquidClass) for _ in destination_liquid
        ]

        if not isinstance(method, list):
            method = [method] * count
        method = [_validate_as_instance(_, Transfer) for _ in method]

        # validate parameter counts
        countable_parameters = (
            source,
            destination,
            volume,
            density,
            source_liquid,
            destination_liquid,
            method,
        )
        correct_parameter_counts = all(len(_) == count for _ in countable_parameters)
        if not correct_parameter_counts:
            raise ValueError(
                f"Specified parameters {countable_parameters} could not all be interpreted as the same length {correct_parameter_counts}."
            )

        # format shape
        shape = LiquidHandle.builders.shape(rows, columns, None)

        # validate all containers against the shape
        for aliquot in sum(source, destination):
            container_type = aliquot.container.container_type
            _check_container_type_with_shape(container_type, shape)

        # apply liquid classes to transfer methods
        for src, des, met in zip(source_liquid, destination_liquid, method):
            met._shape = LiquidHandle.builders.shape(**shape)
            met._source_liquid = src
            met._destination_liquid = des

        # apply tip types to transfer methods
        for vol, met in zip(volume, method):
            if met._has_calibration() and not met.tip_type:
                try:
                    met.tip_type = met._rec_tip_type(vol)
                except RuntimeError:
                    met.tip_type = met._get_sorted_tip_types()[-1].name

        # if one tip is true then all methods need to have the same tip_type
        if one_tip is True:
            tip_types = [_.tip_type for _ in method]
            if not all(_ == tip_types[0] for _ in tip_types):
                raise ValueError(
                    f"If one_tip is true and any tip_type is set, then all tip types must be the same but {tip_types} was specified."
                )

        # generate either a LiquidHandle location or instruction list
        locations, instructions = [], []
        for src, des, vol, met, dens in zip(
            source, destination, volume, method, density
        ):
            max_tip_capacity = met._tip_capacity()
            remaining_vol = vol
            while remaining_vol > Unit(0, "ul"):
                transfer_vol = min(remaining_vol, max_tip_capacity)
                if one_tip is True:
                    locations += location_helper(src, des, transfer_vol, met, dens)
                else:
                    location_transports = location_helper(
                        src, des, transfer_vol, met, dens
                    )
                    source_transports = location_transports[0]["transports"]
                    instruction_mode = mode
                    if not instruction_mode:
                        instruction_mode = LiquidHandle.builders.desired_mode(
                            source_transports, mode
                        )
                    instructions.append(
                        LiquidHandle(
                            location_transports,
                            shape=met._shape,
                            mode=instruction_mode,
                            mode_params=(
                                LiquidHandle.builders.instruction_mode_params(
                                    tip_type=met.tip_type
                                )
                            ),
                        )
                    )
                remaining_vol -= transfer_vol

        # if one tip is true then there's a locations list
        if locations:
            source_transports = locations[0]["transports"]
            # if not mode:
            mode = LiquidHandle.builders.desired_mode(source_transports, mode)
            instructions.append(
                LiquidHandle(
                    locations,
                    shape=shape,
                    mode=mode,
                    mode_params=LiquidHandle.builders.instruction_mode_params(
                        tip_type=method[0].tip_type
                    ),
                )
            )
        return self._append_and_return(instructions)

    # pylint: disable=protected-access
    def mix(
        self,
        well,
        volume,
        rows=1,
        columns=1,
        liquid=LiquidClass,
        method=Mix,
        one_tip=False,
        mode=None,
    ):
        """Generates LiquidHandle instructions within wells

        Mix liquid in specified wells.

        Parameters
        ----------
        well : Well or WellGroup or list(Well)
            Well(s) to be mixed.
        volume : str or Unit or list(str) or list(Unit)
            Volume(s) of liquid to be mixed within the specified well(s).
            The number of volume(s) specified must correspond with the number
            of well(s).
        rows : int, optional
            Number of rows to be concurrently mixed
        columns : int, optional
            Number of columns to be concurrently mixed
        liquid : LiquidClass or list(LiquidClass), optional
            Type(s) of liquid contained in the Well(s). This affects the
            aspirate and dispense behavior including the flowrates,
            liquid level detection thresholds, and physical movements.
        method : Mix or list(Mix), optional
            Method(s) with which Integrates with the specified liquid to
            define a set of physical movements.
        one_tip : bool, optional
            If True then a single tip will be used for all operations
        mode : str, optional
            The liquid handling mode

        Returns
        -------
        list(LiquidHandle)
            Returns a list of :py:class:`autoprotocol.instruction.LiquidHandle`
            instructions created from the specified parameters

        Raises
        ------
        ValueError
            if the specified parameters can't be interpreted as lists of
            equal length
        ValueError
            if one_tip is true, but not all mix methods have a tip_type
        ValueError
            if the specified volume is larger than the maximum tip capacity
            of the available liquid_handling devices for a given mix

        Examples
        --------
        Mix within a single well

        .. code-block:: python

            from autoprotocol import Protocol, Unit

            p = Protocol()
            plate = p.ref("example_plate", cont_type="384-flat", discard=True)

            p.mix(plate.well(0), "5:ul")

        Sequential mixes within multiple wells

        .. code-block:: python

            wells = plate.wells_from(0, 8, columnwise=True)
            volumes = [Unit(x, "ul") for x in range(1, 9)]
            p.mix(wells, volumes)


        Concurrent mixes within multiple wells

        .. code-block:: python

            # single-column concurrent mix
            p.mix(plate.well(0), "5:ul", rows=8)

            # 96-well concurrent mix in the A1 quadrant
            p.mix(plate.well(0), "5:ul", rows=8, columns=12)

            # 96-well concurrent mix in the A2 quadrant
            p.mix(plate.well(1), "5:ul", rows=8, columns=12)

            # 384-well concurrent mix
            p.mix(plate.well(0), "5:ul", rows=16, columns=24)

        Mix with extra parameters

        .. code-block:: python

            from autoprotocol.liquid_handle import Mix
            from autoprotocol.instruction import LiquidHandle

            p.mix(
                plate.well(0), "5:ul", rows=8,
                method=Mix(
                    mix_params=LiquidHandle.builders.mix(

                    )
                )
            )

        See Also
        --------
        Mix : base LiquidHandleMethod for mix operations
        """

        def location_helper(aliquot, volume, method):
            """Generates LiquidHandle mix locations

            Parameters
            ----------
            aliquot : Well
                Wells to transfer mix liquid in.
            volume : Unit
                The volume of liquid to be transferred within the aliquot.
            method : Mix
                Integrates the input liquid class and defines a set of
                transfers based on its attributes and methods.

            Returns
            -------
            list(dict)
                LiquidHandle locations
            """
            self._remove_cover(aliquot.container, "liquid_handle in")

            return [
                LiquidHandle.builders.location(
                    location=aliquot, transports=method._mix_transports(volume)
                )
            ]

        # validate parameter types
        well = WellGroup(well)
        count = len(well)

        if not isinstance(volume, list):
            volume = [volume] * count
        volume = [parse_unit(_, "uL") for _ in volume]

        if not isinstance(liquid, list):
            liquid = [liquid] * count
        liquid = [_validate_as_instance(_, LiquidClass) for _ in liquid]

        if not isinstance(method, list):
            method = [method] * count
        method = [_validate_as_instance(_, Mix) for _ in method]

        # validate parameter counts
        countable_parameters = (well, volume, liquid, method)
        correct_parameter_counts = all(len(_) == count for _ in countable_parameters)
        if not correct_parameter_counts:
            raise ValueError(
                f"Specified parameters {countable_parameters} could not all be interpreted as the same length {correct_parameter_counts}."
            )

        # format shape
        shape = LiquidHandle.builders.shape(rows, columns, None)

        # validate all containers against the shape
        for aliquot in well:
            container_type = aliquot.container.container_type
            _check_container_type_with_shape(container_type, shape)

        # apply liquid classes to mix methods
        for liq, met in zip(liquid, method):
            met._shape = LiquidHandle.builders.shape(**shape)
            met._liquid = liq

        # apply tip types to mix methods
        for vol, met in zip(volume, method):
            if met._has_calibration() and not met.tip_type:
                try:
                    met.tip_type = met._rec_tip_type(vol)
                except RuntimeError:
                    met.tip_type = met._get_sorted_tip_types()[-1].name

        # if one tip is true then all methods need to have the same tip_type
        if one_tip is True:
            tip_types = [_.tip_type for _ in method]
            if not all(_ == tip_types[0] for _ in tip_types):
                raise ValueError(
                    f"If one_tip is true and any tip_type is set, then all tip types must be the same but {tip_types} was specified."
                )

        # generate either a LiquidHandle location or instruction list
        locations, instructions = [], []
        for wel, vol, met in zip(well, volume, method):
            max_tip_capacity = met._tip_capacity()

            if vol > max_tip_capacity:
                raise ValueError(
                    f"Attempted mix volume {vol} is larger than the maximum capacity of {max_tip_capacity} for transfer shape {vol.shape}."
                )

            self._remove_cover(wel.container, "liquid_handle mix")
            if one_tip is True:
                locations += location_helper(wel, vol, met)
            else:
                location_transports = location_helper(wel, vol, met)
                source_transports = location_transports[0]["transports"]
                instruction_mode = mode
                if not instruction_mode:
                    instruction_mode = LiquidHandle.builders.desired_mode(
                        source_transports, mode
                    )
                instructions.append(
                    LiquidHandle(
                        location_transports,
                        shape=met._shape,
                        mode=instruction_mode,
                        mode_params=(
                            LiquidHandle.builders.instruction_mode_params(
                                tip_type=met.tip_type
                            )
                        ),
                    )
                )

        # if one tip is true then there's a locations list
        if locations:
            source_transports = locations[0]["transports"]
            if not mode:
                mode = LiquidHandle.builders.desired_mode(source_transports, mode)
            instructions.append(
                LiquidHandle(
                    locations,
                    shape=shape,
                    mode=mode,
                    mode_params=LiquidHandle.builders.instruction_mode_params(
                        tip_type=method[0].tip_type
                    ),
                )
            )
        return self._append_and_return(instructions)

    def spread(
        self,
        source,
        dest,
        volume="50:microliter",
        dispense_speed="20:microliter/second",
    ):
        """
        Spread the specified volume of the source aliquot across the surface of
        the agar contained in the object container.

        Uses a spiral pattern generated by a set of liquid_handle instructions.

        Example Usage:
        .. code-block:: python

            p = Protocol()

            agar_plate = p.ref("agar_plate", None, "1-flat", discard=True)
            bact = p.ref("bacteria", None, "micro-1.5", discard=True)

            p.spread(bact.well(0), agar_plate.well(0), "55:microliter")

        Parameters
        ----------
        source : Well
            Source of material to spread on agar
        dest : Well
            Reference to destination location (plate containing agar)
        volume : str or Unit, optional
            Volume of source material to spread on agar
        dispense_speed : str or Unit, optional
            Speed at which to dispense source aliquot across agar surface

        Returns
        -------
        LiquidHandle
            Returns a :py:class:`autoprotocol.instruction.LiquidHandle`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            If specified source is not of type Well
        TypeError
            If specified destination is not of type Well
        """

        def euclidean_distance(point_a, point_b):
            """
            Calculate the euclidean distance between a pair of xy coordinates

            Parameters
            ----------
            point_a: Iterable
                First point
            point_b: Iterable
                Second point
            Returns
            -------
            float
                The distance between the two points
            """
            from math import sqrt

            x_distance = abs(point_a[0] - point_b[0])
            y_distance = abs(point_a[1] - point_b[1])
            return sqrt(x_distance ** 2 + y_distance ** 2)

        # Check validity of Well inputs
        if not isinstance(source, Well):
            raise TypeError("Source must be of type Well.")
        if not isinstance(dest, Well):
            raise TypeError("Destination, (dest), must be of type Well.")
        self._remove_cover(source.container, "spread")
        self._remove_cover(dest.container, "spread")

        volume = Unit(volume)
        if dest.volume:
            dest.volume += volume
        else:
            dest.volume = volume
        if source.volume:
            source.volume -= volume

        aspirate_transport_list = [
            LiquidHandle.builders.transport(
                mode_params=LiquidHandle.builders.mode_params(
                    position_z=LiquidHandle.builders.position_z(
                        reference="liquid_surface",
                        offset=Unit("-1:mm"),
                        detection_method="capacitance",
                        detection_threshold=AGAR_CLLD_THRESHOLD,
                    )
                )
            ),
            LiquidHandle.builders.transport(
                volume=-volume,
                mode_params=LiquidHandle.builders.mode_params(
                    position_z=LiquidHandle.builders.position_z(
                        reference="liquid_surface",
                        detection_method="tracked",
                        offset=Unit("-1.0:mm"),
                    )
                ),
            ),
        ]

        dispense_transport_list = [
            LiquidHandle.builders.transport(
                mode_params=LiquidHandle.builders.mode_params(
                    position_z=LiquidHandle.builders.position_z(
                        reference="liquid_surface",
                        detection_method="capacitance",
                        detection_threshold=AGAR_CLLD_THRESHOLD,
                    )
                )
            )
        ]

        distances = [
            euclidean_distance(first, second)
            for first, second in zip(SPREAD_PATH, SPREAD_PATH[1:])
        ]
        distance_total = sum(distances)
        distance_ratios = [dist / distance_total for dist in distances]

        for ratio, position in zip(distance_ratios, SPREAD_PATH[1:]):
            dispense_transport_list += [
                LiquidHandle.builders.transport(
                    volume=volume * ratio,
                    flowrate=LiquidHandle.builders.flowrate(dispense_speed),
                    mode_params=LiquidHandle.builders.mode_params(
                        position_x=LiquidHandle.builders.position_xy(position[0]),
                        position_y=LiquidHandle.builders.position_xy(position[1]),
                        position_z=LiquidHandle.builders.position_z(
                            reference="liquid_surface",
                            detection_method="tracked",
                            offset=Unit("0.5:mm"),
                        ),
                    ),
                )
            ]

        location = [
            LiquidHandle.builders.location(
                location=source, transports=aspirate_transport_list
            ),
            LiquidHandle.builders.location(
                location=dest, transports=dispense_transport_list
            ),
        ]

        return self._append_and_return(LiquidHandle(location))

    def _transfer_volume(self, source, destination, volume, shape):
        """
        Transfers volume and properties between aliquots.

        Parameters
        ----------
        source : Well
            The shape origin to be transferred from
        destination : Well
            The shape origin to be transferred to
        volume : Unit
            The volume to be transferred
        shape : dict
            See Also Instruction.builders.shape

        Raises
        ------
        RuntimeError
            If the inferred sources and destinations aren't the same length
        """
        source_wells = source.container.wells_from_shape(source.index, shape)
        dest_wells = destination.container.wells_from_shape(destination.index, shape)
        if not len(source_wells) == len(dest_wells):
            raise RuntimeError(
                f"Transfer source: {source_wells} and destination: "
                f"{dest_wells} WellGroups didn't have the same number of wells."
            )
        for source_well, dest_well in zip(source_wells, dest_wells):
            if self.propagate_properties:
                dest_well.add_properties(source_well.properties)

            if source_well.volume is not None:
                source_well.volume -= volume

            if dest_well.volume is not None:
                dest_well.volume += volume
            else:
                dest_well.volume = volume

    def evaporate(self, ref, mode, duration, evaporator_temperature, mode_params=None):
        """
        Removes liquid or moisture from a container using the mode specified.

        Example Usage:

        .. code-block:: python

            p = Protocol()
            c = p.ref("container", id=None,
                      cont_type="micro-1.5", storage="cold_20")
            blowdown_params = Evaporate.builders.get_mode_params(
                                mode="blowdown", mode_params={
                                    "gas":"nitrogen",
                                    "vortex_speed":Unit("200:rpm"),
                                    "blow_rate": "200:uL/sec"
                                })
            p.evaporate(c,
                        mode="blowdown",
                        duration="10:minute",
                        evaporator_temperature="22:degC",
                        mode_params = blowdown_params

        .. code-block:: json

            {
                "op": "evaporate",
                "ref": "container",
                "mode": "blowdown",
                "duration": "10:minute",
                "evaporator_temperature": "22:degC",
                "mode_params": {
                    "gas": "ntirogen",
                    "vortex_speed": "200:rpm",
                    "blow_rate": "200:uL/sec"
                }
            }

        Parameters
        ----------
        ref : Container
            Sample container
        mode : Str
            The mode of evaporation method
        duration : Unit or Str
            The length of time the sample is evaporated for
        evaporator_temperature : Unit or str
            The incubation temperature of the sample being evaporated
        mode_params : Dict
            Dictionary of parameters for evaporation mode

        Returns
        -------
        Evaporate
            Returns a :py:class:`autoprotocol.instruction.Evaporate`
            instruction created from the specified parameters

        Raises
        ------
        TypeError
            If the provided object is not a Container type.
        ValueError
            If the duration is less than 0 minute
        TypeError
            If evaporator_temperature is not provided in Unit or str
        ValueError
            If the evaporation_temperature is lower than or equal to
            condenser_temperature
        """

        duration = parse_unit(duration, "minute")
        evaporator_temperature = parse_unit(evaporator_temperature, "celsius")
        mode_params = Evaporate.builders.get_mode_params(mode, mode_params)
        if not isinstance(ref, Container):
            raise TypeError("Param `ref` must be a container object.")

        if duration <= Unit("0:minute"):
            raise ValueError(
                f"Param `duration`: {duration} should be longer than 0 minute."
            )

        if mode_params:
            condenser_temp = mode_params.get("condenser_temperature")
            if "condenser_temperature" in mode_params.keys():
                if condenser_temp >= evaporator_temperature:
                    raise ValueError(
                        f"Param `condenser_temperature`: {condenser_temp} "
                        "cannot be higher than the evaporator_temperature:"
                        f" {evaporator_temperature}"
                    )

        return self._append_and_return(
            Evaporate(
                ref=ref,
                duration=duration,
                evaporator_temperature=evaporator_temperature,
                mode=mode,
                mode_params=mode_params,
            )
        )
