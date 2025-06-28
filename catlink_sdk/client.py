"""Main client for CatLink SDK."""

from typing import List, Optional, Dict, Any
import logging

from .auth import CatLinkAuth
from .models import Device, LitterBox, FeederDevice, ScooperDevice, AdditionalDeviceConfig
from .constants import (
    API_DEVICE_LIST,
    DEVICE_TYPE_SCOOPER,
    DEVICE_TYPE_LITTER_BOX_599,
    DEVICE_TYPE_FEEDER,
    RETURN_CODE_ILLEGAL_TOKEN,
)

_LOGGER = logging.getLogger(__name__)


class CatLinkClient:
    """Main client for interacting with CatLink API."""

    def __init__(
        self,
        phone: str,
        password: str,
        phone_iac: str = "86",
        api_base: Optional[str] = None,
        language: Optional[str] = None,
    ):
        """Initialize the CatLink client."""
        from .constants import DEFAULT_API_BASE, DEFAULT_LANGUAGE
        
        self.auth = CatLinkAuth(
            phone=phone,
            password=password,
            phone_iac=phone_iac,
            api_base=api_base or DEFAULT_API_BASE,
            language=language or DEFAULT_LANGUAGE,
        )
        self.devices: List[Device] = []

    async def async_init(self) -> bool:
        """Initialize the client and authenticate."""
        success = await self.auth.login()
        if success:
            await self.get_devices()
        return success

    async def authenticate(self) -> bool:
        """Authenticate with the CatLink API."""
        return await self.auth.login()

    async def get_devices(self, device_configs: Optional[Dict[str, AdditionalDeviceConfig]] = None) -> List[Device]:
        """Get all devices associated with the account."""
        if not self.auth.token:
            if not await self.auth.login():
                return []

        response = await self.auth.request(API_DEVICE_LIST, {"type": "NONE"})
        return_code = response.get("returnCode", 0)

        if return_code == RETURN_CODE_ILLEGAL_TOKEN:
            # Token expired, re-authenticate
            if await self.auth.login():
                response = await self.auth.request(API_DEVICE_LIST, {"type": "NONE"})
            else:
                return []

        devices_data = response.get("data", {}).get("devices", [])
        if not devices_data:
            _LOGGER.warning("No devices found: %s", response)
            return []

        self.devices = []
        for device_data in devices_data:
            device_id = device_data.get("id")
            config = None
            if device_configs and device_id in device_configs:
                config = device_configs[device_id]
            
            device = self._create_device(device_data, config)
            if device:
                await device.async_init()
                self.devices.append(device)

        return self.devices

    def _create_device(self, device_data: Dict[str, Any], config: Optional[AdditionalDeviceConfig] = None) -> Optional[Device]:
        """Create a device instance based on device type."""
        device_type = device_data.get("deviceType")
        
        if device_type == DEVICE_TYPE_SCOOPER:
            return ScooperDevice(device_data, self.auth, config)
        elif device_type == DEVICE_TYPE_LITTER_BOX_599:
            return LitterBox(device_data, self.auth, config)
        elif device_type == DEVICE_TYPE_FEEDER:
            return FeederDevice(device_data, self.auth, config)
        else:
            _LOGGER.warning("Unknown device type: %s", device_type)
            return Device(device_data, self.auth, config)

    async def get_device_by_id(self, device_id: str) -> Optional[Device]:
        """Get a specific device by ID."""
        if not self.devices:
            await self.get_devices()
        
        for device in self.devices:
            if device.id == device_id:
                return device
        return None

    async def get_device_by_name(self, name: str) -> Optional[Device]:
        """Get a specific device by name."""
        if not self.devices:
            await self.get_devices()
        
        for device in self.devices:
            if device.name == name:
                return device
        return None

    async def update_all_devices(self) -> None:
        """Update all device details."""
        for device in self.devices:
            await device.update_device_detail()

    async def close(self) -> None:
        """Close the client session."""
        await self.auth.close()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.async_init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()