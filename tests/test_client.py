"""Tests for CatLink client."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from catlink_sdk import CatLinkClient


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization."""
    client = CatLinkClient(phone="1234567890", password="password")
    assert client.phone == "1234567890"
    assert client.password == "password"
    assert client.auth is not None
    await client.close()


@pytest.mark.asyncio
async def test_client_authenticate():
    """Test client authentication."""
    client = CatLinkClient(phone="1234567890", password="password")
    
    with patch.object(client.auth, 'login', new_callable=AsyncMock) as mock_login:
        mock_login.return_value = {"token": "test_token", "uid": "test_uid"}
        
        result = await client.authenticate()
        
        assert result == {"token": "test_token", "uid": "test_uid"}
        mock_login.assert_called_once()
    
    await client.close()


@pytest.mark.asyncio
async def test_get_devices_empty():
    """Test getting devices when no devices exist."""
    client = CatLinkClient(phone="1234567890", password="password")
    
    with patch.object(client.auth, 'request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"data": {"list": []}}
        
        devices = await client.get_devices()
        
        assert devices == []
        mock_request.assert_called_once_with("GET", "token/device/list")
    
    await client.close()


@pytest.mark.asyncio
async def test_close_client():
    """Test closing client properly closes session."""
    client = CatLinkClient(phone="1234567890", password="password")
    
    # Create a mock session
    mock_session = AsyncMock()
    client.auth._session = mock_session
    
    await client.close()
    
    mock_session.close.assert_called_once()