import json
from autoprotocol.util import make_dottable_dict
from autoprotocol.container import WellGroup

def ligate(protocol, params):
    '''
    Template for ligation_config.json file
    (change or add to defaults for your run):
    {
        "parameters":{
            "resources": {
                "id": null,
                "type": "384-pcr",
                "storage": "cold_20",
                "discard": false
            },
            "water": {
                "id": null,
                "type": "micro-1.5",
                "storage": "cold_4",
                "discard": false
            },
            "destination_plate": {
                "id": null,
                "type": "96-pcr",
                "storage": "cold_4",
                "discard": false
            },
            "T4_Ligase": "resources/A1",
            "T4_buffer": "resources/A2",
            "cut_backbone": "resources/B1",
            "insert_1": "resources/B2",
            "insert_2": "resources/B3",
            "insert_3": "resources/B4",
            "construct_1": "destination_plate/B1",
            "construct_2": "destination_plate/B2",
            "construct_3": "destination_plate/B3",
            "ligase_vol": "3:microliter",
            "buffer_vol": "2:microliter",
            "source_DNA_vol": "1:microliter",
            "insert_vol": "3:microliter",
            "water_vol": "2:microliter",
            "ligation_time": "10:minute",
            "deactivation_time": "5:minute",
            "deactivation_temp": "65:celsius"
        }
    }
    '''
    params = make_dottable_dict(params)
    refs = make_dottable_dict(params.refs)

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

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(ligate)