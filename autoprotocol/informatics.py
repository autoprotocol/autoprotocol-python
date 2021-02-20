"""
Contains all the Autoprotocol Informatics objects

    :copyright: 2020 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""

from abc import abstractmethod

from .compound import Compound
from .util import is_valid_well


class Informatics:
    """
    Base class for informatics attribute in an instruction that is to later be
    encoded as JSON.
    """

    def __init__(self):
        pass

    @abstractmethod
    def as_dict(self):
        pass

    @abstractmethod
    def validate(self, data):
        pass


class AttachCompounds(Informatics):
    """
    Informatics type attach_compounds is constructed as a list of dict detailing
    new compounds associated with target wells

    Parameters
    ----------
    data: dict
        dict of Informatics data

    Returns
    -------
    AttachCompounds

    Raises
    ------
    TypeError
        data must be a dict
    TypeError
        wells must be Well, list of Well, or WellGroup
    TypeError
        compounds must be a list
    TypeError
        each element in compounds must be Compound type
    """

    def __init__(self, data: dict):

        self.wells = data["wells"]
        self.compounds = data["compounds"]
        self.validate()
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
            "type": "attach_compounds",
            "data": {"wells": self.wells, "compounds": self.compounds},
        }

    def validate(self):
        """
        validate input dict has valid parameters to instantiate AttachCompounds

        Raises
        ------
        TypeError
            wells is a valid well type
        TypeError
            compounds is a list
        TypeError
            compounds element is a Compound
        """
        if not is_valid_well(self.wells):
            raise TypeError(
                f"wells: {self.wells} must be Well, list of Well or WellGroup."
            )

        if not isinstance(self.compounds, list):
            raise TypeError(
                f"compounds: {self.compounds} must be provided in a list."
            )
        for compd in self.compounds:
            if not isinstance(compd, Compound):
                raise TypeError(f"compound: {compd} must be Compound type.")
