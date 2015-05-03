from __future__ import print_function
import json
from .protocol import Protocol
from .unit import Unit
from .container import WellGroup
import argparse
import sys

if sys.version_info[0] >= 3:
    string_type = str
else:
    string_type = basestring

'''
    :copyright: 2015 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''


def param_default(typeDesc):
    if isinstance(typeDesc, string_type):
        typeDesc = {'type': typeDesc}
    if typeDesc['type'] in ['aliquot+', 'aliquot++']:
        return []
    elif typeDesc['type'] == 'group+':
        return [{}]
    elif typeDesc['type'] == 'group':
        return {
            k: param_default(typeDesc['inputs'][k])
            for k, v in typeDesc['inputs'].items()
        }
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
        val = typeDesc.get('default') or param_default(typeDesc)
    if val is None:  # still None?
        return None

    type = typeDesc['type']

    if type == 'aliquot':
        container, well_idx = val.split('/')
        return protocol.refs[container].container.well(well_idx)
    elif type == 'aliquot+':
        return WellGroup([convert_param(protocol, a, 'aliquot') for a in val])
    elif type == 'aliquot++':
        return [convert_param(protocol, aqs, 'aliquot+') for aqs in val]
    elif type == 'container':
        return protocol.refs[val].container
    elif type in ['volume', 'time', 'temperature', 'length']:
        # TODO: this should be a separate 'condition' type, rather than
        # overloading 'temperature'.
        if type == 'temperature' and \
                val in ['ambient', 'warm_37', 'cold_4', 'cold_20', 'cold_80']:
            return val
        else:
            return Unit.fromstring(val)
    elif type in 'bool':
        return bool(val)
    elif type == 'string':
        return str(val)
    elif type == 'integer':
        return int(val)
    elif type == 'decimal':
        return float(val)
    elif type == 'group':
        return {
            k: convert_param(protocol, val.get(k), typeDesc['inputs'][k])
            for k in typeDesc['inputs']
            }
    elif type == 'group+':
        return [{
            k: convert_param(protocol, x.get(k), typeDesc['inputs'][k])
            for k in typeDesc['inputs']
            } for x in val]
    elif type == 'thermocycle':
        return [
            {
                'cycles': g['cycles'],
                'steps': [
                    {
                        'duration': Unit.fromstring(s['duration']),
                        'temperature': Unit.fromstring(s['temperature'])
                    }
                    for s in g['steps']
                ]
            }
            for g in val
        ]
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
              "version": "1.0.0",
              "format": "python",
              "license": "MIT",
              "description": "This is a protocol.",
              "protocols": [
                {
                  "name": "SampleProtocol",
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
        self.version = json['version']
        self.protocols = json['protocols']

    def protocol_info(self, name):
        return ProtocolInfo(
            next(p for p in self.protocols if p['name'] == name))


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

    source = json.loads(open(args.config, 'r').read().decode("utf-8"))
    protocol = Protocol()
    if protocol_name:
        manifest_json = open('manifest.json', 'r').read().decode('utf-8')
        manifest = Manifest(json.loads(manifest_json))
        params = manifest.protocol_info(protocol_name).parse(protocol, source)
    else:
        params = protocol._ref_containers_and_wells(source["parameters"])

    fn(protocol, params)

    print(json.dumps(protocol.as_dict(), indent=2))
