import json
from autoprotocol.util import make_dottable_dict
from autoprotocol.protocols.kunkel_anneal import kunkel_anneal
from autoprotocol.protocols.kunkel_kinase import kunkel_kinase
from autoprotocol.protocols.kunkel_dilute import kunkel_dilute
from autoprotocol.protocols.kunkel_polymerize import kunkel_polymerize

def kunkel_complete(protocol, refs, params):
    params = make_dottable_dict(params)

    kunkel_kinase(protocol, refs, params.kinase_parameters)

    protocol.unseal("kinased_oligo_plate")

    kunkel_dilute(protocol, refs, params.dilute_parameters)

    kunkel_anneal(protocol, refs, params.anneal_parameters)

    protocol.unseal("reaction_plate")

    kunkel_polymerize(protocol, refs, params.polymerize_parameters)

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(kunkel_complete)