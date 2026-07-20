def sizeof_fmt(
    num: float,
    iec: bool = True,
    separator: str = "",
    precision: int = 2,
    sign: bool = False,
) -> str:
    """Formats the given number using either decimal or binary units.

    Arguments:
        num: The number to be formatted.
        iec: If true use binary units, decimal otherwise. Defaults to True.
        separator: Separator between formatted number and unit. Defaults to "".
        precision: Precision to use when rounding the number. Defaults to 2.
        sign: If true, adds a plus sign to positive numbers. Defaults to False.

    Returns:
        A string with the formatted number.
    """
    suffix = "B"
    if iec:
        power = 1024
        units = ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi", "Yi"]
    else:
        power = 1000
        units = ["", "k", "M", "G", "T", "P", "E", "Z", "Y"]

    plus = "+" if sign and num > 0 else ""
    fmt = "{0:{1}.{2}f}{3}{4}{5}"
    prec = 0
    for unit in units[:-1]:  # noqa
        if abs(round(num, precision)) < power:
            break
        num /= float(power)
        prec = precision
    else:
        unit = units[-1]
    return fmt.format(num, plus, prec, separator, unit, suffix)
