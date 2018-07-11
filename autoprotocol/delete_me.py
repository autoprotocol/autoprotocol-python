"""
Temporary file for missing deps that will be fixed once liquid handle fixes are in
"""
# pragma pylint:disable=all

_SUPPORTED_SHAPES = ["SBS96", "SBS384"]

def shape_builder(rows=1, columns=1, format="SBS96"):
    """
    Helper function for building a shape dictionary

    Parameters
    ----------
    rows: Int, optional
        Number of rows to be concurrently transferred
    columns: Int, optional
        Number of columns to be concurrently transferred
    format: String, optional
        Plate format in String form. Example formats are "SBS96" and "SBS384"
    Returns
    -------
    Shape parameters: Dictionary
    """
    if format is None:
        if 9 <= rows <= 16 or 13 <= columns <= 24:
            format = "SBS384"
        elif 1 <= rows <= 8 and 1 <= columns <= 12:
            format = "SBS96"
        else:
            raise ValueError("Invalid number of rows and/or columns specified")

    if not isinstance(rows, int) or not isinstance(columns, int):
        raise TypeError("Rows/columns have to be of type integer")
    if format not in _SUPPORTED_SHAPES:
        raise ValueError("Invalid shape given. Shape has to be in {}".format(
            _SUPPORTED_SHAPES
        ))
    if (format == "SBS96" and (rows > 8 or columns > 12) or
            format == "SBS384" and (rows > 16 or columns > 24)):
        raise ValueError("Number of rows/columns exceed the defined format")

    arg_list = list(locals().items())
    arg_dict = {k: v for k, v in arg_list if v}
    return arg_dict
