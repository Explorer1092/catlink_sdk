"""CatLink SDK models."""

from .device import Device
from .litterbox import LitterBox
from .feeder import FeederDevice
from .scooper import ScooperDevice
from .config import AdditionalDeviceConfig

__all__ = ["Device", "LitterBox", "FeederDevice", "ScooperDevice", "AdditionalDeviceConfig"]