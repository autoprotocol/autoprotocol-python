from autoprotocol.informatics import Informatics
from autoprotocol.util import parse_unit

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
