"""Feeder device model for CatLink SDK."""

import datetime
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import logging

from .device import Device
from .config import AdditionalDeviceConfig
from ..constants import API_FEEDER_DETAIL

if TYPE_CHECKING:
    from ..auth import CatLinkAuth

_LOGGER = logging.getLogger(__name__)


class FeederDevice(Device):
    """Feeder device class."""

    def __init__(self, data: Dict[str, Any], auth: "CatLinkAuth", config: Optional[AdditionalDeviceConfig] = None):
        """Initialize the feeder device."""
        super().__init__(data, auth, config)
        self.logs: List[Dict[str, Any]] = []

    async def async_init(self) -> None:
        """Initialize the feeder device asynchronously."""
        await super().async_init()
        await self.update_logs()

    @property
    def weight(self) -> Optional[int]:
        """Return the food weight in grams."""
        return self.detail.get("weight")

    @property
    def error(self) -> Optional[str]:
        """Return the error message."""
        return self.detail.get("error")

    @property
    def state(self) -> Optional[str]:
        """Return the food output status."""
        return self.detail.get("foodOutStatus")

    @property
    def last_log(self) -> Optional[str]:
        """Return the last log entry."""
        if self.logs:
            log = self.logs[0]
            parts = [
                log.get('time', ''),
                log.get('event', ''),
                log.get('firstSection', ''),
                log.get('secondSection', '')
            ]
            return ' '.join(filter(None, parts))
        return None

    def get_attributes(self) -> Dict[str, Any]:
        """Return all device attributes."""
        attrs = super().get_attributes()
        attrs.update({
            "weight": self.weight,
            "food_out_status": self.detail.get("foodOutStatus"),
            "auto_fill_status": self.detail.get("autoFillStatus"),
            "indicator_light_status": self.detail.get("indicatorLightStatus"),
            "breath_light_status": self.detail.get("breathLightStatus"),
            "power_supply_status": self.detail.get("powerSupplyStatus"),
            "key_lock_status": self.detail.get("keyLockStatus"),
            "current_error_message": self.detail.get("currentErrorMessage"),
            "current_error_type": self.detail.get("currentErrorType"),
            "last_log": self.last_log,
        })
        return attrs

    async def update_device_detail(self) -> Dict[str, Any]:
        """Update device details."""
        params = {"deviceId": self.id}
        
        try:
            response = await self.auth.request(API_FEEDER_DETAIL, params)
            device_info = response.get("data", {}).get("deviceInfo", {})
            
            if device_info:
                self.detail = device_info
                self._notify_listeners()
                return device_info
            else:
                _LOGGER.warning("No device info in response: %s", response)
                return {}
        except Exception as e:
            _LOGGER.error("Failed to update device detail for %s: %s", self.name, e)
            return {}

    async def update_logs(self) -> List[Dict[str, Any]]:
        """Update feeding logs."""
        params = {"deviceId": self.id}
        
        try:
            response = await self.auth.request("token/device/feeder/stats/log/top5", params)
            logs = response.get("data", {}).get("feederLogTop5", [])
            
            if logs:
                self.logs = logs
                self._notify_listeners()
                return logs
            else:
                _LOGGER.debug("No logs in response: %s", response)
                return []
        except Exception as e:
            _LOGGER.warning("Failed to update logs for %s: %s", self.name, e)
            return []

    async def dispense_food(self, amount: int = 5) -> bool:
        """Dispense food from the feeder."""
        params = {
            "footOutNum": amount,
            "deviceId": self.id,
        }
        
        response = await self.auth.request("token/device/feeder/foodOut", params, "POST")
        if response.get("returnCode", 0) != 0:
            _LOGGER.error("Failed to dispense food: %s", response)
            return False
        
        await self.update_device_detail()
        _LOGGER.info("Food dispensed successfully: %d grams", amount)
        return True

    def get_feeding_logs(self) -> List[Dict[str, Any]]:
        """Get feeding logs."""
        return self.logs.copy()