# CatLink SDK 调试指南

## 概述

本指南说明如何使用 CatLink SDK 的调试功能来查看设备的所有可用参数，特别是除臭相关的状态。

## 新增功能

### 1. 调试模式

所有猫砂盒设备（LitterBox 和 ScooperDevice）现在都支持调试模式：

```python
# 启用调试模式
device.enable_debug(True)

# 禁用调试模式
device.enable_debug(False)
```

### 2. 新增属性

SDK 现在支持以下新属性：

#### 除臭相关
- `deodorant_countdown` - 除臭剂剩余天数（不区分除臭棉/魔方）

#### 设备状态
- `work_status` - 工作状态代码
- `alarm_status` - 报警状态
- `atmosphere_status` - 氛围状态
- `online` - 在线状态
- `last_sync` - 最后同步时间

#### 环境信息
- `temperature` - 温度（部分设备支持）
- `humidity` - 湿度（部分设备支持）

#### 设备设置
- `key_lock` - 按键锁定状态
- `safe_time` - 安全时间设置
- `cat_litter_pave_second` - 铺猫砂秒数
- `box_full_sensitivity` - 垃圾盒满敏感度
- `quiet_times` - 安静时间设置

#### 清洁信息
- `induction_clean_time` - 自动清洁次数
- `device_error_list` - 设备错误列表

### 3. 调试信息获取

```python
# 获取完整的调试信息
debug_info = device.get_debug_info()

# 调试信息包含：
# - 原始设备数据 (raw_data)
# - 原始详情数据 (raw_detail)
# - 所有属性 (all_attributes)
# - 最近的日志 (logs)
# - 重量历史 (weight_history)
```

## 使用示例

### 基本使用

```python
import asyncio
from catlink_sdk import CatLinkClient

async def main():
    # 创建客户端
    client = CatLinkClient(phone="your_phone", password="your_password")
    await client.authenticate()
    
    # 获取设备
    devices = await client.get_devices()
    
    for device in devices:
        if device.type in ["LITTER_BOX", "SCOOPER"]:
            # 启用调试
            device.enable_debug(True)
            
            # 更新设备详情
            await device.update_device_detail()
            
            # 打印除臭信息
            print(f"除臭剂剩余: {device.deodorant_countdown} 天")
            
            # 获取所有属性
            attrs = device.get_attributes()
            print(f"所有属性: {attrs}")
            
            # 获取调试信息
            debug_info = device.get_debug_info()
            # 保存到文件以便分析
            import json
            with open(f"debug_{device.id}.json", 'w') as f:
                json.dump(debug_info, f, indent=2, ensure_ascii=False)

asyncio.run(main())
```

### 运行调试脚本

使用提供的 `test_debug.py` 脚本：

```bash
python test_debug.py <手机号> <密码>
```

该脚本会：
1. 连接到 CatLink API
2. 获取所有设备
3. 对每个猫砂盒设备启用调试模式
4. 显示所有可用的参数
5. 保存完整的调试信息到 JSON 文件
6. 检查是否有未知的字段（可能包含新功能）

## 关于除臭状态

目前 SDK 只能获取除臭剂的剩余天数（`deodorant_countdown`），无法区分具体是除臭棉还是除臭魔方。

从 API 返回的数据分析来看：
- API 只提供 `deodorantCountdown` 字段
- 没有发现区分除臭棉/魔方类型的字段
- 没有发现除臭剂具体状态的其他字段

如果您在调试输出中发现了新的相关字段，请提交反馈。

## 故障排除

1. **调试日志未显示**
   - 确保已设置日志级别为 DEBUG：
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **属性返回 None**
   - 确保设备支持该功能
   - 确保已调用 `update_device_detail()` 更新设备信息
   - 检查调试信息中的 `raw_detail` 查看原始数据

3. **发现未知字段**
   - 运行调试脚本会自动检测未知字段
   - 这些字段可能表示新功能或特定型号的特殊功能
   - 请记录这些字段并反馈给开发者

## 贡献

如果您发现了新的参数或功能，欢迎：
1. 提交 Issue 报告新发现的字段
2. 提交 PR 添加对新字段的支持
3. 分享您的调试日志（注意隐私信息） 