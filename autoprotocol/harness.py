"""
Module containing the harness module which helps with Manifest interpretation

    :copyright: 2021 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""

import argparse
import io
import json

from . import UserError
from .compound import Compound, CompoundError
from .container import WellGroup
from .protocol import Protocol
from .unit import Unit, UnitError


_DYE_TEST_RS = {"dye4000": "rs18qmhr7t9jwq", "water": "rs17gmh5wafm5p"}


def get_protocol_preview(protocol, name, manifest="manifest.json"):
    """
    Parses the 'preview' section of a manifest to use as protocol inputs

        Example Usage:

        .. code-block:: python

          p = Protocol()
          preview = get_protocol_preview(p, name="qPCR")

        Output:

        .. code-block:: python
        {
            "qPCR_input1": "value",
            "qPCR_input2": "value2",
            "qPCR_group": {
                "group_entry1": "value",
                "group_entry2": "value"
            }
        }


    Parameters
    ----------
    protocol : Protocol
        Protocol object being parsed.
    name : str
        Name of protocol in manifest to get preview for
    manifest : str, optional
        Name of manifest file

    Returns
    -------
    dict
        Dictionary of parameters used as a Protocol input

    Raises
    ------
    RuntimeError
        No manifest.json file present in directory
    RuntimeError
        Protocol not found in manifest
    RuntimeError
        More than one protocol found in manifest

    """
    try:
        manifest_json = io.open(manifest, encoding="utf-8").read()
    except IOError:
        raise RuntimeError(f"'{manifest}' file not found in directory.")
    manifest = Manifest(json.loads(manifest_json))

    source = [m for m in manifest.protocols if m["name"] == name]
    if not source:
        raise RuntimeError(
            f"Protocol '{name}' not found in list of protocols in this " f"manifest."
        )
    if len(source) != 1:
        raise RuntimeError(
            f"More than one protocol with name '{name}' was found in the "
            f"manifest. All protocol names in a manifest must be unique for it "
            f"to be valid."
        )
    preview = source[0]["preview"]
    run_params = manifest.protocol_info(name).parse(protocol, preview)

    return run_params


def param_default(type_desc):
    if isinstance(type_desc, str):
        type_desc = {"type": type_desc}

    type = type_desc["type"]  # pylint: disable=redefined-builtin
    default = type_desc.get("default")

    if default is not None and type != "group-choice":
        return default

    if type_desc["type"] in ["aliquot+", "aliquot++", "container+"]:
        return []
    elif type_desc["type"] == "group+":
        return [{}]
    elif type_desc["type"] == "group":
        return {k: param_default(v) for k, v in type_desc["inputs"].items()}
    elif type_desc["type"] == "group-choice":
        default_inputs = {}
        for option in type_desc.get("options", []):
            value = option.get("value")
            inputs = option.get("inputs")
            if inputs:
                group_typedesc = {"type": "group", "inputs": inputs}
                default_inputs[value] = param_default(group_typedesc)

        return {"value": default, "inputs": default_inputs}
    elif type_desc["type"] == "csv-table":
        return [{}, [{}]]
    else:
        return None


def convert_param(protocol, val, type_desc):
    """
    Convert parameters based on their input types

    Parameters
    ----------
    protocol : Protocol
        Protocol object being parsed.
    val : str or int or bool or dict or list
        Parameter value to be converted.
    type_desc : dict or str
        Description of input type.

    Returns
    -------
    list or dict or Unit or int or str or float or bool or None
        Converted parameter of the relevant type

    Raises
    ------
    RuntimeError
        Invalid aliquot reference provided for aliquot, aliquot+, aliquot++
    RuntimeError
        Invalid container reference provided for container, container+
    RuntimeError
        Invalid unit-type provided
    RuntimeError
        Invalid temperature condition provided
    RuntimeError
        Invalid format provided for integer or decimal
    RuntimeError
        Invalid value or format provided for group or group+
    RuntimeError
        Invalid format provided for thermocycle or thermocycle_step
    RuntimeError
        Invalid format provided for csv input
    ValueError
        Unknown input type provided

    """
    if isinstance(type_desc, str):
        type_desc = {"type": type_desc}
    if val is None:
        val = param_default(type_desc)
    if val is None:  # still None?
        return None
    type = type_desc["type"]  # pylint: disable=redefined-builtin

    if type == "aliquot":
        try:
            container = ("/").join(val.split("/")[0:-1])
            well_idx = val.split("/")[-1]
            return protocol.refs[container].container.well(well_idx)
        except (KeyError, AttributeError, ValueError):
            label = type_desc.get("label") or "[unknown]"
            raise RuntimeError(
                f"'{val}' (supplied to input '{label}') is not "
                f"a valid reference to an aliquot"
            )
    elif type == "aliquot+":
        try:
            return WellGroup([convert_param(protocol, a, "aliquot") for a in val])
        except:
            label = type_desc.get("label") or "[unknown]"
            raise RuntimeError(
                f"The value supplied to input '{label}' (type aliquot+) is "
                f"improperly formatted."
            )
    elif type == "aliquot++":
        try:
            return [convert_param(protocol, aqs, "aliquot+") for aqs in val]
        except:
            label = type_desc.get("label") or "[unknown]"
            raise RuntimeError(
                f"The value supplied to input '{label}' (type aliquot++) is "
                f"improperly formatted."
            )
    elif type == "compound":
        try:
            return Compound(val["format"], val["value"])
        except CompoundError as e:
            raise RuntimeError(f"Invalid Compound; Details: {e.value}")
    elif type == "compound+":
        try:
            return [convert_param(protocol, cont, "compound") for cont in val]
        except:
            label = type_desc.get("label") or "[unknown]"
            raise RuntimeError(
                f"The value supplied to input '{label}' (type compound+) is "
                f"improperly formatted."
            )
    elif type == "container":

        try:
            return protocol.refs[val].container
        except KeyError:
            label = type_desc.get("label") or "[unknown]"
            raise RuntimeError(
                f"'{val}' (supplied to input '{label}') is not "
                f"a valid reference to a container"
            )
    elif type == "container+":
        try:
            return [convert_param(protocol, cont, "container") for cont in val]
        except:
            label = type_desc.get("label") or "[unknown]"
            raise RuntimeError(
                f"The value supplied to input '{label}' (type container+) is "
                f"improperly formatted."
            )
    elif type in [
        "amount_concentration",
        "frequency",
        "length",
        "mass_concentration",
        "time",
        "volume",
        "volume_concentration",
        # TODO: Deprecate the following two types in next major release
        "concentration(mass)",
        "concentration(molar)",
    ]:
        try:
            return Unit(val)
        except UnitError as e:
            raise RuntimeError(
                f"The value supplied ({e.value}) as a unit of '{type}' is "
                f"improperly formatted. Units of {type} must be in the form: "
                f"'number:unit'"
            )
    elif type == "temperature":
        try:
            if val in [
                "ambient",
                "warm_30",
                "warm_35",
                "warm_37",
                "cold_4",
                "cold_20",
                "cold_80",
                "cold_196",
            ]:
                return val
            return Unit(val)
        except UnitError as e:
            raise RuntimeError(
                f"Invalid temperature value for {e.value}: "
                f"temperature input types must be either "
                f"storage conditions (ex: 'cold_20') or "
                f"temperature units in the form of "
                f"'number:unit'"
            )
    elif type in "bool":
        return bool(val)
    elif type in "csv":
        return val
    elif type in ["string", "choice"]:
        return str(val)
    elif type == "integer":
        try:
            return int(val)
        except ValueError:
            label = type_desc.get("label") or "[unknown]"
            raise RuntimeError(
                f"The value supplied to input '{label}' (type integer) is "
                f"improperly formatted."
            )
    elif type == "decimal":
        try:
            return float(val)
        except ValueError:
            label = type_desc.get("label") or "[unknown]"
            raise RuntimeError(
                f"The value supplied to input '{label}' (type decimal) is "
                f"improperly formatted."
            )
    elif type == "group":
        try:
            return {
                k: convert_param(protocol, val.get(k), type_desc["inputs"][k])
                for k in type_desc["inputs"]
            }
        except KeyError as e:
            label = type_desc.get("label") or "[unknown]"
            raise RuntimeError(
                f"The value supplied to input '{label}' (type group) is "
                f"missing a(n) {e} field."
            )
        except AttributeError:
            label = type_desc.get("label") or "[unknown]"
            raise RuntimeError(
                f"The value supplied to input '{label}' (type group) is "
                f"improperly formatted."
            )
    elif type == "group+":
        try:
            return [
                {
                    k: convert_param(protocol, x.get(k), type_desc["inputs"][k])
                    for k in type_desc["inputs"]
                }
                for x in val
            ]
        except (TypeError, AttributeError):
            raise RuntimeError(
                f"The value supplied to input '{type_desc['label']}' "
                f"(type group+) must be in the form of a list of dictionaries"
            )
        except KeyError as e:
            label = type_desc.get("label") or "[unknown]"
            raise RuntimeError(
                f"The value supplied to input '{label}' (type group+) is "
                f"missing a(n) {e} field."
            )
    elif type == "group-choice":
        try:
            return {
                "value": val["value"],
                "inputs": {
                    opt["value"]: convert_param(
                        protocol,
                        val["inputs"].get(opt["value"]),
                        {"type": "group", "inputs": opt["inputs"]},
                    )
                    for opt in type_desc["options"]
                    if opt["value"] == val["value"]
                },
            }
        except (KeyError, AttributeError) as e:
            label = type_desc.get("label") or "[unknown]"
            if e in ["value", "inputs"]:
                raise RuntimeError(
                    f"The value supplied to input '{label}' "
                    f"(type group-choice) is missing a(n) {e} field."
                )
    elif type == "thermocycle":
        try:
            return [
                {
                    "cycles": g["cycles"],
                    "steps": [
                        convert_param(protocol, s, "thermocycle_step")
                        for s in g["steps"]
                    ],
                }
                for g in val
            ]
        except (TypeError, KeyError):
            raise RuntimeError(_thermocycle_error_text())

    elif type == "thermocycle_step":
        try:
            output = {"duration": Unit(val["duration"])}
        except UnitError as e:
            raise RuntimeError(
                f"Invalid duration value for {e.value}: duration input types "
                f"must be time units in the form of 'number:unit'"
            )

        try:
            if "gradient" in val:
                output["gradient"] = {
                    "top": Unit(val["gradient"]["top"]),
                    "bottom": Unit(val["gradient"]["bottom"]),
                }
            else:
                output["temperature"] = Unit(val["temperature"])
        except UnitError as e:
            raise RuntimeError(
                f"Invalid temperature value for {e.value}: thermocycle "
                f"temperature input types must be temperature units in the "
                f"form of 'number:unit'"
            )

        if "read" in val:
            output["read"] = val["read"]

        return output

    elif type == "csv-table":
        try:
            values = []
            for i, row in enumerate(val[1]):
                value = {}
                for header, header_value in row.items():
                    type_desc = {
                        "type": val[0].get(header),
                        "label": f"csv-table item ({i}): {header}",
                    }

                    value[header] = convert_param(
                        protocol, header_value, type_desc=type_desc
                    )

                values.append(value)

            return values

        except (AttributeError, IndexError, TypeError):
            label = type_desc.get("label") or "[unknown]"
            raise RuntimeError(
                f"The values supplied to {label} (type csv-table) are "
                f"improperly formatted. Format must be a list of dictionaries "
                f"with the first dictionary comprising keys with associated "
                f"column input types."
            )

    else:
        raise ValueError(f"Unknown input type {type!r}")


class ProtocolInfo(object):
    def __init__(self, json_dict):
        self.input_types = json_dict["inputs"]

    def parse(self, protocol, inputs):
        refs = inputs["refs"]
        params = inputs["parameters"]

        for name in refs:
            ref = refs[name]
            c = protocol.ref(
                name,
                ref.get("id"),
                ref["type"],
                storage=ref.get("store"),
                discard=ref.get("discard"),
                cover=ref.get("cover"),
            )
            aqs = ref.get("aliquots")
            if aqs:
                for idx in aqs:
                    aq = aqs[idx]
                    c.well(idx).set_volume(aq["volume"])
                    if "name" in aq:
                        c.well(idx).set_name(aq["name"])
                    if "mass_mg" in aq:
                        c.well(idx).set_mass(aq["mass_mg"])
                    if "properties" in aq:
                        c.well(idx).set_properties(aq.get("properties"))

        out_params = {}
        for k in self.input_types:
            typeDesc = self.input_types[k]
            out_params[k] = convert_param(protocol, params.get(k), typeDesc)

        return out_params


class Manifest(object):
    """
    Object representation of a manifest.json file

    Parameters
    ----------
    object : JSON object
        A manifest.json file with the following format:

        .. code-block:: none

            {
              "format": "python",
              "license": "MIT",
              "description": "This is a protocol.",
              "protocols": [
                {
                  "name": "SampleProtocol",
                  "version": 1.0.0,
                  "command_string": "python sample_protocol.py",
                  "preview": {
                    "refs":{},
                    "parameters": {},
                    "inputs": {},
                    "dependencies": []
                  }
                }
              ]
            }

    """

    def __init__(self, json_dict):
        self.protocols = json_dict["protocols"]

    def protocol_info(self, name):
        try:
            return ProtocolInfo(next(p for p in self.protocols if p["name"] == name))
        except StopIteration:
            raise RuntimeError(
                f"Harness.run(): {name} does not match the "
                f"'name' field of any protocol in the "
                f"associated manifest.json file."
            )


def run(fn, protocol_name=None, seal_after_run=True, protocol_class=None):
    """
    Run the protocol specified by the function.

    If protocol_name is passed, use preview parameters from the protocol with
    the matching "name" value in the manifest.json file to run the given
    function.  Otherwise, take configuration JSON file from the command line
    and run the given function.

    Parameters
    ----------
    fn : function
        Function that generates Autoprotocol
    protocol_name :  str, optional
        str matching the "name" value in the manifest.json file
    seal_after_run : bool, optional
        Implicitly add a seal/cover to all stored refs within the protocol
        using seal_on_store()
    protocol_class: Protocol, optional
        References the base protocol class to be used for instantiation.
        If not provided, defaults to using Autoprotocol Python's default
        Protocol implementation

    Raises
    ------
    TypeError
        If protocol_class provided is not a subclass of Protocol
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="JSON-formatted protocol configuration file")
    parser.add_argument(
        "--dye_test",
        help="Execute protocol by pre-filling preview aliquots with OrangeG "
        "dye, and provisioning water only.",
        action="store_true",
    )
    args = parser.parse_args()

    source = json.loads(io.open(args.config, encoding="utf-8").read())

    if protocol_class is None:
        protocol = Protocol()
    else:
        if not issubclass(protocol_class, Protocol):
            raise TypeError(
                "Protocol class provided needs to be subclass of " "Protocol"
            )
        protocol = protocol_class()

    # pragma pylint: disable=protected-access
    if protocol_name:
        manifest_json = io.open("manifest.json", encoding="utf-8").read()
        manifest = Manifest(json.loads(manifest_json))
        params = manifest.protocol_info(protocol_name).parse(protocol, source)
        # Add dye to preview aliquots if --dye_test included as an optional
        # argument
        if args.dye_test:
            num_dye_steps = _add_dye_to_preview_refs(protocol)
    else:
        params = protocol._ref_containers_and_wells(source["parameters"])
    # pragma pylint: enable=protected-access

    try:
        fn(protocol, params)
        if seal_after_run:
            seal_on_store(protocol)
        # Convert all provisions to water if --dye_test is included as an
        # optional argument
        if args.dye_test:
            _convert_provision_instructions(
                protocol, num_dye_steps, len(protocol.instructions) - 1
            )
            _convert_dispense_instructions(
                protocol, num_dye_steps, len(protocol.instructions) - 1
            )
    except UserError as e:
        print(
            json.dumps({"errors": [{"message": e.message, "info": e.info}]}, indent=2)
        )
        return

    print(json.dumps(protocol.as_dict(), indent=2))


