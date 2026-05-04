"""StableFill public API.

The historical implementation package is still named ``tablefill`` for
backwards compatibility, but new code can import from ``stablefill``.
"""

from tablefill import (
    DiagnosticContext,
    InputParseError,
    PlaceholderError,
    TableFillError,
    TemplateScanError,
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
]
