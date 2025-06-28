"""Authentication module for CatLink SDK."""

import base64
import hashlib
import time
from typing import Optional, Dict, Any

import aiohttp
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from .constants import (
    DEFAULT_API_BASE,
    RSA_PUBLIC_KEY,
    SIGN_KEY,
    DEFAULT_LANGUAGE,
)


class CatLinkAuth:
    """Handle authentication for CatLink API."""

    def __init__(
        self,
        phone: str,
        password: str,
        phone_iac: str = "86",
        api_base: str = DEFAULT_API_BASE,
        language: str = DEFAULT_LANGUAGE,
    ):
        """Initialize authentication handler."""
        self.phone = phone
        self.phone_iac = phone_iac
        self._password = password
        self.api_base = api_base.rstrip("/")
        self.language = language
        self.token: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def password(self) -> str:
        """Return encrypted password."""
        if len(self._password) <= 16:
            return self.encrypt_password(self._password)
        return self._password

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def api_url(self, endpoint: str) -> str:
        """Return the full URL for an API endpoint."""
        if endpoint.startswith(("https://", "http://")):
            return endpoint
        return f"{self.api_base}/{endpoint.lstrip('/')}"

    async def request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        **kwargs
    ) -> Dict[str, Any]:
        """Make an API request."""
        method = method.upper()
        url = self.api_url(endpoint)
        
        headers = {
            "language": self.language,
            "User-Agent": "okhttp/3.10.0",
            "token": self.token or "",
        }
        
        if params is None:
            params = {}
        
        params["noncestr"] = int(time.time() * 1000)
        if self.token:
            params["token"] = self.token
        params["sign"] = self.params_sign(params)
        
        kwargs["timeout"] = kwargs.get("timeout", 60)
        kwargs["headers"] = headers
        
        if method == "GET":
            kwargs["params"] = params
        elif method == "POST_GET":
            method = "POST"
            kwargs["params"] = params
        else:
            kwargs["data"] = params
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                return await response.json()
        except Exception as e:
            print(f"Request failed: {method} {url} - {e}")
            return {}

    async def login(self) -> bool:
        """Login to CatLink API."""
        params = {
            "platform": "ANDROID",
            "internationalCode": self.phone_iac,
            "mobile": str(self.phone),
            "password": self.password,
        }
        
        self.token = None
        response = await self.request("login/password", params, "POST")
        
        token = response.get("data", {}).get("token")
        if not token:
            print(f"Login failed for {self.phone}: {response}")
            return False
        
        self.token = token
        return True

    async def check_auth(self) -> bool:
        """Check if current auth token is valid."""
        if not self.token:
            return await self.login()
        
        # Test token by making a simple request
        response = await self.request("token/device/union/list/sorted", {"type": "NONE"})
        if response.get("returnCode") == 1002:  # Illegal token
            return await self.login()
        
        return True

    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()

    @staticmethod
    def params_sign(params: Dict[str, Any]) -> str:
        """Sign the parameters for API request."""
        items = sorted(params.items())
        param_str = "&".join([f"{k}={v}" for k, v in items])
        param_str += f"&key={SIGN_KEY}"
        return hashlib.md5(param_str.encode()).hexdigest().upper()

    @staticmethod
    def encrypt_password(password: str) -> str:
        """Encrypt password using RSA."""
        password = str(password)
        md5_hash = hashlib.md5(password.encode()).hexdigest().lower()
        sha_hash = hashlib.sha1(md5_hash.encode()).hexdigest().upper()
        
        public_key = serialization.load_der_public_key(
            base64.b64decode(RSA_PUBLIC_KEY),
            default_backend()
        )
        
        encrypted = public_key.encrypt(
            sha_hash.encode(),
            padding.PKCS1v15()
        )
        
        return base64.b64encode(encrypted).decode()