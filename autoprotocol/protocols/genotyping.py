from autoprotocol.container import WellGroup
from autoprotocol.util import make_dottable_dict

def genotyping(protocol, params):
    '''
    Template for genotyping_config.json file
    do not change the structure of this config file, make sure that the tubes
    containing your master mix has a key in the format of "mastermixname_MM" and
    the corresponding source DNA samples are a list of well references associated
    with a key in the parameters with the format of "mastermixname_samples"

    (change or add to default values for your run):
    {
        "parameters":{
            "allele1_MM": {
                "id": null,
                "type": "micro-1.5",
                "storage": "cold_20",
                "discard": false
            },
            "allele2_MM": {
                "id": null,
                "type": "micro-1.5",
                "storage": "cold_20",
                "discard": false
            },
            "dna_source": {
                "id": null,
                "type": "96-flat",
                "storage": "cold_4",
                "discard": false
            },
            "pcr": {
                "id": null,
                "type": "96-pcr",
                "storage": "cold_20",
                "discard": false
            },
            "pcr_match_sample_layout":true,
            "mastermix_vol_per_rxn": "14:microliter",
            "sample_vol": "3:microliter",
            "allele1_samples": [
                "dna_source/0",
                "dna_source/1",
                "dna_source/2",
                "dna_source/3",
                "dna_source/4",
                "dna_source/5",
                "dna_source/6",
                "dna_source/7",
                "dna_source/8",
                "dna_source/9",
                "dna_source/10",
                "dna_source/11"
            ],
            "allele2_samples": [
                "dna_source/12",
                "dna_source/13",
                "dna_source/14",
                "dna_source/15",
                "dna_source/16",
                "dna_source/17",
                "dna_source/18",
                "dna_source/19",
                "dna_source/20",
                "dna_source/21",
                "dna_source/22",
                "dna_source/23"
            ],
        "pcr_cycles": 30,
        "activation_time": "2:minute",
        "activation_temp": "95:celsius",
        "denaturation_time": "10:second",
        "denaturation_temp": "94:celsius",
        "annealing_time": "15:second",
        "annealing_temp": "55:celsius",
        "extension_time": "20:second",
        "extension_temp": "72:celsius"
        }
    }

    '''
    params = make_dottable_dict(params)
    refs = make_dottable_dict(params.refs)

    mix_to_samples = {}

    for k in refs.keys():
        if k.rsplit("_")[-1] == "MM":
            mix_to_samples[k] = params["%s_samples" % k.rsplit("_")[0]]

    for mix, group in mix_to_samples.items():
        if params.pcr_match_sample_layout:
            destination_wells = WellGroup([refs.pcr.well(i) for i in group.indices()])
            protocol.distribute(refs[mix].well(0), destination_wells,
                params.mastermix_vol_per_rxn, allow_carryover=True)
            protocol.transfer(group, destination_wells, params.sample_vol)
        else:
            pass

    protocol.seal("pcr")

    protocol.thermocycle(refs["pcr"], [
        {"cycles": 1,
         "steps": [{
            "temperature": params.activation_temp,
            "duration": params.activation_time,
            }]
         },
         {"cycles": params.pcr_cycles,
             "steps": [
                {"temperature": params.denaturation_temp,
                 "duration": params.denaturation_time},
                {"temperature": params.annealing_temp,
                 "duration": params.annealing_time},
                {"temperature": params.extension_temp,
                 "duration": params.extension_time}
                ]
        },
            {"cycles": 1,
                "steps": [
                {"temperature": "72:celsius", "duration":"2:minute"}]
            }
    ])


if __name__ == '__main__':
    from autoprotocol.harness import run
    run(genotyping)
