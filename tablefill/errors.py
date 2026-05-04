"""Domain-specific exceptions and diagnostics for tablefill."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class DiagnosticContext:
    """Structured context attached to expected tablefill failures."""

    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    table: Optional[str] = None
    entry_index: Optional[int] = None
    placeholder: Optional[str] = None
    source: Optional[str] = None
    context: Optional[str] = None

    def format(self) -> str:
        fields = []
        if self.file and self.line is not None:
            fields.append("location=%s:%s" % (self.file, self.line))
        if self.file:
            fields.append("file=%s" % self.file)
        if self.line is not None:
            fields.append("line=%s" % self.line)
        if self.column is not None:
            fields.append("column=%s" % self.column)
        if self.table:
            fields.append("table=%s" % self.table)
        if self.entry_index is not None:
            fields.append("entry=%s" % self.entry_index)
        if self.placeholder:
            fields.append("placeholder=%r" % self.placeholder)
        if self.source:
            fields.append("source=%s" % self.source)
        if self.context:
            fields.append("context=%r" % self.context)
        return "; ".join(fields)


class TableFillError(Exception):
    """Base exception raised for expected tablefill failures."""

    code = "TABLEFILL_ERROR"

    def __init__(self, message, context=None, cause=None, code=None):
        super().__init__(message)
        self.message = message
        self.context = context
        self.cause = cause
        self.code = code or self.code

    def __str__(self):
        parts = ["[%s] %s" % (self.code, self.message)]
        if self.context:
            details = self.context.format()
            if details:
                parts.append("Details: %s" % details)
        if self.cause:
            parts.append("Cause: %s" % self.cause)
        return "\n".join(parts)


class InputParseError(TableFillError):
    """Raised when an input table file cannot be parsed safely."""

    code = "INPUT_PARSE_ERROR"


class PlaceholderError(TableFillError):
    """Raised when a placeholder cannot be formatted or replaced."""

    code = "PLACEHOLDER_ERROR"


class TemplateScanError(TableFillError):
    """Raised when the template structure cannot be scanned safely."""

    code = "TEMPLATE_SCAN_ERROR"
