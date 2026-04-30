"""Inline named-value placeholder support."""

from __future__ import annotations

import re
from typing import Callable, Dict, Iterable, List, Optional, Tuple

try:
    from .parsers import normalize_key
except ImportError:
    from parsers import normalize_key


INLINE_RE = re.compile(r"\{\{\s*([^{}|]+?)\s*(?:\|\s*([^{}]+?)\s*)?\}\}")


def replace_inline_placeholders(
    lines: Iterable[str],
    values: Dict[str, str],
    renderer: Callable[[str, Optional[str]], str],
) -> Tuple[List[str], List[str]]:
    """Replace ``{{name}}`` placeholders anywhere in template lines.

    ``{{name|,.0f}}`` passes ``,.0f`` to the caller-provided renderer. Missing
    keys are left in place and returned as warning strings with 1-based line
    numbers.
    """

    available = ", ".join(sorted(values.keys()))
    warnings: List[str] = []
    rendered_lines: List[str] = []

    for line_number, line in enumerate(lines, start=1):

        def replace(match: re.Match[str]) -> str:
            raw_key = match.group(1)
            key = normalize_key(raw_key)
            format_spec = match.group(2).strip() if match.group(2) else None
            if key not in values:
                warning = (
                    "line %d: inline placeholder %r has no matching input "
                    "value. Available keys: %s"
                )
                warnings.append(warning % (line_number, match.group(0), available or "(none)"))
                return match.group(0)
            return renderer(values[key], format_spec)

        rendered_lines.append(INLINE_RE.sub(replace, line))

    return rendered_lines, warnings