def _add_dye_to_preview_refs(protocol, rs=_DYE_TEST_RS["dye4000"]):
    # Store starting number of instructions
    starting_num = len(protocol.instructions)

    # For each ref in protocol
    for _, ref_obj in protocol.refs.items():

        ref_cont = ref_obj.container
        # Raise RuntimeError if any refs have an id, to avoid adding dye to
        # real samples
        if ref_cont.id:
            raise RuntimeError(
                "Cannot run a dye test when any ref has a defined container "
                "id. Please resubmit using only new containers."
            )

        # Add dye to each well
        for well in ref_cont.all_wells():
            current_vol = well.volume
            if current_vol and current_vol > Unit(0, "microliter"):
                protocol.provision(rs, well, current_vol)
                well.set_volume(current_vol)

    # Return number of instructions added
    return len(protocol.instructions) - starting_num


def _convert_provision_instructions(
    protocol, first_index, last_index, rs=_DYE_TEST_RS["water"]
):
    # Make sure inputs are valid
    if not isinstance(first_index, int):
        raise ValueError("first_index must be a non-negative integer")
    if not isinstance(last_index, int):
        raise ValueError("last_index must be a non-negative integer")
    if first_index < 0:
        raise ValueError("Indices out of range. first_index must be 0 or greater")
    if first_index > len(protocol.instructions) - 1:
        raise ValueError(
            "Indices out of range. The last instruction index in the protocol "
            "is %d" % (len(protocol.instructions) - 1)
        )
    if last_index > len(protocol.instructions) - 1:
        raise ValueError(
            "Indices out of range. The last instruction index in the protocol "
            "is %d" % (len(protocol.instructions) - 1)
        )
    if last_index < first_index:
        raise ValueError("last_index must be greater than or equal to first_index")

    for instruction in protocol.instructions[first_index : last_index + 1]:
        if instruction.op == "provision":
            instruction.data["resource_id"] = rs


