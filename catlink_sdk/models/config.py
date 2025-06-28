"""Configuration models for CatLink SDK."""

from typing import Optional
from dataclasses import dataclass


@dataclass
class AdditionalDeviceConfig:
    """Additional configuration for CatLink devices."""
    
    name: str = ""
    mac: str = ""
    empty_weight: float = 0.0
    max_samples_litter: int = 24
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.empty_weight < 0:
            self.empty_weight = 0.0
        if self.max_samples_litter < 1:
            self.max_samples_litter = 24