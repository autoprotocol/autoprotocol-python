import json
from .protocol import Protocol
from .unit import Unit
from .container import WellGroup
import argparse


def convert_param(protocol, val, type):
    if type == 'aliquot':
        container, well_idx = val.split('/')
        return protocol.refs[container].container.well(well_idx)
    elif type == 'aliquot+':
        return WellGroup([convert_param(protocol, a, 'aliquot') for a in val])
    elif type == 'container':
        return protocol.refs[val].container
    elif type in ['volume', 'time', 'temperature']:
        return Unit.fromstring(val)
    elif type == 'integer':
        return val


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
    '''Take configuration JSON file from the command line and run the given
    protocol.

    Example
    -------

    sample_config.json
        {
            "parameters": {
                "sample_plate":{
                    "id": null,
                    "type": "96-deep",
                    "storage": null,
                    "discard": true
                },
                "buffer_vol": "4:microliter"
            }

        }

    sample.py

        def sample(protocol, params):
            protocol.distribute(params.refs["sample_plate"].well("A1"),
                refs["sample_plate"].wells_from("B1", 12),
                params["buffer_vol"]

        if __name__ == '__main__':
            from autoprotocol.harness import run
            run(sample)

    on command-line:
        $ python -m sample autoprotocol/config/sample_config.json

    Parameters
    ----------
    fn : function
    '''
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
