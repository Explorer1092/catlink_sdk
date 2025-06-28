# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python SDK project called `catlink_sdk` managed with Poetry and Python 3.11. It provides a Python interface for interacting with CatLink smart pet devices (litter boxes, feeders, etc.).

## Development Commands

### Dependency Management
```bash
# Install dependencies
poetry install

# Add a new dependency
poetry add <package-name>

# Add a development dependency
poetry add --group dev <package-name>

# Update dependencies
poetry update

# Show installed packages
poetry show
```

### Running Code
```bash
# Run Python scripts with Poetry's virtual environment
poetry run python <script.py>

# Activate virtual environment
poetry shell

# Run tests (once test framework is added)
poetry run pytest
```

### Building and Publishing
```bash
# Build the package
poetry build

# Publish to PyPI (requires configuration)
poetry publish
```

## Project Structure

- `pyproject.toml` - Poetry configuration and project metadata
- `.gitignore` - Git ignore patterns for Python projects
- `catlink_sdk/` - Main SDK package
  - `auth.py` - Authentication handling
  - `client.py` - Main client class
  - `constants.py` - API constants and device types
  - `models/` - Device model classes
    - `device.py` - Base device class
    - `litterbox.py` - Litter box specific functionality
    - `feeder.py` - Feeder device functionality
    - `scooper.py` - Scooper device functionality
    - `config.py` - Device configuration models
- `vendors/catlink/` - Reference implementation from Home Assistant integration

## Development Guidelines

1. Use Poetry for all dependency management
2. Python version requirement: ^3.11
3. Follow standard Python project structure
4. Keep dependencies minimal and well-documented in pyproject.toml
5. Main dependencies: aiohttp (for async HTTP requests), cryptography (for password encryption)

## SDK Usage Example

```python
import asyncio
from catlink_sdk import CatLinkClient, AdditionalDeviceConfig

async def main():
    # Initialize client
    client = CatLinkClient(phone="1234567890", password="password")
    
    # Optional: Configure device-specific settings
    device_configs = {
        "device_id_here": AdditionalDeviceConfig(
            empty_weight=5.0,  # Empty litter box weight in kg
            max_samples_litter=24  # Number of weight samples to track
        )
    }
    
    # Authenticate and get devices
    await client.authenticate()
    devices = await client.get_devices(device_configs)
    
    # Control a litter box or scooper
    for device in devices:
        if device.type in ["SCOOPER", "LITTER_BOX_599"]:
            await device.set_mode("auto")
            await device.execute_action("Cleaning")
            
            # Access device-specific properties
            print(f"Litter weight: {device.litter_weight} kg")
            print(f"Is occupied: {device.occupied}")
            print(f"Temperature: {device.temperature}°C")
            
    # Control a feeder
    for device in devices:
        if device.type == "FEEDER":
            await device.dispense_food(amount=10)  # Dispense 10g of food
            
    # Close session
    await client.close()

asyncio.run(main())
```

## Supported Device Types

- **SCOOPER** - Smart litter box with scooping mechanism
- **LITTER_BOX_599** - Litter box model 599
- **FEEDER** - Smart pet feeder
- **WATER_FOUNTAIN** - Smart water fountain (future support)