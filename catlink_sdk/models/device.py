"""Base device model for CatLink SDK."""

from typing import Dict, Optional, Any, TYPE_CHECKING
import logging

from ..constants import (
    API_DEVICE_INFO,
    API_DEVICE_CHANGE_MODE,
    API_DEVICE_ACTION,
)
from .config import AdditionalDeviceConfig

if TYPE_CHECKING:
    from ..auth import CatLinkAuth

_LOGGER = logging.getLogger(__name__)


class Device:
    """Base device class for CatLink devices."""

    def __init__(self, data: Dict[str, Any], auth: "CatLinkAuth", config: Optional[AdditionalDeviceConfig] = None):
        """Initialize the device."""
        self.data = data
        self.auth = auth
        self.config = config or AdditionalDeviceConfig()
        self.detail: Dict[str, Any] = {}
        self._listeners = []

    async def async_init(self) -> None:
        """Initialize the device asynchronously."""
        await self.update_device_detail()

    def update_data(self, data: Dict[str, Any]) -> None:
        """Update device data."""
        self.data = data
        self._notify_listeners()
        _LOGGER.info("Updated device data: %s", data)

    def _notify_listeners(self):
        """Notify all listeners of data changes."""
        for listener in self._listeners:
            try:
                listener()
            except Exception as e:
                _LOGGER.error("Error notifying listener: %s", e)

    def add_listener(self, callback):
        """Add a listener for data changes."""
        self._listeners.append(callback)

    def remove_listener(self, callback):
        """Remove a listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    @property
    def id(self) -> Optional[str]:
        """Return the device ID."""
        # Try both 'id' and 'deviceId' for compatibility
        return self.detail.get("deviceId") or self.data.get("id") or self.data.get("deviceId")

    @property
    def mac(self) -> Optional[str]:
        """Return the device MAC address."""
        return self.data.get("mac")

    @property
    def model(self) -> Optional[str]:
        """Return the device model."""
        return self.data.get("model")

    @property
    def type(self) -> Optional[str]:
        """Return the device type."""
        return self.data.get("deviceType")

    @property
    def name(self) -> str:
        """Return the device name."""
        return self.data.get("deviceName", "")

    @property
    def error(self) -> Optional[str]:
        """Return the device error message."""
        return self.detail.get("currentMessage") or self.data.get("currentErrorMessage")

    @property
    def state(self) -> str:
        """Return the device state."""
        try:
            status = self.detail.get("workStatus", "")
            state_map = {
                "00": "idle",
                "01": "running",
                "02": "need_reset",
            }
            return state_map.get(str(status).strip(), status)
        except Exception as e:
            _LOGGER.error("Get device state failed: %s", e)
            return "unknown"

    @property
    def mode(self) -> Optional[str]:
        """Return the current device mode."""
        mode_key = self.detail.get("workModel")
        return self.modes.get(mode_key)

    @property
    def modes(self) -> Dict[str, str]:
        """Return available device modes."""
        return {}

    @property
    def action(self) -> Optional[str]:
        """Return the current device action."""
        return None

    @property
    def online(self) -> bool:
        """Return whether the device is online."""
        try:
            return self.detail.get("online", False)
        except Exception:
            return False

    @property
    def actions(self) -> Dict[str, str]:
        """Return available device actions."""
        return {}

    def get_attributes(self) -> Dict[str, Any]:
        """Return device attributes."""
        return {
            "id": self.id,
            "mac": self.mac,
            "model": self.model,
            "type": self.type,
            "name": self.name,
            "state": self.state,
            "mode": self.mode,
            "error": self.error,
            "work_status": self.detail.get("workStatus"),
            "alarm_status": self.detail.get("alarmStatus"),
            "atmosphere_status": self.detail.get("atmosphereStatus"),
            "temperature": self.detail.get("temperature"),
            "humidity": self.detail.get("humidity"),
            "weight": self.detail.get("weight"),
            "key_lock": self.detail.get("keyLock"),
            "safe_time": self.detail.get("safeTime"),
            "pave_second": self.detail.get("catLitterPaveSecond"),
        }

    async def set_mode(self, mode: str) -> bool:
        """Set the device mode."""
        mode_key = None
        for k, v in self.modes.items():
            if v == mode:
                mode_key = k
                break
        
        if mode_key is None:
            _LOGGER.warning("Invalid mode %s. Available modes: %s", mode, self.modes)
            return False
        
        params = {
            "workModel": mode_key,
            "deviceId": self.id,
        }
        
        response = await self.auth.request(API_DEVICE_CHANGE_MODE, params, "POST")
        if response.get("returnCode", 0) != 0:
            _LOGGER.error("Failed to set mode: %s", response)
            return False
        
        await self.update_device_detail()
        _LOGGER.info("Mode set successfully: %s", mode)
        return True

    async def execute_action(self, action: str) -> bool:
        """Execute a device action."""
        action_key = None
        for k, v in self.actions.items():
            if v == action:
                action_key = k
                break
        
        if action_key is None:
            _LOGGER.warning("Invalid action %s. Available actions: %s", action, self.actions)
            return False
        
        params = {
            "cmd": action_key,
            "deviceId": self.id,
        }
        
        response = await self.auth.request(API_DEVICE_ACTION, params, "POST")
        if response.get("returnCode", 0) != 0:
            _LOGGER.error("Failed to execute action: %s", response)
            return False
        
        await self.update_device_detail()
        _LOGGER.info("Action executed successfully: %s", action)
        return True

    async def update_device_detail(self) -> Dict[str, Any]:
        """Update device details."""
        params = {"deviceId": self.id}
        
        try:
            response = await self.auth.request(API_DEVICE_INFO, params)
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