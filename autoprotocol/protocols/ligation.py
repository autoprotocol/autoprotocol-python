import json
from autoprotocol.util import make_dottable_dict

def ligate(protocol, refs, params):
    params = make_dottable_dict(params)
    refs = make_dottable_dict(refs)

    destination_wells = WellGroup([params.construct_1, params.construct_2, params.construct_3])

    #distribute water and backbone
    protocol.distribute(refs.water.well(0), destination_wells, params.water_vol, allow_carryover=True)
    protocol.distribute(params.cut_backbone, destination_wells, params.source_DNA_vol)

    #transfer buffer and ligase to all final wells
    protocol.transfer(params.T4_Ligase, destination_wells, params.ligase_vol)
    protocol.transfer(params.T4_buffer, destination_wells, params.buffer_vol)

    #transfer DNA to appropriate wells
    protocol.transfer(params.insert_1, destination_wells, params.insert_vol, mix_after=True)
    protocol.transfer(params.insert_2, params.construct_2, params.insert_vol, mix_after=True)
    protocol.transfer(params.insert_3, params.construct_3, params.insert_vol, mix_after=True)


    protocol.seal("destination_plate")

    protocol.incubate("destination_plate","ambient", params.ligation_time)

    #thermocycle to deactivate enzyme
    protocol.thermocycle("destination_plate", [
        {"cycles": 1, "steps": [
            {"temperature": params.deactivation_temp, "duration": params.deactivation_time},
        ]},
    ])

    print json.dumps(protocol.as_dict(), indent=4)

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(ligate)