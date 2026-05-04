"""Compatibility package for the historical ``tablefill`` import path."""

from stablefill import (
    DiagnosticContext,
    InputParseError,
    PlaceholderError,
    TableFillError,
    TemplateScanError,
    __author__,
    __email__,
    __version__,
    main,
    stablefill,
    tablefill,
)

__all__ = [
    'DiagnosticContext',
    'InputParseError',
    'PlaceholderError',
    'TableFillError',
    'TemplateScanError',
    'main',
    'stablefill',
    'tablefill',
    '__author__',
    '__email__',
    '__version__',
]
