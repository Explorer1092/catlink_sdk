"""Scooper device model for CatLink SDK."""

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


class ScooperDevice(Device):
    """Scooper device class for CatLink smart litter boxes."""

    def __init__(
        self, 
        data: Dict[str, Any], 
        auth: "CatLinkAuth",
        config: Optional[AdditionalDeviceConfig] = None
    ):
        """Initialize the scooper device."""
        super().__init__(data, auth, config)
        self.logs: List[Dict[str, Any]] = []
        self._litter_weight_during_day = deque(maxlen=self.config.max_samples_litter)
        self._error_logs = deque(maxlen=20)
        self.empty_litter_box_weight = self.config.empty_weight

    async def async_init(self) -> None:
        """Initialize the scooper device asynchronously."""
        await super().async_init()
        await self.update_logs()

    @property
    def modes(self) -> Dict[str, str]:
        """Return available modes."""
        return {
            "00": MODE_AUTO,
            "01": MODE_MANUAL,
            "02": MODE_TIME,
            "03": "empty",
        }

    @property
    def actions(self) -> Dict[str, str]:
        """Return available actions."""
        return {
            "00": "pause",
            "01": "start",
        }

    @property
    def last_log(self) -> Optional[str]:
        """Return the last log entry."""
        if self.logs:
            log = self.logs[0]
            return f"{log.get('time')} {log.get('event')}"
        return None

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
            _LOGGER.error("Failed to get device state: %s", e)
            return "unknown"

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
    def litter_remaining_days(self) -> Optional[int]:
        """Return the remaining days of litter."""
        try:
            return self.detail.get("litterCountdown")
        except Exception as e:
            _LOGGER.error("Failed to get litter remaining days: %s", e)
            return None

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
    def occupied(self) -> bool:
        """Return whether the scooper is currently occupied."""
        try:
            if len(self._litter_weight_during_day) < 2:
                return False
            
            for i in range(len(self._litter_weight_during_day) - 1):
                if self._litter_weight_during_day[i] < self._litter_weight_during_day[i + 1]:
                    return True
            return False
        except Exception:
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
    def temperature(self) -> Optional[float]:
        """Return the temperature in Celsius."""
        temp = self.detail.get("temperature")
        if temp and temp != "-":
            try:
                return float(temp)
            except ValueError:
                pass
        return None

    @property
    def humidity(self) -> Optional[float]:
        """Return the humidity percentage."""
        hum = self.detail.get("humidity")
        if hum and hum != "-":
            try:
                return float(hum)
            except ValueError:
                pass
        return None

    @property
    def error(self) -> Optional[str]:
        """Return the current error message."""
        try:
            error = self.detail.get("currentMessage") or self.data.get("currentErrorMessage", "")
            if error and error.lower() != "device online":
                self._error_logs.append({
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "error": error,
                })
            return error if error else None
        except Exception as e:
            _LOGGER.error("Failed to get device error: %s", e)
            return "unknown"

    def get_attributes(self) -> Dict[str, Any]:
        """Return all device attributes."""
        attrs = super().get_attributes()
        attrs.update({
            "litter_weight": self.litter_weight,
            "litter_remaining_days": self.litter_remaining_days,
            "total_clean_time": self.total_clean_time,
            "manual_clean_time": self.manual_clean_time,
            "deodorant_countdown": self.deodorant_countdown,
            "occupied": self.occupied,
            "online": self.online,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "last_log": self.last_log,
            "error_logs": list(self._error_logs),
        })
        return attrs

    async def update_logs(self) -> List[Dict[str, Any]]:
        """Update device logs."""
        params = {"deviceId": self.id}
        
        try:
            response = await self.auth.request("token/device/scooper/stats/log/top5", params)
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

    def get_error_logs(self) -> List[Dict[str, str]]:
        """Get error log history."""
        return list(self._error_logs)