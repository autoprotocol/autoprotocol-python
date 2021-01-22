import enum


class Compound:
    def __init__(self, notation, value):
        if notation in Notation.__members__:
            self.notation = notation
            self.value = value
        else:
            raise CompoundError(
                f" {notation} is not among valid Notations {Notation.__members__.keys()}"
            )


class Notation(enum.Enum):
    SMILES = "SMILES"
    InChI = "InChI"


class CompoundError(Exception):
    def __init__(self, value):
        super(CompoundError, self).__init__(value)
        self.value = value
