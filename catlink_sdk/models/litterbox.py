"""Litter box model for CatLink SDK."""

from collections import deque
import datetime
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import logging

from .device import Device
from .config import AdditionalDeviceConfig
from ..constants import MODE_AUTO, MODE_MANUAL, MODE_TIME

if TYPE_CHECKING:
    from ..auth import CatLinkAuth

_LOGGER = logging.getLogger(__name__)


class LitterBox(Device):
    """Litter box device class."""

    def __init__(self, data: Dict[str, Any], auth: "CatLinkAuth", config: Optional[AdditionalDeviceConfig] = None):
        """Initialize the litter box."""
        super().__init__(data, auth, config)
        self.logs: List[Dict[str, Any]] = []
        self._litter_weight_during_day = deque(maxlen=self.config.max_samples_litter)
        self.empty_litter_box_weight = self.config.empty_weight

    async def async_init(self) -> None:
        """Initialize the litter box asynchronously."""
        await super().async_init()
        await self.update_logs()

    @property
    def modes(self) -> Dict[str, str]:
        """Return available modes."""
        return {
            "00": MODE_AUTO,
            "01": MODE_MANUAL,
            "02": MODE_TIME,
        }

    @property
    def actions(self) -> Dict[str, str]:
        """Return available actions."""
        return {
            "01": "Cleaning",
            "00": "Pause",
        }

    @property
    def garbage_actions(self) -> Dict[str, str]:
        """Return garbage-related actions."""
        return {
            "00": "Change Bag",
            "01": "Reset",
        }

    @property
    def last_log(self) -> Optional[str]:
        """Return the last log entry."""
        if self.logs:
            log = self.logs[0]
            return f"{log.get('time')} {log.get('event')}"
        return None

    @property
    def error(self) -> str:
        """Return the current error status."""
        try:
            return self.detail.get("currentError") or "Normal Operation"
        except Exception as e:
            _LOGGER.error("Failed to get error status: %s", e)
            return "Unknown"

    @property
    def litter_weight(self) -> float:
        """Return the current litter weight in kg."""
        try:
            cat_litter_weight = self.detail.get("catLitterWeight", self.empty_litter_box_weight)
            litter_weight = cat_litter_weight - self.empty_litter_box_weight
            self._litter_weight_during_day.append(litter_weight)
            return litter_weight
        except Exception as e:
            _LOGGER.error("Failed to get litter weight: %s", e)
            return 0.0

    @property
    def litter_remaining_days(self) -> int:
        """Return the remaining days of litter."""
        try:
            return int(self.detail.get("litterCountdown", 0))
        except Exception as e:
            _LOGGER.error("Failed to get litter remaining days: %s", e)
            return 0

    @property
    def total_clean_time(self) -> int:
        """Return the total number of cleanings."""
        try:
            return int(self.detail.get("inductionTimes", 0)) + int(self.detail.get("manualTimes", 0))
        except Exception as e:
            _LOGGER.error("Failed to get total clean time: %s", e)
            return 0

    @property
    def manual_clean_time(self) -> int:
        """Return the number of manual cleanings."""
        try:
            return int(self.detail.get("manualTimes", 0))
        except Exception as e:
            _LOGGER.error("Failed to get manual clean time: %s", e)
            return 0

    @property
    def deodorant_countdown(self) -> int:
        """Return the deodorant countdown in days."""
        try:
            return int(self.detail.get("deodorantCountdown", 0))
        except Exception as e:
            _LOGGER.error("Failed to get deodorant countdown: %s", e)
            return 0

    @property
    def knob_status(self) -> str:
        """Return the knob status."""
        try:
            errors = self.detail.get("deviceErrorList", [])
            knob_flag = any("left_knob_abnormal" in e.get("errkey", "") for e in errors)
            return "Empty Mode" if knob_flag else "Cleaning Mode"
        except Exception as e:
            _LOGGER.error("Failed to get knob status: %s", e)
            return "Unknown"

    @property
    def occupied(self) -> bool:
        """Return whether the litter box is currently occupied."""
        try:
            # Check if weight is increasing
            if len(self._litter_weight_during_day) < 2:
                return False
            
            for i in range(len(self._litter_weight_during_day) - 1):
                if self._litter_weight_during_day[i] < self._litter_weight_during_day[i + 1]:
                    return True
            return False
        except Exception as e:
            _LOGGER.error("Failed to get occupied status: %s", e)
            return False

    @property
    def online(self) -> bool:
        """Return whether the device is online."""
        try:
            return self.detail.get("online", False)
        except Exception as e:
            _LOGGER.error("Failed to get online status: %s", e)
            return False

    @property
    def last_sync(self) -> Optional[str]:
        """Return the last sync time."""
        timestamp = self.detail.get("lastHeartBeatTimestamp")
        if timestamp:
            try:
                dt = datetime.datetime.fromtimestamp(int(timestamp) / 1000.0)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                _LOGGER.error("Failed to parse last sync time: %s", e)
        return None

    @property
    def garbage_tobe_status(self) -> str:
        """Return the garbage bag status."""
        try:
            errors = self.detail.get("deviceErrorList", [])
            full_flag = any("garbage_tobe_full_abnormal" in e.get("errkey", "") for e in errors)
            return "Full" if full_flag else "Normal"
        except Exception as e:
            _LOGGER.error("Failed to get garbage status: %s", e)
            return "Unknown"

    def get_attributes(self) -> Dict[str, Any]:
        """Return all device attributes."""
        attrs = super().get_attributes()
        attrs.update({
            "litter_weight": self.litter_weight,
            "litter_remaining_days": self.litter_remaining_days,
            "total_clean_time": self.total_clean_time,
            "manual_clean_time": self.manual_clean_time,
            "deodorant_countdown": self.deodorant_countdown,
            "knob_status": self.knob_status,
            "occupied": self.occupied,
            "online": self.online,
            "last_sync": self.last_sync,
            "garbage_status": self.garbage_tobe_status,
            "last_log": self.last_log,
            "box_full_sensitivity": self.detail.get("boxFullSensitivity"),
            "quiet_times": self.detail.get("quietTimes"),
        })
        return attrs

    async def update_logs(self) -> List[Dict[str, Any]]:
        """Update device logs."""
        params = {"deviceId": self.id}
        
        try:
            response = await self.auth.request("token/litterbox/stats/log/top5", params)
            logs = response.get("data", {}).get("scooperLogTop5", [])
            
            if logs:
                self.logs = logs
                self._notify_listeners()
                return logs
            else:
                _LOGGER.warning("No logs in response: %s", response)
                return []
        except Exception as e:
            _LOGGER.error("Failed to update logs for %s: %s", self.name, e)
            return []

    async def set_mode(self, mode: str) -> bool:
        """Set the litter box mode."""
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
        
        response = await self.auth.request("token/litterbox/changeMode", params, "POST")
        if response.get("returnCode", 0) != 0:
            _LOGGER.error("Failed to set mode: %s", response)
            return False
        
        await self.update_device_detail()
        _LOGGER.info("Mode set successfully: %s", mode)
        return True

    async def execute_action(self, action: str) -> bool:
        """Execute a litter box action."""
        if action in self.garbage_actions.values():
            return await self.change_bag(action)
        
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
        
        response = await self.auth.request("token/litterbox/actionCmd", params, "POST")
        if response.get("returnCode", 0) != 0:
            _LOGGER.error("Failed to execute action: %s", response)
            return False
        
        await self.update_device_detail()
        _LOGGER.info("Action executed successfully: %s", action)
        return True

    async def change_bag(self, action: str) -> bool:
        """Change the garbage bag."""
        params = {
            "enable": "1" if action == "Change Bag" else "0",
            "deviceId": self.id,
        }
        
        response = await self.auth.request("token/litterbox/replaceGarbageBagCmd", params, "POST")
        if response.get("returnCode", 0) != 0:
            _LOGGER.error("Failed to change bag: %s", response)
            return False
        
        await self.update_device_detail()
        _LOGGER.info("Bag change executed successfully: %s", action)
        return True

    async def update_device_detail(self) -> Dict[str, Any]:
        """Update device details."""
        params = {"deviceId": self.id}
        
        try:
            response = await self.auth.request("token/litterbox/info", params)
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