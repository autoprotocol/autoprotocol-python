import json
from autoprotocol.util import make_dottable_dict

def kunkel_polymerize(protocol, refs, params):
    params = make_dottable_dict(params)

    reactions = refs["reaction_plate"].wells_from(params.reaction_start, params.kunkel_number, columnwise = True)

    for reaction in reactions:
        protocol.transfer(params.polymerize_MM_loc, reaction, params.polymerize_MM_vol, mix_after=True)

    protocol.seal("reaction_plate")

    protocol.incubate("reaction_plate", "ambient", "1.5:hour")

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(kunkel_polymerize)
