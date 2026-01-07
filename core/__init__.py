"""Core business logic modules for video downloader pipeline."""

from .auth_manager import AuthManager
from .downloader import Downloader

# Optional imports - these modules may not exist yet
try:
    from .transcriber import Transcriber
except ImportError:
    Transcriber = None

try:
    from .analyzer import Analyzer
except ImportError:
    Analyzer = None

try:
    from .pipeline import Pipeline
except ImportError:
    Pipeline = None

__all__ = ['AuthManager', 'Downloader']
if Transcriber:
    __all__.append('Transcriber')
if Analyzer:
    __all__.append('Analyzer')
if Pipeline:
    __all__.append('Pipeline')
