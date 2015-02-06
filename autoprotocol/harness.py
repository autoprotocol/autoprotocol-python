import json
from .protocol import Protocol
from .unit import Unit
from .container import WellGroup
import argparse

'''
    :copyright: 2015 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''


def convert_param(protocol, val, type):
    if type == 'aliquot':
        container, well_idx = val.split('/')
        return protocol.refs[container].container.well(well_idx)
    elif type == 'aliquot+':
        return WellGroup([convert_param(protocol, a, 'aliquot') for a in val])
    elif type == 'aliquot++':
        return [convert_param(protocol, aqs, 'aliquot+') for aqs in val]
    elif type == 'container':
        return protocol.refs[val].container
    elif type in ['volume', 'time', 'temperature']:
        if val in ['ambient', 'warm_37', 'cold_4', 'cold_20']:
            return val
        else:
            return Unit.fromstring(val)
    elif type in ['integer', 'bool', 'string']:
        return val
    elif type == 'decimal':
        return float(val)


class ProtocolInfo(object):
    def __init__(self, json):
        self.input_types = json['inputs']

    def parse(self, protocol, inputs):
        refs = inputs['refs']
        params = inputs['parameters']

        for name, ref in refs.iteritems():
            c = protocol.ref(
                name,
                ref.get('id'),
                ref['type'],
                storage=ref.get('store'),
                discard=ref.get('discard'))
            aqs = ref.get('aliquots')
            if aqs:
                for idx, aq in aqs.iteritems():
                    c.well(idx).set_volume(aq['volume'])
                    if "properties" in aq:
                        c.well(idx).set_properties(aq.get('properties'))

        out_params = {}
        for k, v in params.iteritems():
            out_params[k] = convert_param(protocol, v, self.input_types[k])

        return out_params


class Manifest(object):
    def __init__(self, json):
        self.version = json['version']
        self.protocols = json['protocols']

    def protocol_info(self, name):
        return ProtocolInfo(
            next(p for p in self.protocols if p['name'] == name))


def run(fn, protocol_name=None):
    """
    If no protocol_name is passed, use preview parameters from matching
    protocol in the manifest.json file to run the given function.  Otherwise,
    take configuration JSON file from the command line and run the given
    protocol.

    Parameters
    ----------
    fn : function

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

    print json.dumps(protocol.as_dict(), indent=2)
