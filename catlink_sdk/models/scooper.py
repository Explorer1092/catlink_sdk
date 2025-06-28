"""Scooper device model for CatLink SDK."""

from collections import deque
import datetime
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import logging
import json

from .device import Device
from .config import AdditionalDeviceConfig
from ..constants import MODE_AUTO, MODE_MANUAL, MODE_TIME

if TYPE_CHECKING:
    from ..auth import CatLinkAuth

_LOGGER = logging.getLogger(__name__)


class ScooperDevice(Device):
    """Scooper device class."""

    def __init__(self, data: Dict[str, Any], auth: "CatLinkAuth", config: Optional[AdditionalDeviceConfig] = None):
        """Initialize the scooper device."""
        super().__init__(data, auth, config)
        self.logs: List[Dict[str, Any]] = []
        self._litter_weight_during_day = deque(maxlen=self.config.max_samples_litter)
        self.empty_litter_box_weight = self.config.empty_weight
        self._debug_enabled = False

    async def async_init(self) -> None:
        """Initialize the scooper device asynchronously."""
        await super().async_init()
        # Removed update_logs() call - API endpoint returns 404

    def enable_debug(self, enabled: bool = True) -> None:
        """Enable or disable debug mode."""
        self._debug_enabled = enabled
        if enabled:
            _LOGGER.info("Debug mode enabled for %s", self.name)

    def _debug_log(self, message: str, data: Any = None) -> None:
        """Log debug information if debug mode is enabled."""
        if self._debug_enabled:
            if data:
                _LOGGER.debug("%s: %s - Data: %s", self.name, message, json.dumps(data, indent=2, ensure_ascii=False))
            else:
                _LOGGER.debug("%s: %s", self.name, message)

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
    def state(self) -> str:
        """Return the device state."""
        try:
            status = self.detail.get("workStatus", "")
            if status == "00":
                return "Idle"
            elif status == "01":
                return "Working"
            else:
                return "Unknown"
        except Exception as e:
            _LOGGER.error("Failed to get state: %s", e)
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
    def induction_clean_time(self) -> int:
        """Return the number of automatic cleanings."""
        try:
            return int(self.detail.get("inductionTimes", 0))
        except Exception as e:
            _LOGGER.error("Failed to get induction clean time: %s", e)
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
    def work_status(self) -> Optional[str]:
        """Return the work status."""
        try:
            return self.detail.get("workStatus")
        except Exception as e:
            _LOGGER.error("Failed to get work status: %s", e)
            return None

    @property
    def alarm_status(self) -> Optional[str]:
        """Return the alarm status."""
        try:
            return self.detail.get("alarmStatus")
        except Exception as e:
            _LOGGER.error("Failed to get alarm status: %s", e)
            return None

    @property
    def atmosphere_status(self) -> Optional[str]:
        """Return the atmosphere status."""
        try:
            return self.detail.get("atmosphereStatus")
        except Exception as e:
            _LOGGER.error("Failed to get atmosphere status: %s", e)
            return None

    @property
    def occupied(self) -> bool:
        """Return whether the scooper is currently occupied."""
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
    def temperature(self) -> Optional[float]:
        """Return the temperature."""
        try:
            return self.detail.get("temperature")
        except Exception as e:
            _LOGGER.error("Failed to get temperature: %s", e)
            return None

    @property
    def humidity(self) -> Optional[float]:
        """Return the humidity."""
        try:
            return self.detail.get("humidity")
        except Exception as e:
            _LOGGER.error("Failed to get humidity: %s", e)
            return None

    @property
    def key_lock(self) -> Optional[bool]:
        """Return the key lock status."""
        try:
            return self.detail.get("keyLock")
        except Exception as e:
            _LOGGER.error("Failed to get key lock status: %s", e)
            return None

    @property
    def safe_time(self) -> Optional[int]:
        """Return the safe time setting."""
        try:
            return self.detail.get("safeTime")
        except Exception as e:
            _LOGGER.error("Failed to get safe time: %s", e)
            return None

    @property
    def cat_litter_pave_second(self) -> Optional[int]:
        """Return the cat litter paving seconds."""
        try:
            return self.detail.get("catLitterPaveSecond")
        except Exception as e:
            _LOGGER.error("Failed to get pave second: %s", e)
            return None

    @property
    def box_full_sensitivity(self) -> Optional[int]:
        """Return the box full sensitivity setting."""
        try:
            return self.detail.get("boxFullSensitivity")
        except Exception as e:
            _LOGGER.error("Failed to get box full sensitivity: %s", e)
            return None

    @property
    def quiet_times(self) -> Optional[List[Dict[str, Any]]]:
        """Return the quiet time settings."""
        try:
            return self.detail.get("quietTimes")
        except Exception as e:
            _LOGGER.error("Failed to get quiet times: %s", e)
            return None

    @property
    def device_error_list(self) -> List[Dict[str, Any]]:
        """Return the device error list."""
        try:
            return self.detail.get("deviceErrorList", [])
        except Exception as e:
            _LOGGER.error("Failed to get device error list: %s", e)
            return []

    @property
    def weight(self) -> Optional[str]:
        """Return the device weight status (e.g., '充足')."""
        try:
            return self.detail.get("weight")
        except Exception as e:
            _LOGGER.error("Failed to get weight: %s", e)
            return None

    @property
    def last_log(self) -> Optional[str]:
        """Return the last log entry."""
        if self.logs:
            log = self.logs[0]
            return f"{log.get('time')} {log.get('event')}"
        return None

    # Lighting and Sound Properties
    @property
    def atmosphere_model(self) -> Optional[str]:
        """Return the atmosphere model setting."""
        return self.detail.get("atmosphereModel")

    @property
    def light_color_model(self) -> Optional[str]:
        """Return the light color model."""
        return self.detail.get("lightColorModel")

    @property
    def light_color(self) -> Optional[str]:
        """Return the current light color."""
        return self.detail.get("lightColor")

    @property
    def indicator_light(self) -> Optional[str]:
        """Return the indicator light status (e.g., 'ALWAYS_OPEN')."""
        return self.detail.get("indicatorLight")

    @property
    def panel_tone(self) -> Optional[str]:
        """Return the panel tone setting."""
        return self.detail.get("paneltone")

    @property
    def warning_tone(self) -> Optional[str]:
        """Return the warning tone setting."""
        return self.detail.get("warningtone")

    # Timing and Schedule Properties
    @property
    def timing_settings(self) -> Optional[List[Dict[str, Any]]]:
        """Return the scheduled cleaning times."""
        return self.detail.get("timingSettings")

    @property
    def near_enable_timing(self) -> Optional[bool]:
        """Return the near enable timing setting."""
        return self.detail.get("nearEnableTiming")

    @property
    def all_timing_toggle(self) -> bool:
        """Return whether all timing is toggled on/off."""
        return self.detail.get("allTimingToggle", False)

    @property
    def timer_times(self) -> int:
        """Return the number of timer cleanings."""
        try:
            return int(self.detail.get("timerTimes", 0))
        except Exception as e:
            _LOGGER.error("Failed to get timer times: %s", e)
            return 0

    @property
    def clear_times(self) -> int:
        """Return the number of clear operations."""
        try:
            return int(self.detail.get("clearTimes", 0))
        except Exception as e:
            _LOGGER.error("Failed to get clear times: %s", e)
            return 0

    # User and Sharing Properties
    @property
    def master(self) -> Optional[int]:
        """Return whether this is the master device."""
        return self.detail.get("master")

    @property
    def sharers(self) -> Optional[List[Dict[str, Any]]]:
        """Return the list of users sharing this device."""
        return self.detail.get("sharers")

    # Device Information Properties
    @property
    def default_status(self) -> Optional[int]:
        """Return the default device status."""
        return self.detail.get("defaultStatus")

    @property
    def current_message_type(self) -> Optional[str]:
        """Return the type of current message."""
        return self.detail.get("currentMessageType")

    @property
    def quiet_enable(self) -> bool:
        """Return whether quiet mode is enabled."""
        return self.detail.get("quietEnable", False)

    @property
    def firmware_version(self) -> Optional[str]:
        """Return the firmware version."""
        return self.detail.get("firmwareVersion")

    @property
    def timezone_id(self) -> Optional[str]:
        """Return the timezone ID."""
        return self.detail.get("timezoneId")

    @property
    def gmt(self) -> Optional[str]:
        """Return the GMT offset."""
        return self.detail.get("gmt")

    @property
    def auto_update_pet_weight(self) -> bool:
        """Return whether auto update pet weight is enabled."""
        return self.detail.get("autoUpdatePetWeight", False)

    @property
    def pro_model(self) -> bool:
        """Return whether this is a pro model."""
        return self.detail.get("proModel", False)

    @property
    def support_weight_calibration(self) -> bool:
        """Return whether weight calibration is supported."""
        return self.detail.get("supportWeightCalibration", False)

    @property
    def real_model(self) -> Optional[str]:
        """Return the real model number."""
        return self.detail.get("realModel")

    @property
    def toilet_slice_flag(self) -> bool:
        """Return the toilet slice flag."""
        return self.detail.get("toiletSliceFlag", False)

    @property
    def deodorization_status(self) -> Optional[str]:
        """Return the deodorization status."""
        return self.detail.get("deodorizationStatus")

    @property
    def box_installed(self) -> Optional[int]:
        """Return whether the box is installed."""
        return self.detail.get("boxInstalled")

    @property
    def sand_type(self) -> Optional[int]:
        """Return the type of sand."""
        return self.detail.get("sandType")

    @property
    def support_box_testing(self) -> bool:
        """Return whether box testing is supported."""
        return self.detail.get("supportBoxTesting", False)

    @property
    def error_alert_flag(self) -> bool:
        """Return whether error alerts are enabled."""
        return self.detail.get("errorAlertFlag", False)

    @property
    def high_edition(self) -> bool:
        """Return whether this is a high edition model."""
        return self.detail.get("highEdition", False)

    @property
    def ccare_temp_entrance(self) -> bool:
        """Return the ccare temp entrance flag."""
        return self.detail.get("ccareTempEntrance", False)

    @property
    def ccare_countdown_timestamp(self) -> Optional[str]:
        """Return the ccare countdown timestamp."""
        return self.detail.get("ccareCountdownTimestamp")

    # Product Information Properties
    @property
    def show_buy_btn(self) -> Optional[bool]:
        """Return whether to show buy button."""
        return self.detail.get("showBuyBtn")

    @property
    def good_url(self) -> Optional[str]:
        """Return the product URL."""
        return self.detail.get("goodUrl")

    @property
    def mall_code(self) -> Optional[str]:
        """Return the mall code."""
        return self.detail.get("mallCode")

    def get_attributes(self) -> Dict[str, Any]:
        """Return all device attributes."""
        attrs = super().get_attributes()
        attrs.update({
            # Weight and litter info
            "litter_weight": self.litter_weight,
            "litter_remaining_days": self.litter_remaining_days,
            "cat_litter_weight_raw": self.detail.get("catLitterWeight"),
            "weight": self.weight,
            
            # Cleaning info
            "total_clean_time": self.total_clean_time,
            "manual_clean_time": self.manual_clean_time,
            "induction_clean_time": self.induction_clean_time,
            "timer_times": self.timer_times,
            "clear_times": self.clear_times,
            
            # Deodorant info
            "deodorant_countdown": self.deodorant_countdown,
            
            # Status info
            "state": self.state,
            "occupied": self.occupied,
            "online": self.online,
            "work_status": self.work_status,
            "alarm_status": self.alarm_status,
            "atmosphere_status": self.atmosphere_status,
            "current_message_type": self.current_message_type,
            
            # Device settings
            "key_lock": self.key_lock,
            "safe_time": self.safe_time,
            "cat_litter_pave_second": self.cat_litter_pave_second,
            "box_full_sensitivity": self.box_full_sensitivity,
            "quiet_times": self.quiet_times,
            "quiet_enable": self.quiet_enable,
            
            # Lighting and sound settings
            "atmosphere_model": self.atmosphere_model,
            "light_color_model": self.light_color_model,
            "light_color": self.light_color,
            "indicator_light": self.indicator_light,
            "panel_tone": self.panel_tone,
            "warning_tone": self.warning_tone,
            
            # Timing settings
            "timing_settings": self.timing_settings,
            "near_enable_timing": self.near_enable_timing,
            "all_timing_toggle": self.all_timing_toggle,
            
            # User and sharing
            "master": self.master,
            "sharers": self.sharers,
            "default_status": self.default_status,
            
            # Device information
            "firmware_version": self.firmware_version,
            "timezone_id": self.timezone_id,
            "gmt": self.gmt,
            "auto_update_pet_weight": self.auto_update_pet_weight,
            "pro_model": self.pro_model,
            "support_weight_calibration": self.support_weight_calibration,
            "real_model": self.real_model,
            "toilet_slice_flag": self.toilet_slice_flag,
            "deodorization_status": self.deodorization_status,
            "box_installed": self.box_installed,
            "sand_type": self.sand_type,
            "support_box_testing": self.support_box_testing,
            "error_alert_flag": self.error_alert_flag,
            "high_edition": self.high_edition,
            "ccare_temp_entrance": self.ccare_temp_entrance,
            "ccare_countdown_timestamp": self.ccare_countdown_timestamp,
            
            # Product information
            "show_buy_btn": self.show_buy_btn,
            "good_url": self.good_url,
            "mall_code": self.mall_code,
            
            # Environment info
            "temperature": self.temperature,
            "humidity": self.humidity,
            
            # Sync and error info
            "last_sync": self.last_sync,
            "last_log": self.last_log,
            "device_error_list": self.device_error_list,
            
            # Debug info
            "debug_enabled": self._debug_enabled,
        })
        
        # Add all raw detail data for debugging
        if self._debug_enabled:
            attrs["_raw_detail"] = self.detail
            
        return attrs

    def get_debug_info(self) -> Dict[str, Any]:
        """Get comprehensive debug information."""
        debug_info = {
            "device_id": self.id,
            "device_name": self.name,
            "device_type": self.type,
            "device_model": self.model,
            "raw_data": self.data,
            "raw_detail": self.detail,
            "all_attributes": self.get_attributes(),
            "logs": self.logs[:10] if self.logs else [],
            "weight_history": list(self._litter_weight_during_day),
        }
        
        self._debug_log("Debug info generated", debug_info)
        return debug_info

    async def update_logs(self) -> List[Dict[str, Any]]:
        """Update device logs - DISABLED: API endpoint returns 404."""
        # This API endpoint is no longer available, returning empty list
        return []
        
        # Original implementation commented out:
        # params = {"deviceId": self.id}
        # 
        # try:
        #     response = await self.auth.request("token/catToilet/event/log", params)
        #     self._debug_log("Logs response", response)
        #     
        #     logs = response.get("data", {}).get("scooperLogTop5", [])
        #     
        #     if logs:
        #         self.logs = logs
        #         self._notify_listeners()
        #         return logs
        #     else:
        #         _LOGGER.warning("No logs in response: %s", response)
        #         return []
        # except Exception as e:
        #     _LOGGER.error("Failed to update logs for %s: %s", self.name, e)
        #     return []

    async def set_mode(self, mode: str) -> bool:
        """Set the scooper mode."""
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
        
        self._debug_log("Setting mode", params)
        
        response = await self.auth.request("token/device/changeMode", params, "POST")
        self._debug_log("Mode change response", response)
        
        if response.get("returnCode", 0) != 0:
            _LOGGER.error("Failed to set mode: %s", response)
            return False
        
        await self.update_device_detail()
        _LOGGER.info("Mode set successfully: %s", mode)
        return True

    async def execute_action(self, action: str) -> bool:
        """Execute a scooper action."""
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
        
        self._debug_log("Executing action", params)
        
        response = await self.auth.request("token/device/actionCmd", params, "POST")
        self._debug_log("Action response", response)
        
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
            response = await self.auth.request("token/device/info", params)
            self._debug_log("Device detail response", response)
            
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