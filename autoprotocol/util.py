"""
Module containing utility functions

    :copyright: 2021 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""

from .constants import SBS_FORMAT_SHAPES
from .unit import Unit, UnitStringError, UnitValueError


def is_valid_well(well):
    """Checks if an input is of type Well, WellGroup or list of type Well.

    Example Usage:

    .. code-block:: python

        if not is_valid_well(source):
            raise TypeError("Source must be of type Well, list of Wells, or "
                            "WellGroup.")

    Parameters
    ----------
    well : Well or WellGroup or list(Well)
        Parameter to validate is type Well, WellGroup, list of Wells.

    Returns
    -------
    bool
        Returns True if param is of type Well, WellGroup or list of type Well.
    """
    from autoprotocol.container import Well, WellGroup

    if not isinstance(well, (Well, WellGroup, list)):
        return False
    if isinstance(well, list):
        if not all(isinstance(well, Well) for well in well):
            return False
    return True


def parse_unit(unit, accepted_unit=None):
    """
    Parses and checks unit provided and ensures its of valid type and
    dimensionality.

    Note that this also checks against the dimensionality of the
    `accepted_unit`.
    I.e. `parse_unit("1:s", "minute")` will return True.

    Raises type errors if the Unit provided is invalid.

    Parameters
    ----------
    unit: Unit or str
        Input to be checked
    accepted_unit: Unit or str or list(Unit) or list(str), optional
        Dimensionality of unit should match against the accepted unit(s).

    Examples
    --------
    .. code-block:: python

        parse_unit("1:ul", "1:ml")
        parse_unit("1:ul", "ml")
        parse_unit("1:ul", ["ml", "kg"])

    Returns
    -------
    Unit
        Parsed and checked unit

    Raises
    ------
    TypeError
        Error when input does not match expected type or dimensionality
    """
    if not isinstance(unit, Unit):
        try:
            unit = Unit(unit)
        except (UnitStringError, UnitValueError):
            raise TypeError(f"{unit} is not of type Unit/str")
    if accepted_unit is not None:
        # Note: This is hacky. We should formalize the concept of base Units
        # in AP-Py
        def parse_base_unit(base_unit):
            if not isinstance(base_unit, Unit):
                if isinstance(base_unit, str):
                    if ":" not in base_unit:
                        base_unit = "1:" + base_unit
            return Unit(base_unit)

        if isinstance(accepted_unit, list):
            accepted_unit = [parse_base_unit(a_u) for a_u in accepted_unit]
        else:
            accepted_unit = [parse_base_unit(accepted_unit)]
        if all([unit.dimensionality != a_u.dimensionality for a_u in accepted_unit]):
            raise TypeError(
                f"{unit} is not of the expected dimensionality " f"{accepted_unit}"
            )

    return unit


def _validate_as_instance(item, target_type):
    """
    Validates that the item is an instance of the target_type and if not,
    checks whether the item is the

    Parameters
    ----------
    item : target_type
    target_type : type

    Returns
    -------
    target_type
        the item as an instance of the target type

    Raises
    ------
    TypeError
        if the passed item isn't either target_type or an instance thereof
    """
    if not isinstance(item, target_type):
        try:
            item = _validate_as_instance(item(), target_type)
        except:
            raise TypeError(f"{item} can't be parsed as a {target_type}.")
    return item


def _check_container_type_with_shape(container_type, shape):
    """
    Checks whether the selected origin and shape pair are valid

    Parameters
    ----------
    container_type : ContainerType
        the origin of the liquid handling operation. for multi channel
        operations this is the top left well of the stamp. for single channel
        operations this is the source well.
    shape : dict
        the shape of the transfer. used to determine the shape format of
        multichannel liquid handling operations
        see LiquidHandle.builders.shape

    Raises
    ------
    ValueError
        invalid combination of container and shape specified
    """
    from .instruction import Instruction

    shape = Instruction.builders.shape(**shape)
    format_rows = SBS_FORMAT_SHAPES[shape["format"]]["rows"]
    format_columns = SBS_FORMAT_SHAPES[shape["format"]]["columns"]

    is_single = shape["rows"] == shape["columns"] == 1

    if container_type.is_tube and not is_single:
        raise ValueError(
            f"Tube container_type {container_type} was specified with multi "
            f"channel transfer shape {shape}, but tubes only support single "
            f"channel liquid handling."
        )

    container_wells = container_type.well_count
    if container_wells == 24:
        rows_one_or_even = shape["rows"] == 1 or shape["rows"] % 2 == 0
        columns_one_or_even = shape["columns"] == 1 or shape["columns"] % 2 == 0
        if not (rows_one_or_even and columns_one_or_even):
            raise ValueError(
                f"24 well container_type {container_type.container_type} was "
                f"specified, but multi channel transfers in 24 well "
                f"containers must have row and column counts either equal to "
                f"1 or divisible by 2, but {shape} was specified."
            )

    if (
        shape["format"] == "SBS384"
        and container_wells < 384
        and "sbs384_compatible" not in container_type.capabilities
    ):
        raise ValueError(
            f"SBS384 transfers can only be executed in 384 well plates, but "
            f"container_type: {container_type} has {container_wells} wells."
            f"If the container_type is compatible with less than 384 wells, make sure to include: sbs384_compatible in the container_type's capabilities list"
        )

    # check for valid multi channel shapes
    max_rows = shape["rows"] == format_rows
    max_columns = shape["columns"] == format_columns
    is_full = max_rows and max_columns
    is_selective = (max_rows or max_columns) and not (max_rows and max_columns)

    if is_single or is_full:
        pass
    elif is_selective:
        if shape["format"] != "SBS96":
            raise ValueError(
                f"{shape['format']} formatted transfers require rows: "
                f"{format_rows} and columns: {format_columns}, but {shape} was "
                f"specified."
            )
    else:
        raise ValueError(
            f"Invalid transfer shape passed: only individual wells or full "
            f"rows/columns can be transferred. For {shape['format']} format "
            f"a full row consists of {format_columns} columns and a full "
            f"column consists of {format_rows} rows, but {shape} was specified."
        )
