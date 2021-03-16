import re


class Compound:
    """
    Represents a single Compound

    Parameters
    ----------
    SMILES : Simplified Molecular-Input Line-Entry System

    """

    def __init__(self, SMILES):
        if self.is_valid(SMILES):
            self.SMILES = SMILES
        else:
            raise CompoundError(f"{SMILES} is not a valid SMILES key")

    @staticmethod
    def is_valid(SMILES):
        # Any alphanumeric string with no space that does not start with 'InChI='
        pattern = r"^(?!InChI=)\w\S+$"
        return re.match(pattern, SMILES)


class CompoundError(Exception):
    def __init__(self, value):
        super(CompoundError, self).__init__(value)
        self.value = value