def _convert_dispense_instructions(
    protocol, first_index, last_index, rs=_DYE_TEST_RS["water"]
):
    # Make sure inputs are valid
    if not isinstance(first_index, int):
        raise ValueError("first_index must be a non-negative integer")
    if not isinstance(last_index, int):
        raise ValueError("last_index must be a non-negative integer")
    if first_index < 0:
        raise ValueError("Indices out of range. first_index must be 0 or greater")
    if first_index > len(protocol.instructions) - 1:
        raise ValueError(
            "Indices out of range. The last instruction index in the protocol "
            "is %d" % (len(protocol.instructions) - 1)
        )
    if last_index > len(protocol.instructions) - 1:
        raise ValueError(
            "Indices out of range. The last instruction index in the protocol "
            "is %d" % (len(protocol.instructions) - 1)
        )
    if last_index < first_index:
        raise ValueError("last_index must be greater than or equal to first_index")

    for instruction in protocol.instructions[first_index : last_index + 1]:
        if instruction.op == "dispense":
            if "resource_id" in instruction.data:
                instruction.data["resource_id"] = rs
            if "reagent" in instruction.data:
                instruction.data.pop("reagent", None)
                instruction.data["resource_id"] = rs


def _thermocycle_error_text():
    """
    Returns formatted error text for thermocycle value errors
    """

    return """Thermocycle input types must take a list of dictionaries in the form of:
  [{"cycles": integer,
    "steps": [{
      "duration": duration,
      "temperature": temperature
      "read": boolean (optional)
    }]
  }]
--or--
  [{"cycles": integer,
    "steps": [{
      "duration": duration,
      "gradient": {
        "top": temperature,
        "bottom": temperature
      }
      "read": boolean (optional)
    }]
  }]
(You can intermix gradient and non-gradient steps)"""


