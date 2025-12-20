import importlib.metadata as _metadata
from typing import Final

__version__: Final = _metadata.version(__package__ or __file__.split("/")[-1])
VERSION: Final = __version__
