"""CatLink SDK - Python SDK for CatLink smart pet devices."""

from .client import CatLinkClient
from .auth import CatLinkAuth
from .models import Device, LitterBox, FeederDevice, ScooperDevice, AdditionalDeviceConfig
from .constants import (
    DEVICE_TYPE_SCOOPER,
    DEVICE_TYPE_LITTER_BOX_599,
    DEVICE_TYPE_FEEDER,
    DEVICE_TYPE_WATER_FOUNTAIN,
    MODE_AUTO,
    MODE_MANUAL,
    MODE_TIME,
    ACTION_START,
    ACTION_PAUSE,
    ACTION_CLEAN,
    STATE_IDLE,
    STATE_RUNNING,
    STATE_NEED_RESET,
    WORK_STATUS_IDLE,
    WORK_STATUS_RUNNING,
    WORK_STATUS_NEED_RESET,
)

__version__ = "0.1.0"

__all__ = [
    "CatLinkClient",
    "CatLinkAuth",
    "Device",
    "LitterBox",
    "FeederDevice",
    "ScooperDevice",
    "AdditionalDeviceConfig",
    "DEVICE_TYPE_SCOOPER",
    "DEVICE_TYPE_LITTER_BOX_599",
    "DEVICE_TYPE_FEEDER",
    "DEVICE_TYPE_WATER_FOUNTAIN",
    "MODE_AUTO",
    "MODE_MANUAL",
    "MODE_TIME",
    "ACTION_START",
    "ACTION_PAUSE",
    "ACTION_CLEAN",
    "STATE_IDLE",
    "STATE_RUNNING",
    "STATE_NEED_RESET",
    "WORK_STATUS_IDLE",
    "WORK_STATUS_RUNNING",
    "WORK_STATUS_NEED_RESET",
]