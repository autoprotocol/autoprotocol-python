import json
from autoprotocol.container import WellGroup
from autoprotocol.util import make_dottable_dict
from autoprotocol.protocol import Protocol

def kunkel_anneal(protocol, refs, params):
    params = make_dottable_dict(params)

    reaction_wells = refs["reaction_plate"].wells_from(0,len(params.oligos), columnwise=True)

    protocol.distribute(params.ssDNA_mix_loc,reaction_wells, params.ssDNA_mix_vol)

    for oligo,reaction in zip(params.oligos,reaction_wells.wells):
        protocol.transfer(oligo,reaction,params.oligo_vol,mix_after=True)

    protocol.seal("reaction_plate")

    protocol.thermocycle_ramp("reaction_plate","95:celsius", "25:celsius", "60:minute", step_duration="4:minute")

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(kunkel_anneal)