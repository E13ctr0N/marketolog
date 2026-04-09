"""CSV formatting for tabular MCP tool responses.

Saves 40-60% of context tokens compared to JSON for tabular data.
"""

import csv
import io
import json


def _csv_quote(value: str) -> str:
    """Return a CSV-safe representation of a string cell.

    Wraps in double-quotes only when the value contains a comma or newline.
    Internal double-quotes in those cases are escaped as per RFC 4180.
    """
    if "," in value or "\n" in value or "\r" in value:
        return '"' + value.replace('"', '""') + '"'
    return value


def format_tabular(data: list[dict]) -> str:
    """Convert list of dicts to CSV string.

    - Header from keys of first dict
    - None → empty string
    - Nested dicts/lists → JSON-serialized into cell
    - Strings with commas → quoted
    """
    if not data:
        return ""

    fieldnames = list(data[0].keys())
    lines = []

    # Header row — field names are plain identifiers, safe to join directly
    lines.append(",".join(_csv_quote(str(f)) for f in fieldnames))

    for row in data:
        cells = []
        for key in fieldnames:
            value = row.get(key)
            if value is None:
                cells.append("")
            elif isinstance(value, (dict, list)):
                cells.append(_csv_quote(json.dumps(value, ensure_ascii=False)))
            else:
                cells.append(_csv_quote(str(value)))

        lines.append(",".join(cells))

    return "\n".join(lines) + "\n"
