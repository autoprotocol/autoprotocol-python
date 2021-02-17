"""
Contains all the Autoprotocol Informatics objects

    :copyright: 2020 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""

from abc import abstractmethod
from .compound import Compound
from .container import Container, WellGroup
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


class AttachCompounds(Informatics):
    """
    informatics type attach_compounds is constructed as a list of dict detailing
    new compounds

    Parameters
    ----------
    data:
        dict of informatics data
    all_wells: WellGroup
        All wells used in the instruction that are applicable for attach_compounds
        to take effect on.

    Returns
    -------
    AttachCompounds

    Raises
    ------
    TypeError
        data must be a dict
    TypeError
        wells must be Well, list of Well, or WellGroup
    ValueError
        wells must be part of wells or containers instruction operates on
    TypeError
        compounds must be a list
    TypeError
        each element in compounds must be Compound type
    """
    def __init__(self, data: dict, all_wells):
        # turn data into specific attributes for this type of informatics
        if not isinstance(data, dict):
            raise TypeError(
                f"informatics data: {data} must be provided in a dict."
            )

        self.wells = data["wells"]
        self.compounds = data["compounds"]

        # validate wells
        if not is_valid_well(self.wells):
            raise TypeError(
                f"wells: {self.wells} must be Well, list of Well or WellGroup."
            )
        wells = WellGroup(self.wells)
        # wells must be one or more of the wells or container instruction is operating on.
        if isinstance(all_wells, Container):
            all_wells = all_wells.all_wells()
        else:
            all_wells = WellGroup(all_wells)
        for well in wells.wells:
            if well not in all_wells.wells:
                raise ValueError(
                    f"informatics well: {wells} must be one of the wells used in this instruction."
                )

        # validate compounds
        if not isinstance(self.compounds, list):
            raise TypeError(
                f"compounds: {self.compounds} must be provided in a list."
            )
        for compd in self.compounds:
            if not isinstance(compd, Compound):
                raise TypeError(f"compound: {compd} must be Compound type.")

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
            "data": {"wells": self.wells, "compounds": self.compounds}
        }
