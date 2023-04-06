import json

from autoprotocol.informatics import Informatics
from autoprotocol.util import parse_unit


class TestUtils:
    @staticmethod
    def read_json_file(file_path: str):
        file = open("./test/data/{0}".format(file_path), encoding="utf-8")
        data = json.load(file)
        return json.dumps(data, indent=2, sort_keys=True)


class TestProvisionMixture(Informatics):
    def __init__(self, mixture_id, volume_to_provision, total_volume):
        self.mixture_id = mixture_id
        self.volume_to_provision = parse_unit(volume_to_provision, "uL")
        self.total_volume = parse_unit(total_volume, "uL")
        super().__init__()

    def as_dict(self):
        """generates a Python object representation of Informatics attribute in
        class Instruction

         Returns
         -------
         dict
             a dict of python objects that have the same structure as the
             Autoprotocol JSON for the Informatics

         Notes
         -----
         Used as a part of JSON serialization of the Instruction

         See Also
         --------
         :class:`Instruction` : Instruction class

        """

        return {
            "type": "provision_mixture",
            "data": {
                "mixture_id": self.mixture_id,
                "volume_to_provision": self.volume_to_provision,
                "total_volume": self.total_volume,
            },
        }

    def validate(self):
        pass
