"""Domain-specific exceptions for tablefill."""


class TableFillError(Exception):
    """Base exception raised for expected tablefill failures."""


class InputParseError(TableFillError):
    """Raised when an input table file cannot be parsed safely."""


class PlaceholderError(TableFillError):
    """Raised when a placeholder cannot be formatted or replaced."""
