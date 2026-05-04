"""StableFill public API.

New code should import from ``stablefill``. The historical ``tablefill``
package remains available as a compatibility alias.
"""

__author__ = "Mauricio Caceres Bravo"
__email__ = "mauricio.caceres.bravo@gmail.com"
__version__ = "0.11.0"

from .errors import (
    DiagnosticContext,
    InputParseError,
    PlaceholderError,
    TableFillError,
    TemplateScanError,
)
from .tablefill import (
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
