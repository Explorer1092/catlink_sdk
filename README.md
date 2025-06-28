# CatLink SDK for Python

A Python SDK for interacting with CatLink smart pet devices, including litter boxes, feeders, and water fountains.

## Features

- 🐱 Full support for CatLink smart devices (litter boxes, feeders, water fountains)
- 🔐 Secure authentication with encrypted passwords
- 🔄 Async/await support for efficient operations
- 📊 Real-time device monitoring and control
- 🎯 Type hints for better IDE support
- 🛠️ Comprehensive device management

## Installation

### Using pip

```bash
pip install catlink-sdk
```

### Using Poetry

```bash
poetry add catlink-sdk
```

### From source

```bash
git clone https://github.com/Explorer1092/catlink_sdk.git
cd catlink_sdk
poetry install
```

## Quick Start

```python
import asyncio
from catlink_sdk import CatLinkClient

async def main():
    # Initialize client
    client = CatLinkClient(phone="your_phone_number", password="your_password")
    
    # Authenticate
    await client.authenticate()
    
    # Get all devices
    devices = await client.get_devices()
    
    # Control a litter box
    for device in devices:
        if device.type in ["SCOOPER", "LITTER_BOX_599"]:
            # Set to auto mode
            await device.set_mode("auto")
            
            # Start cleaning
            await device.execute_action("Cleaning")
            
            # Check status
            print(f"Device: {device.name}")
            print(f"Litter weight: {device.litter_weight} kg")
            print(f"Temperature: {device.temperature}°C")
            print(f"Occupied: {device.occupied}")
    
    # Close session
    await client.close()

asyncio.run(main())
```

## Advanced Usage

### Device Configuration

```python
from catlink_sdk import CatLinkClient, AdditionalDeviceConfig

# Configure device-specific settings
device_configs = {
    "device_id_here": AdditionalDeviceConfig(
        empty_weight=5.0,  # Empty litter box weight in kg
        max_samples_litter=24  # Number of weight samples to track
    )
}

# Pass configs when getting devices
devices = await client.get_devices(device_configs)
```

### Monitoring Mode

The SDK includes a monitoring mode that continuously tracks device status:

```bash
# Using CLI
python -m example.cli -c example/config.toml --monitor

# Using Docker
docker-compose up -d
```

### Supported Device Types

| Device Type | Description | Features |
|------------|-------------|-----------|
| `SCOOPER` | Smart litter box with scooping | Auto cleaning, weight tracking, occupancy detection |
| `LITTER_BOX_599` | Litter box model 599 | Weight monitoring, temperature sensing |
| `FEEDER` | Smart pet feeder | Scheduled feeding, portion control |
| `WATER_FOUNTAIN` | Smart water fountain | Water level monitoring (coming soon) |

## Device Properties

### Common Properties
- `id` - Device ID
- `name` - Device name
- `type` - Device type
- `online` - Online status
- `battery_status` - Battery level (if applicable)
- `firmware_version` - Firmware version

### Litter Box Properties
- `litter_weight` - Current litter weight
- `occupied` - Whether pet is inside
- `temperature` - Internal temperature
- `humidity` - Internal humidity
- `deodorization_status` - Deodorizer status
- `sand_type` - Type of litter being used
- `error_msg` - Error messages if any

### Feeder Properties
- `food_state` - Food level status
- `eating_times` - Number of meals today
- `feed_amount_today` - Total food dispensed today

## Configuration Example

Create a `config.toml` file:

```toml
[catlink]
phone = "your_phone_number"
password = "your_password"

[device_configs]
[device_configs.your_device_id]
empty_weight = 5.0
max_samples_litter = 24
```

## Docker Support

Run the SDK in a container for long-term monitoring:

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f catlink-monitor

# Stop
docker-compose down
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/Explorer1092/catlink_sdk.git
cd catlink_sdk

# Install dependencies
poetry install

# Run tests
poetry run pytest
```

### Project Structure

```
catlink_sdk/
├── catlink_sdk/
│   ├── __init__.py
│   ├── auth.py          # Authentication handling
│   ├── client.py        # Main client class
│   ├── constants.py     # API constants
│   └── models/          # Device models
│       ├── device.py    # Base device class
│       ├── litterbox.py # Litter box specific
│       ├── feeder.py    # Feeder specific
│       └── scooper.py   # Scooper specific
├── example/
│   ├── cli.py          # CLI example
│   └── config.toml.example
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## API Reference

### CatLinkClient

```python
class CatLinkClient:
    def __init__(self, phone: str, password: str, api_base: str = None)
    async def authenticate() -> Dict[str, Any]
    async def get_devices(device_configs: Dict[str, AdditionalDeviceConfig] = None) -> List[Device]
    async def get_device(device_id: str) -> Device
    async def close()
```

### Device Methods

```python
class Device:
    async def update_state()
    async def set_mode(mode: str)
    async def execute_action(action: str)
    
# Litter box specific
class LitterBox(Device):
    async def start_cleaning()
    async def pause_cleaning()
    
# Feeder specific  
class Feeder(Device):
    async def dispense_food(amount: int)
    async def set_feeding_schedule(schedule: List[Dict])
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Based on the Home Assistant CatLink integration
- Thanks to the CatLink API for making this possible

## Support

- 📧 Email: [your-email@example.com]
- 🐛 Issues: [GitHub Issues](https://github.com/Explorer1092/catlink_sdk/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/Explorer1092/catlink_sdk/discussions)