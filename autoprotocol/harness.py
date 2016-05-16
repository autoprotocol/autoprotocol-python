from __future__ import print_function
import json
import io
from .protocol import Protocol
from .unit import Unit, UnitError
from .container import WellGroup
from . import UserError
import argparse
import sys

if sys.version_info[0] >= 3:
    string_type = str
else:
    string_type = basestring

'''
    :copyright: 2016 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''


def param_default(typeDesc):
    if isinstance(typeDesc, string_type):
        typeDesc = {'type': typeDesc}

    type = typeDesc['type']
    default = typeDesc.get('default')

    if default is not None and type != 'group-choice':
        return default

    if typeDesc['type'] in ['aliquot+', 'aliquot++', 'container+']:
        return []
    elif typeDesc['type'] == 'group+':
        return [{}]
    elif typeDesc['type'] == 'group':
        return {
            k: param_default(v)
            for k, v in typeDesc['inputs'].items()
        }
    elif typeDesc['type'] == 'group-choice':
        default_inputs = {}
        for option in typeDesc.get('options', []):
            value = option.get('value')
            inputs = option.get('inputs')
            if inputs:
                group_typedesc = {'type': 'group', 'inputs': inputs}
                default_inputs[value] = param_default(group_typedesc)

        return {
            'value': default,
            'inputs': default_inputs
        }
    elif typeDesc['type'] == 'csv-table':
        return [{}, {}]
    else:
        return None


def convert_param(protocol, val, typeDesc):
    """
    Convert parameters based on their input types

    Parameters
    ----------
    protocol : Protocol
        Protocol object being parsed.
    val : str, int, bool, dict, list
        Parameter value to be converted.
    typeDesc : dict, str
        Description of input type.

    """
    if isinstance(typeDesc, string_type):
        typeDesc = {'type': typeDesc}
    if val is None:
        val = param_default(typeDesc)
    if val is None:  # still None?
        return None
    type = typeDesc['type']

    if type == 'aliquot':
        try:
            container = ('/').join(val.split('/')[0:-1])
            well_idx = val.split('/')[-1]
            return protocol.refs[container].container.well(well_idx)
        except (KeyError, AttributeError, ValueError):
            label = typeDesc.get('label') or "[unknown]"
            raise RuntimeError("'%s' (supplied to input '%s') is not a valid "
                               "reference to an aliquot" % (val, label))
    elif type == 'aliquot+':
        try:
            return WellGroup([convert_param(protocol, a, 'aliquot') for a in val])
        except:
            label = typeDesc.get('label') or "[unknown]"
            raise RuntimeError("The value supplied to input '%s' (type aliquot+) is improperly "
                               "formatted." % label)
    elif type == 'aliquot++':
        try:
            return [convert_param(protocol, aqs, 'aliquot+') for aqs in val]
        except:
            label = typeDesc.get('label') or "[unknown]"
            raise RuntimeError("The value supplied to input '%s' (type aliquot++) is improperly "
                               "formatted." % label)
    elif type == 'container':

        try:
            return protocol.refs[val].container
        except KeyError:
            label = typeDesc.get('label') or "[unknown]"
            raise RuntimeError("'%s' (supplied to input '%s') is not a valid "
                               "reference to a container" % (val, label))
    elif type == 'container+':
        try:
            return [convert_param(protocol, cont, 'container') for cont in val]
        except:
            label = typeDesc.get('label') or "[unknown]"
            raise RuntimeError("The value supplied to input '%s' (type container+) is improperly "
                               "formatted." % label)
    elif type in ['volume', 'time', 'length']:
        try:
            return Unit.fromstring(val)
        except UnitError as e:
            raise RuntimeError("The value supplied (%s) as a unit of '%s' is "
                               "improperly formatted. Units of %s must be in "
                               "the form: 'number:unit'" % (e.value, type, type))
    elif type == 'temperature':
        try:
            if val in ['ambient', 'warm_30', 'warm_37', 'cold_4', 'cold_20', 'cold_80']:
                return val
            else:
                return Unit.fromstring(val)
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
            label = typeDesc.get('label') or "[unknown]"
            raise RuntimeError("The value supplied to input '%s' (type integer) is improperly "
                               "formatted." % label)
    elif type == 'decimal':
        try:
            return float(val)
        except ValueError:
            label = typeDesc.get('label') or "[unknown]"
            raise RuntimeError("The value supplied to input '%s' (type decimal) is improperly "
                               "formatted." % label)
    elif type == 'group':
        try:
            return {
                k: convert_param(protocol, val.get(k), typeDesc['inputs'][k])
                for k in typeDesc['inputs']
            }
        except KeyError as e:
            label = typeDesc.get('label') or "[unknown]"
            raise RuntimeError("The value supplied to input '%s' (type group) is missing "
                               "a(n) %s field." % (label, e))
        except AttributeError:
            label = typeDesc.get('label') or "[unknown]"
            raise RuntimeError("The value supplied to input '%s' (type group) is improperly "
                               "formatted." % label)
    elif type == 'group+':
        try:
            return [{
                    k: convert_param(protocol, x.get(k), typeDesc['inputs'][k])
                    for k in typeDesc['inputs']
                    } for x in val]
        except (TypeError, AttributeError):
            raise RuntimeError("The value supplied to input '%s' (type group+) must be in "
                               "the form of a list of dictionaries" % typeDesc['label'])
        except KeyError as e:
            label = typeDesc.get('label') or "[unknown]"
            raise RuntimeError("The value supplied to input '%s' (type group+) is missing "
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
                    for opt in typeDesc['options'] if opt['value'] == val['value']
                }
            }
        except (KeyError, AttributeError) as e:
            label = typeDesc.get('label') or "[unknown]"
            if e in ["value", "inputs"]:
                raise RuntimeError("The value supplied to input '%s' (type group-choice) "
                                   "is missing a(n) %s field." % (label, e))
    elif type == 'thermocycle':
        try:
            return [
                {
                    'cycles': g['cycles'],
                    'steps': [convert_param(protocol, s, 'thermocycle_step') for s in g['steps']]
                }
                for g in val
            ]
        except (TypeError, KeyError):
            raise RuntimeError(_thermocycle_error_text())

    elif type == 'thermocycle_step':
        try:
            output = {'duration': Unit.fromstring(val['duration'])}
        except UnitError as e:
            raise RuntimeError("Invalid duration value for %s: duration input types must "
                               "be time units in the form of 'number:unit'" % e.value)

        try:
            if 'gradient' in val:
                output['gradient'] = {
                    'top': Unit.fromstring(val['gradient']['top']),
                    'bottom': Unit.fromstring(val['gradient']['bottom'])
                }
            else:
                output['temperature'] = Unit.fromstring(val['temperature'])
        except UnitError as e:
            raise RuntimeError("Invalid temperature value for %s: thermocycle temperature "
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
                    typeDesc = {
                        "type": val[0].get(header),
                        "label": "csv-table item (%s): %s" % (i, header)
                    }

                    value[header] = convert_param(protocol, header_value, typeDesc=typeDesc)

                values.append(value)

            return values

        except (AttributeError, IndexError, TypeError):
            label = typeDesc.get('label') or "[unknown]"
            raise RuntimeError(
                "The values supplied to %s (type csv-table) are improperly "
                "formatted. Format must be a list of dictionaries with the first "
                "dictionary comprising keys with associated column input types." % label
            )

    else:
        raise ValueError("Unknown input type %r" % type)


class ProtocolInfo(object):

    def __init__(self, json):
        self.input_types = json['inputs']

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
                discard=ref.get('discard'))
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

        .. code-block:: json

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
              ]
            }

    """

    def __init__(self, json):
        '''
        '''
        self.protocols = json['protocols']

    def protocol_info(self, name):
        '''
        '''
        try:
            return ProtocolInfo(
                next(p for p in self.protocols if p['name'] == name))
        except StopIteration:
            raise RuntimeError("Harness.run(): %s does not match "
                               "the 'name' field of any protocol in the "
                               "associated manifest.json file." % name)


def run(fn, protocol_name=None):
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

    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config',
        help='JSON-formatted protocol configuration file')
    args = parser.parse_args()

    source = json.loads(io.open(args.config, encoding='utf-8').read())
    protocol = Protocol()
    if protocol_name:
        manifest_json = io.open('manifest.json', encoding='utf-8').read()
        manifest = Manifest(json.loads(manifest_json))
        params = manifest.protocol_info(protocol_name).parse(protocol, source)
    else:
        params = protocol._ref_containers_and_wells(source["parameters"])

    try:
        fn(protocol, params)
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
