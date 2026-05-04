"""Explicit template grammar and scanner helpers."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Optional

try:
    from .errors import DiagnosticContext, TemplateScanError
except ImportError:
    from errors import DiagnosticContext, TemplateScanError


@dataclass
class TemplateGrammar:
    """Regular-expression grammar for one template family."""

    begin: str
    end: str
    label: str
    comment: str


@dataclass
class LabelSearchResult:
    """Result of scanning forward from a table start marker."""

    matched: bool
    tag: str
    label_line: Optional[int]
    end_line: Optional[int]


def grammar_for_filetype(filetype: str) -> TemplateGrammar:
    """Return the explicit fill grammar for ``tex``, ``lyx``, or ``md``."""

    grammars = {
        'tex': TemplateGrammar(
            begin=r'(^\s*%\s*tablefill:start\s+tab:.+$)|(.*\\begin{(sub)?table}.*)',
            end=r'(^\s*%\s*tablefill:end.*$)|(.*\\end{(sub)?table}.*)',
            label=r'(?:^\s*%\s*tablefill:start\s+|.*\\label{)tab:(.+?)(?:}|\b)',
            comment=r'^\s*%',
        ),
        'lyx': TemplateGrammar(
            begin=r'.*\\begin_inset Float table.*',
            end=r'</lyxtabular>',
            label=r'name "tab:(.+)"',
            comment=r'^\s*%',
        ),
        'md': TemplateGrammar(
            begin=r'(^<!--.*tablefill:start.*-->$)|(^\s*\\begin{table}.*)',
            end=r'(^<!--.*tablefill:end.*-->$)|(.*\\end{table}.*)',
            label=r'(?:^<!--.*\b|.*\\label{)tab:(.+)(?:\b.*-->$|})',
            comment=r'^\s*<!--',
        ),
    }
    try:
        return grammars[filetype]
    except KeyError:
        raise KeyError("Unknown template filetype %r" % filetype)


class TemplateScanner:
    """Classify template lines according to the StableFill grammar."""

    def __init__(self, grammar: TemplateGrammar, template: Optional[str] = None):
        self.grammar = grammar
        self.template = template

    def is_table_start(self, line: str) -> bool:
        return bool(re.search(self.grammar.begin, line))

    def is_table_end(self, line: str) -> bool:
        return bool(re.search(self.grammar.end, line))

    def is_comment(self, line: str) -> bool:
        return bool(re.search(self.grammar.comment, line.strip()))

    def extract_label(self, line: str) -> Optional[str]:
        match = re.search(self.grammar.label, line, flags=re.IGNORECASE)
        if not match:
            return None
        label = match.group(1)
        return label.strip('{}"').lower()

    def has_placeholder(self, line: str, placeholder_patterns: Iterable[str]) -> bool:
        return any(re.search(pattern, line) for pattern in placeholder_patterns)

    def search_label(self, lines, start: int, table_keys) -> LabelSearchResult:
        """Search for a table label between a table start and end marker."""

        line_count = len(lines)
        for index in range(start, line_count):
            line = lines[index]
            label = self.extract_label(line)
            if label:
                return LabelSearchResult(label in table_keys, label, index + 1, None)
            if self.is_table_end(line):
                return LabelSearchResult(False, '', None, index + 1)

        context = DiagnosticContext(
            file=self.template,
            line=start + 1,
            context=lines[start].rstrip('\r\n') if start < line_count else None,
        )
        message = (
            "Found a table/tablefill start but could not find a matching "
            "label or end marker before EOF."
        )
        raise TemplateScanError(message, context=context)
