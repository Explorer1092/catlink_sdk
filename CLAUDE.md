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

## ✅ SDK 最新更新 (2025-01-28)

### 🎉 新增功能

SDK 现在已经支持之前缺失的所有 36 个参数！包括：

#### 🔦 灯光音效控制
- `atmosphere_model` - 氛围灯模式
- `light_color_model` - 灯光颜色模式
- `light_color` - 当前灯光颜色
- `indicator_light` - 指示灯状态
- `panel_tone` - 面板提示音
- `warning_tone` - 警告音设置

#### ⏰ 定时功能
- `timing_settings` - 定时清理配置数组
- `near_enable_timing` - 近场定时启用
- `all_timing_toggle` - 全部定时开关
- `timer_times` - 定时清理次数
- `clear_times` - 清理操作次数

#### 👥 用户管理
- `master` - 主设备标识
- `sharers` - 共享用户列表

#### 📱 设备信息
- `firmware_version` - 固件版本
- `timezone_id` - 时区ID
- `gmt` - GMT偏移
- `real_model` - 真实型号
- `default_status` - 默认状态
- `current_message_type` - 当前消息类型

#### 🔧 高级功能
- `auto_update_pet_weight` - 自动更新宠物体重
- `pro_model` - Pro型号标识
- `support_weight_calibration` - 支持重量校准
- `high_edition` - 高版本标识
- `toilet_slice_flag` - 厕所切片标志
- `deodorization_status` - 除臭状态
- `box_installed` - 垃圾盒安装状态
- `sand_type` - 猫砂类型
- `support_box_testing` - 支持垃圾盒测试
- `error_alert_flag` - 错误提醒标志
- `quiet_enable` - 静音模式启用
- `ccare_temp_entrance` - Ccare临时入口
- `ccare_countdown_timestamp` - Ccare倒计时时间戳

#### 🛍️ 产品信息
- `show_buy_btn` - 是否显示购买按钮
- `good_url` - 产品URL
- `mall_code` - 商城代码

### 🐛 修复的问题

1. ✅ **weight** 参数类型 - 现在正确处理字符串类型（如"充足"）
2. ✅ **deviceId** 字段兼容性 - 现在同时支持 "id" 和 "deviceId"

### 📝 使用新功能的示例

```python
# 获取设备的所有新属性
device = await client.get_device("device_id")

# 灯光控制
print(f"灯光颜色: {device.light_color}")
print(f"指示灯状态: {device.indicator_light}")

# 定时功能
if device.timing_settings:
    for timing in device.timing_settings:
        print(f"定时清理: {timing['timingHour']}:{timing['timingMin']}")

# 设备信息
print(f"固件版本: {device.firmware_version}")
print(f"是否Pro型号: {device.pro_model}")
print(f"猫砂类型: {device.sand_type}")

# 用户管理
if device.sharers:
    print(f"共享用户数: {len(device.sharers)}")
```