def strptime_format_to_iso_8601_template(strptime_format: str) -> str:
    """
    Convert a strptime-formatted string to an ISO 8601 template.

    :param strptime_format: A strptime-formatted string to convert.
    :return: An ISO 8601 template.
    """

    fmt = {"%Y": "YYYY", "%m": "MM", "%d": "DD", "%H": "HH", "%M": "MM", "%S": "SS"}
    readable = strptime_format
    for old, new in fmt.items():
        readable = readable.replace(old, new)
    return readable
