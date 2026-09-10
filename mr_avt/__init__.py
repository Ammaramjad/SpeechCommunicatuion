"""Multi-Resolution Audio--Visual Transformer (MR-AVT) for speech emotion recognition."""

from .config import MRAVTConfig
from .models.mr_avt import MRAVT

__all__ = ["MRAVT", "MRAVTConfig"]
__version__ = "1.0.0"
