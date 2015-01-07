import json
from .protocol import Protocol
import argparse

def run(fn):
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
    parser.add_argument('config', help='JSON-formatted protocol configuration file')
    args = parser.parse_args()
    config = json.loads(open(args.config, 'r').read().decode("utf-8"))

    protocol = Protocol()
    params = protocol._ref_containers_and_wells(config["parameters"])

    fn(protocol, params)

    print json.dumps(protocol.as_dict(), indent=2)
