"""Inline named-value placeholder support."""

from __future__ import annotations

import re
from typing import Callable, Dict, Iterable, List, Optional, Tuple

try:
    from .parsers import normalize_key
except ImportError:
    from parsers import normalize_key


ANNOTATION_RE = r"\[\[SF:.*?\]\]"
INLINE_RE = re.compile(
    r"(?P<placeholder>\{\{\s*(?P<name>[^{}|]+?)\s*(?:\|\s*(?P<format>[^{}]+?)\s*)?\}\})"
    r"(?P<annotation>%s)?" % ANNOTATION_RE
)


def make_annotation(value: str) -> str:
    return "[[SF: %s]]" % value.replace("]]", "] ]")


def strip_annotations(text: str) -> str:
    return re.sub(ANNOTATION_RE, "", text)


def replace_inline_placeholders(
    lines: Iterable[str],
    values: Dict[str, str],
    renderer: Callable[[str, Optional[str]], str],
    annotate: bool = False,
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
            raw_key = match.group("name")
            key = normalize_key(raw_key)
            format_spec = match.group("format").strip() if match.group("format") else None
            if key not in values:
                warning = (
                    "line %d: inline placeholder %r has no matching input "
                    "value. Available keys: %s"
                )
                warnings.append(warning % (line_number, match.group(0), available or "(none)"))
                return match.group(0)
            rendered = renderer(values[key], format_spec)
            if annotate:
                return match.group("placeholder") + make_annotation(rendered)
            return rendered

        rendered_lines.append(INLINE_RE.sub(replace, line))

    return rendered_lines, warnings
