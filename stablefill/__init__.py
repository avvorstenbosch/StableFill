"""StableFill public API.

New code should import from ``stablefill``. The historical ``tablefill``
package remains available as a compatibility alias.
"""

__author__ = "Mauricio Caceres Bravo"
__email__ = "mauricio.caceres.bravo@gmail.com"
__version__ = "0.13.0"

from .errors import (
    DiagnosticContext,
    InputParseError,
    PlaceholderError,
    TableFillError,
    TemplateScanError,
)
from .tablefill import (
    inspect_stablefill,
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
    'inspect_stablefill',
    'main',
    'stablefill',
    'tablefill',
]
