"""LaTeX-oriented rendering helpers."""

from __future__ import annotations

import re


class LatexRenderer:
    """Escape replacement text for TeX-like output formats."""

    escape_pattern = re.compile(r"(?<!\\)(%|&)")

    def escape_text(self, value: str) -> str:
        return self.escape_pattern.sub(r"\\\1", value)


def renderer_for_filetype(filetype: str) -> LatexRenderer:
    """Return the renderer for a template type.

    StableFill historically escaped TeX-sensitive ``%`` and ``&`` replacement
    values for every supported template type. The renderer factory keeps that
    behavior centralized while making it explicit.
    """

    return LatexRenderer()
