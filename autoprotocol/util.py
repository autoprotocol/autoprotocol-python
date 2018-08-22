"""
Module containing utility functions

    :copyright: 2018 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""

from math import ceil, floor
from itertools import repeat
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
            raise TypeError("{} is not of type Unit/str".format(unit))
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
        if all([unit.dimensionality != a_u.dimensionality for a_u in
                accepted_unit]):
            raise TypeError("{} is not of the expected dimensionality "
                            "{}".format(unit, accepted_unit))

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
            raise TypeError(
                "{} can't be parsed as a {}.".format(item, target_type)
            )
    return item


def _get_wells(origin, shape):
    """
    Returns the wells interacted with by a transfer depending on its origin
    and its shape

    Parameters
    ----------
    origin : Well
        the origin Well (the top-left-most well) for the transfer
    shape : dict
        the shape of the transfer
        See Also LiquidHandle.builders.shape

    Returns
    -------
    WellGroup
        all of the wells being interacted with by the transfer

    Raises
    ------
    ValueError
        if row or column counts exceed the extents of the plate
    """
    from .container import WellGroup
    from .instruction import LiquidHandle

    # validating shape
    shape = LiquidHandle.builders.shape(**shape)

    # unpacking container and shape format properties
    container = origin.container
    container_rows = container.container_type.row_count()
    container_columns = container.container_type.col_count
    format_rows = SBS_FORMAT_SHAPES[shape["format"]]["rows"]
    format_columns = SBS_FORMAT_SHAPES[shape["format"]]["columns"]

    # ratios of tip shape to container well shape
    row_ratio = container_rows / format_rows
    column_ratio = container_columns / format_columns

    # get the origins well position
    origin_row, origin_column = origin.container.decompose(origin)

    # the total row/column span of the head of tips
    tip_row_span = floor((shape["rows"] - 1) * row_ratio) + 1
    tip_column_span = floor((shape["columns"] - 1) * column_ratio) + 1

    # validating origin and shape against container shape
    if origin_row + tip_row_span > container_rows:
        raise ValueError(
            "Specified shape {} with origin {} exceeds the row count {} of "
            "container_type {}."
            "".format(shape, origin, container_rows, container)
        )

    if origin_column + tip_column_span > container_columns:
        raise ValueError(
            "Specified shape {} with origin {} exceeds the column count {} of "
            "container_type {}."
            "".format(shape, origin, container_columns, container)
        )

    # get the column origins for the operation
    column_origins = container.wells_from(
        origin, int(tip_column_span)
    )[::int(max(column_ratio, 1))]

    # get the whole columns for the operation
    columns = [
        WellGroup(container.wells_from(
            _, int(tip_row_span), columnwise=True
        )[::int(max(row_ratio, 1))])
        for _ in column_origins
    ]

    # we currently don't support summing lists of WellGroups
    wells = WellGroup([])
    for column in columns:
        wells += column

    # the number of tips entering each well of the container
    rowwise_tips_per_well = min(
        [shape["rows"], int(ceil(format_rows / container_rows))])
    columnwise_tips_per_well = min(
        [shape["columns"], int(ceil(format_columns / container_columns))])
    tips_per_well = int(columnwise_tips_per_well * rowwise_tips_per_well)

    # repeating each well for each tip that enters it
    repeated_wells = WellGroup(
        [well for item in wells for well in repeat(item, tips_per_well)])

    return repeated_wells


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
    from .instruction import LiquidHandle

    shape = LiquidHandle.builders.shape(**shape)
    format_rows = SBS_FORMAT_SHAPES[shape["format"]]["rows"]
    format_columns = SBS_FORMAT_SHAPES[shape["format"]]["columns"]

    is_single = shape["rows"] == shape["columns"] == 1

    if container_type.is_tube and not is_single:
        raise ValueError(
            "Tube container_type {} was specified with multi channel transfer "
            "shape {}, but tubes only support single channel liquid handling."
            "".format(container_type, shape)
        )

    container_wells = container_type.well_count
    if container_wells == 24:
        rows_one_or_even = (
            shape["rows"] == 1 or shape["rows"] % 2 == 0
        )
        columns_one_or_even = (
            shape["columns"] == 1 or shape["columns"] % 2 == 0
        )
        if not (rows_one_or_even and columns_one_or_even):
            raise ValueError(
                "24 well container_type {} was specified, but multi channel "
                "transfers in 24 well containers must have row and "
                "column counts either equal to 1 or divisible by 2, but "
                "{} was specified."
                "".format(
                    container_type.container_type, shape
                )
            )

    if shape["format"] == "SBS384" and container_wells < 384:
        raise ValueError(
            "SBS384 transfers can only be executed in 384 well plates, but "
            "container_type: {} has {} wells."
            "".format(container_type, container_wells)
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
                "{} formatted transfers require rows: {} and columns: {}, "
                "but {} was specified."
                "".format(
                    shape["format"], format_rows, format_columns, shape
                )
            )
    else:
        raise ValueError(
            "Invalid transfer shape passed: only individual wells or "
            "full rows/columns can be transferred. For {} format "
            "a full row consists of {} columns and a full column consists "
            "of {} rows, but {} was specified."
            "".format(
                shape["format"], format_columns, format_rows, shape
            )
        )
