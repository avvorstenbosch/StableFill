"""Input-file parsing helpers.

The historical parser only split rows on tabs. That remains the first
choice for backwards compatibility, but modern workflows often save
plain whitespace-delimited regression output. This module accepts both
while preserving quoted single-cell text used by older examples.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
import shlex
from typing import Dict, Iterable, List, Sequence

try:
    from .errors import InputParseError
except ImportError:
    from errors import InputParseError


TAG_RE = re.compile(
    r"^\s*<\s*(?P<kind>tab|table|val|value|scalar|stat)\s*:\s*(?P<name>[^>]+?)\s*>\s*$",
    re.IGNORECASE,
)
ESTIMATE_RE = re.compile(
    r"^[+-]?(?:\d+(?:,\d{3})*|\d*\.\d+|\d+)(?:\.\d+)?(?:e[+-]?\d+)?(?:[*]+)?$",
    re.IGNORECASE,
)
PARENTHESIZED_NUMBER_RE = re.compile(
    r"^\([+-]?(?:\d+(?:,\d{3})*|\d*\.\d+|\d+)(?:\.\d+)?(?:e[+-]?\d+)?(?:[*]+)?\)$",
    re.IGNORECASE,
)


@dataclass
class ParsedInputs:
    """Parsed table and scalar-value blocks from one or more files."""

    tables: Dict[str, List[List[str]]] = field(default_factory=dict)
    values: Dict[str, str] = field(default_factory=dict)
    sources: Dict[str, str] = field(default_factory=dict)


def normalize_key(name: str) -> str:
    """Normalize table/value names the same way template labels are matched."""

    key = name.strip().strip("{}\"'").lower()
    for prefix in ("tab:", "table:", "val:", "value:", "scalar:", "stat:"):
        if key.startswith(prefix):
            return key[len(prefix) :]
    return key


def parse_input_files(filenames: Sequence[str], missing_values: Iterable[str]) -> ParsedInputs:
    """Parse tablefill input files into table and named-value dictionaries.

    Args:
        filenames: Input text files to parse, in precedence order.
        missing_values: Tokens that should be ignored when selecting scalar
            values.

    Raises:
        InputParseError: If a data row appears before the first block label.
    """

    parsed = ParsedInputs()
    missing = set(missing_values)
    current_kind = None
    current_key = None
    value_rows: Dict[str, List[List[str]]] = {}

    for filename in filenames:
        with open(filename, "r", newline=None) as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.rstrip("\r\n")
                if not line.strip():
                    continue

                tag = TAG_RE.match(line)
                if tag:
                    current_kind = tag.group("kind").lower()
                    current_key = normalize_key(tag.group("name"))
                    parsed.sources[current_key] = "%s:%d" % (filename, line_number)
                    if current_kind in ("tab", "table"):
                        parsed.tables[current_key] = []
                    else:
                        value_rows[current_key] = []
                    continue

                if current_key is None:
                    message = (
                        "Could not parse input row before any <Tab:...> or "
                        "<Val:...> label at %s:%d: %r"
                    )
                    raise InputParseError(message % (filename, line_number, line.strip()))

                entries = split_input_row(line)
                if current_kind in ("tab", "table"):
                    parsed.tables[current_key].append(entries)
                else:
                    value_rows[current_key].append(entries)

    for key, rows in value_rows.items():
        flat = [entry for row in rows for entry in row]
        usable = [entry for entry in flat if entry not in missing]
        parsed.values[key] = usable[0] if usable else ""

    return parsed


def split_input_row(line: str) -> List[str]:
    """Split one row of an input block into cells.

    Tab-delimited rows use tabs exactly as before. Rows without tabs are split
    with shell-style quoting, except a whole quoted line is kept as one value
    so old examples like ``'tablefill example'`` keep their literal quotes.
    """

    if "\t" in line:
        return [entry.strip() for entry in line.split("\t")]

    stripped = line.strip()
    if _is_whole_quoted_value(stripped):
        return [stripped]

    try:
        entries = shlex.split(stripped, posix=False)
    except ValueError as exc:
        raise InputParseError("Could not split input row %r: %s" % (stripped, exc))

    return combine_adjacent_standard_errors([entry.strip() for entry in entries])


def combine_adjacent_standard_errors(entries: Sequence[str]) -> List[str]:
    """Keep ``estimate (standard error)`` pairs in one logical cell.

    Economics regression tables commonly report estimates and standard errors
    side by side within a model column, for example ``0.125*** (0.031)``. When
    parsing whitespace-delimited input, that pair should occupy one placeholder.
    Rows that consist only of standard errors, such as ``(0.031) (0.100)``, are
    intentionally left as separate cells.
    """

    combined: List[str] = []
    i = 0
    while i < len(entries):
        entry = entries[i]
        next_entry = entries[i + 1] if i + 1 < len(entries) else None
        if next_entry and ESTIMATE_RE.match(entry) and PARENTHESIZED_NUMBER_RE.match(next_entry):
            combined.append("%s %s" % (entry, next_entry))
            i += 2
        else:
            combined.append(entry)
            i += 1

    return combined


def _is_whole_quoted_value(value: str) -> bool:
    if len(value) < 2:
        return False
    quote = value[0]
    if quote not in ("'", '"') or value[-1] != quote:
        return False
    return value.count(quote) == 2