def seal_on_store(protocol):
    """
    Implicitly adds seal/cover instructions to the end of a run for containers
    that do not have a cover.   Cover type applied defaults first to
    "seal" if its within the capabilities of the container type, otherwise
    to "cover".

    Example Usage:

        .. code-block:: python

            def example_method(protocol, params):
            cont = params['container']
            p.transfer(cont.well("A1"), cont.well("A2"), "10:microliter")
            p.seal(cont)
            p.unseal(cont)
            p.cover(cont)
            p.uncover(cont)

    Autoprotocol Output:

        .. code-block:: json

            {
              "refs": {
                "plate": {
                  "new": "96-pcr",
                  "store": {
                    "where": "ambient"
                  }
                }
              },
              "instructions": [
                {
                  "groups": [
                    {
                      "transfer": [
                        {
                          "volume": "10.0:microliter",
                          "to": "plate/1",
                          "from": "plate/0"
                        }
                      ]
                    }
                  ],
                  "op": "pipette"
                },
                {
                  "object": "plate",
                  "type": "ultra-clear",
                  "op": "seal"
                },
                {
                  "object": "plate",
                  "op": "unseal"
                },
                {
                  "lid": "universal",
                  "object": "plate",
                  "op": "cover"
                },
                {
                  "object": "plate",
                  "op": "uncover"
                },
                {
                  "type": "ultra-clear",
                  "object": "plate",
                  "op": "seal"
                }
              ]
            }

    """
    for _, ref in protocol.refs.items():
        if "store" in ref.opts.keys():
            if not (ref.container.is_covered() or ref.container.is_sealed()):
                default_method = ref.container.container_type.prioritize_seal_or_cover
                sealable = "seal" in ref.container.container_type.capabilities
                coverable = "cover" in ref.container.container_type.capabilities
                if default_method == "seal" and sealable:
                    protocol.seal(
                        ref.container, ref.container.container_type.seal_types[0]
                    )
                elif default_method == "cover" and coverable:
                    protocol.cover(
                        ref.container, ref.container.container_type.cover_types[0]
                    )
                elif sealable:
                    protocol.seal(
                        ref.container, ref.container.container_type.seal_types[0]
                    )
                elif coverable:
                    protocol.cover(
                        ref.container, ref.container.container_type.cover_types[0]
                    )
                else:
                    continue
