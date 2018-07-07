"""
Module containing the harness module which helps with Manifest interpretation

    :copyright: 2018 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""

from __future__ import print_function
import json
import io
from .protocol import Protocol
from .unit import Unit, UnitError
from .container import WellGroup
from . import UserError
import argparse
import sys

if sys.version_info.major == 3:
    basestring = str  # pylint: disable=invalid-name

_DYE_TEST_RS = {
    "dye4000": "rs18qmhr7t9jwq",
    "water": "rs17gmh5wafm5p"
}


def param_default(type_desc):
    if isinstance(type_desc, basestring):
        type_desc = {'type': type_desc}

    type = type_desc['type']  # pylint: disable=redefined-builtin
    default = type_desc.get('default')

    if default is not None and type != 'group-choice':
        return default

    if type_desc['type'] in ['aliquot+', 'aliquot++', 'container+']:
        return []
    elif type_desc['type'] == 'group+':
        return [{}]
    elif type_desc['type'] == 'group':
        return {
            k: param_default(v)
            for k, v in type_desc['inputs'].items()
        }
    elif type_desc['type'] == 'group-choice':
        default_inputs = {}
        for option in type_desc.get('options', []):
            value = option.get('value')
            inputs = option.get('inputs')
            if inputs:
                group_typedesc = {'type': 'group', 'inputs': inputs}
                default_inputs[value] = param_default(group_typedesc)

        return {
            'value': default,
            'inputs': default_inputs
        }
    elif type_desc['type'] == 'csv-table':
        return [{}, {}]
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
    if isinstance(type_desc, basestring):
        type_desc = {'type': type_desc}
    if val is None:
        val = param_default(type_desc)
    if val is None:  # still None?
        return None
    type = type_desc['type']  # pylint: disable=redefined-builtin

    if type == 'aliquot':
        try:
            container = ('/').join(val.split('/')[0:-1])
            well_idx = val.split('/')[-1]
            return protocol.refs[container].container.well(well_idx)
        except (KeyError, AttributeError, ValueError):
            label = type_desc.get('label') or "[unknown]"
            raise RuntimeError("'%s' (supplied to input '%s') is not a valid "
                               "reference to an aliquot" % (val, label))
    elif type == 'aliquot+':
        try:
            return WellGroup(
                [convert_param(protocol, a, 'aliquot') for a in val])
        except:
            label = type_desc.get('label') or "[unknown]"
            raise RuntimeError(
                "The value supplied to input '%s' (type aliquot+) is "
                "improperly formatted." % label)
    elif type == 'aliquot++':
        try:
            return [convert_param(protocol, aqs, 'aliquot+') for aqs in val]
        except:
            label = type_desc.get('label') or "[unknown]"
            raise RuntimeError(
                "The value supplied to input '%s' (type aliquot++) is "
                "improperly formatted." % label)
    elif type == 'container':

        try:
            return protocol.refs[val].container
        except KeyError:
            label = type_desc.get('label') or "[unknown]"
            raise RuntimeError("'%s' (supplied to input '%s') is not a valid "
                               "reference to a container" % (val, label))
    elif type == 'container+':
        try:
            return [convert_param(protocol, cont, 'container') for cont in val]
        except:
            label = type_desc.get('label') or "[unknown]"
            raise RuntimeError(
                "The value supplied to input '%s' (type container+) is "
                "improperly formatted." % label)
    elif type in ['volume', 'time', 'length', 'frequency']:
        try:
            return Unit(val)
        except UnitError as e:
            raise RuntimeError("The value supplied (%s) as a unit of '%s' is "
                               "improperly formatted. Units of %s must be in "
                               "the form: 'number:unit'" % (
                               e.value, type, type))
    elif type == 'temperature':
        try:
            if val in ['ambient', 'warm_30', 'warm_37', 'cold_4', 'cold_20',
                       'cold_80']:
                return val
            else:
                return Unit(val)
        except UnitError as e:
            raise RuntimeError("Invalid temperature value for %s: temperature "
                               "input types must be either storage conditions "
                               "(ex: 'cold_20') or temperature units in the "
                               "form of 'number:unit'" % e.value)
    elif type in 'bool':
        return bool(val)
    elif type in 'csv':
        return val
    elif type in ['string', 'choice']:
        return str(val)
    elif type == 'integer':
        try:
            return int(val)
        except ValueError:
            label = type_desc.get('label') or "[unknown]"
            raise RuntimeError(
                "The value supplied to input '%s' (type integer) is improperly "
                "formatted." % label)
    elif type == 'decimal':
        try:
            return float(val)
        except ValueError:
            label = type_desc.get('label') or "[unknown]"
            raise RuntimeError(
                "The value supplied to input '%s' (type decimal) is improperly "
                "formatted." % label)
    elif type == 'group':
        try:
            return {
                k: convert_param(protocol, val.get(k), type_desc['inputs'][k])
                for k in type_desc['inputs']
            }
        except KeyError as e:
            label = type_desc.get('label') or "[unknown]"
            raise RuntimeError(
                "The value supplied to input '%s' (type group) is missing "
                "a(n) %s field." % (label, e))
        except AttributeError:
            label = type_desc.get('label') or "[unknown]"
            raise RuntimeError(
                "The value supplied to input '%s' (type group) is improperly "
                "formatted." % label)
    elif type == 'group+':
        try:
            return [{
                k: convert_param(protocol, x.get(k), type_desc['inputs'][k])
                for k in type_desc['inputs']
            } for x in val]
        except (TypeError, AttributeError):
            raise RuntimeError(
                "The value supplied to input '%s' (type group+) must be in "
                "the form of a list of dictionaries" % type_desc['label'])
        except KeyError as e:
            label = type_desc.get('label') or "[unknown]"
            raise RuntimeError(
                "The value supplied to input '%s' (type group+) is missing "
                "a(n) %s field." % (label, e))
    elif type == 'group-choice':
        try:
            return {
                'value': val['value'],
                'inputs': {
                    opt['value']: convert_param(
                        protocol,
                        val['inputs'].get(opt['value']),
                        {'type': 'group', 'inputs': opt['inputs']})
                    for opt in type_desc['options'] if
                opt['value'] == val['value']
                }
            }
        except (KeyError, AttributeError) as e:
            label = type_desc.get('label') or "[unknown]"
            if e in ["value", "inputs"]:
                raise RuntimeError(
                    "The value supplied to input '%s' (type group-choice) "
                    "is missing a(n) %s field." % (label, e))
    elif type == 'thermocycle':
        try:
            return [
                {
                    'cycles': g['cycles'],
                    'steps': [convert_param(protocol, s, 'thermocycle_step') for
                              s in g['steps']]
                }
                for g in val
            ]
        except (TypeError, KeyError):
            raise RuntimeError(_thermocycle_error_text())

    elif type == 'thermocycle_step':
        try:
            output = {'duration': Unit(val['duration'])}
        except UnitError as e:
            raise RuntimeError(
                "Invalid duration value for %s: duration input types must "
                "be time units in the form of 'number:unit'" % e.value)

        try:
            if 'gradient' in val:
                output['gradient'] = {
                    'top': Unit(val['gradient']['top']),
                    'bottom': Unit(val['gradient']['bottom'])
                }
            else:
                output['temperature'] = Unit(val['temperature'])
        except UnitError as e:
            raise RuntimeError(
                "Invalid temperature value for %s: thermocycle temperature "
                "input types must be temperature units in the form of "
                "'number:unit'" % e.value)

        if 'read' in val:
            output['read'] = val['read']

        return output

    elif type == 'csv-table':
        try:
            values = []
            for i, row in enumerate(val[1]):
                value = {}
                for header, header_value in row.items():
                    type_desc = {
                        "type": val[0].get(header),
                        "label": "csv-table item (%s): %s" % (i, header)
                    }

                    value[header] = convert_param(protocol, header_value,
                                                  type_desc=type_desc)

                values.append(value)

            return values

        except (AttributeError, IndexError, TypeError):
            label = type_desc.get('label') or "[unknown]"
            raise RuntimeError(
                "The values supplied to %s (type csv-table) are improperly "
                "formatted. Format must be a list of dictionaries with the "
                "first dictionary comprising keys with associated column "
                "input types." % label
            )

    else:
        raise ValueError("Unknown input type %r" % type)


class ProtocolInfo(object):

    def __init__(self, json_dict):
        self.input_types = json_dict['inputs']

    def parse(self, protocol, inputs):
        refs = inputs['refs']
        params = inputs['parameters']

        for name in refs:
            ref = refs[name]
            c = protocol.ref(
                name,
                ref.get('id'),
                ref['type'],
                storage=ref.get('store'),
                discard=ref.get('discard'),
                cover=ref.get('cover'))
            aqs = ref.get('aliquots')
            if aqs:
                for idx in aqs:
                    aq = aqs[idx]
                    c.well(idx).set_volume(aq['volume'])
                    if "name" in aq:
                        c.well(idx).set_name(aq['name'])
                    if "properties" in aq:
                        c.well(idx).set_properties(aq.get('properties'))

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
        self.protocols = json_dict['protocols']

    def protocol_info(self, name):
        try:
            return ProtocolInfo(
                next(p for p in self.protocols if p['name'] == name))
        except StopIteration:
            raise RuntimeError("Harness.run(): %s does not match "
                               "the 'name' field of any protocol in the "
                               "associated manifest.json file." % name)


def run(fn, protocol_name=None, seal_after_run=True):
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
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config',
        help='JSON-formatted protocol configuration file')
    parser.add_argument(
        '--dye_test',
        help='Execute protocol by pre-filling preview aliquots with OrangeG '
             'dye, and provisioning water only.',
        action="store_true")
    args = parser.parse_args()

    source = json.loads(io.open(args.config, encoding='utf-8').read())
    protocol = Protocol()

    # pragma pylint: disable=protected-access
    if protocol_name:
        manifest_json = io.open('manifest.json', encoding='utf-8').read()
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
            _convert_provision_instructions(protocol, num_dye_steps,
                                            len(protocol.instructions) - 1)
            _convert_dispense_instructions(protocol, num_dye_steps,
                                           len(protocol.instructions) - 1)
    except UserError as e:
        print(json.dumps({
            'errors': [
                {
                    'message': e.message,
                    'info': e.info
                }
            ]
        }, indent=2))
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
                "id. Please resubmit using only new containers.")

        # Add dye to each well
        for well in ref_cont.all_wells():
            current_vol = well.volume
            if current_vol and current_vol > Unit(0, "microliter"):
                protocol.provision(rs, well, current_vol)
                well.set_volume(current_vol)

    # Return number of instructions added
    return len(protocol.instructions) - starting_num


def _convert_provision_instructions(protocol, first_index, last_index,
                                    rs=_DYE_TEST_RS["water"]):
    # Make sure inputs are valid
    if not isinstance(first_index, int):
        raise ValueError("first_index must be a non-negative integer")
    if not isinstance(last_index, int):
        raise ValueError("last_index must be a non-negative integer")
    if first_index < 0:
        raise ValueError(
            "Indices out of range. first_index must be 0 or greater")
    if first_index > len(protocol.instructions) - 1:
        raise ValueError(
            "Indices out of range. The last instruction index in the protocol "
            "is %d" % (len(protocol.instructions) - 1))
    if last_index > len(protocol.instructions) - 1:
        raise ValueError(
            "Indices out of range. The last instruction index in the protocol "
            "is %d" % (len(protocol.instructions) - 1))
    if last_index < first_index:
        raise ValueError(
            "last_index must be greater than or equal to first_index")

    for instruction in protocol.instructions[first_index:last_index + 1]:
        if instruction.op == "provision":
            instruction.data["resource_id"] = rs


def _convert_dispense_instructions(protocol, first_index, last_index,
                                   rs=_DYE_TEST_RS["water"]):
    # Make sure inputs are valid
    if not isinstance(first_index, int):
        raise ValueError("first_index must be a non-negative integer")
    if not isinstance(last_index, int):
        raise ValueError("last_index must be a non-negative integer")
    if first_index < 0:
        raise ValueError(
            "Indices out of range. first_index must be 0 or greater")
    if first_index > len(protocol.instructions) - 1:
        raise ValueError(
            "Indices out of range. The last instruction index in the protocol "
            "is %d" % (len(protocol.instructions) - 1))
    if last_index > len(protocol.instructions) - 1:
        raise ValueError(
            "Indices out of range. The last instruction index in the protocol "
            "is %d" % (len(protocol.instructions) - 1))
    if last_index < first_index:
        raise ValueError(
            "last_index must be greater than or equal to first_index")

    for instruction in protocol.instructions[first_index:last_index + 1]:
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
                default_method = (
                    ref.container.container_type.prioritize_seal_or_cover)
                sealable = "seal" in ref.container.container_type.capabilities
                coverable = "cover" in ref.container.container_type.capabilities
                if default_method == "seal" and sealable:
                    protocol.seal(ref.container,
                                  ref.container.container_type.seal_types[0])
                elif default_method == "cover" and coverable:
                    protocol.cover(ref.container,
                                   ref.container.container_type.cover_types[0])
                elif sealable:
                    protocol.seal(ref.container,
                                  ref.container.container_type.seal_types[0])
                elif coverable:
                    protocol.cover(ref.container,
                                   ref.container.container_type.cover_types[0])
                else:
                    continue
