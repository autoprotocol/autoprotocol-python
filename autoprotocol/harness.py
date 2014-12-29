import json
from .protocol import Protocol
import argparse

def run(fn):
    '''
    Take a function passed to it, initialize a Protocol object, run
    Protocol.ref_container and Protocol.make_well_references on the JSON config
    file specified on the command-line and pass what they return to the function
    passed. Prints resulting protocol to standard out.

    Example
    -------

    sample_config.json
        {
            "refs":{
                "sample_plate":{
                    "id": null,
                    "type": "96-deep",
                    "storage": null,
                    "discard": true
                }
            },
            "parameters": {
                "buffer_vol": "4:microliter"
            }

        }

    sample.py

        def sample(protocol, refs, params):
            protocol.distribute(refs["sample_plate"].well("A1"),
                refs["sample_plate"].wells_from("B1", 12),
                params["buffer_vol"]

        if __name__ == '__main__':
            from autoprotocol.harness import run
            run(sample)

    on command-line:
        $python -m autoprotocol.protocol.sample autoprotocol/config/sample_config.json

    Parameters
    ----------
    fn :function


    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='JSON-formatted protocol configuration file')
    args = parser.parse_args()
    config = json.loads(open(args.config, 'r').read().decode("utf-8"))

    protocol = Protocol()
    refs = protocol.ref_containers(config["refs"])
    params = protocol.make_well_references(config["parameters"])

    fn(protocol, refs, params)

    print json.dumps(protocol.as_dict(), indent=2)
