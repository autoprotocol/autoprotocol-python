import json
from .protocol import Protocol
import argparse

def run(fn):
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='JSON-formatted protocol configuration file')
    args = parser.parse_args()
    config = json.loads(open(args.config, 'r').read().decode("utf-8"))

    protocol = Protocol()
    refs = protocol.ref_containers(config["refs"])
    params = protocol.make_well_references(config["parameters"])

    fn(protocol, refs, params)

    print json.dumps(protocol.as_dict(), indent=2)
