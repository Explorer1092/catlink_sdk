#!/usr/bin/env python3
"""
CatLink SDK Example CLI Application

This example demonstrates how to use the CatLink SDK with command-line arguments
for authentication and various device control features.
"""

import asyncio
import argparse
import sys
import json
import logging
from getpass import getpass
from typing import Optional, Dict, Set
from datetime import datetime
from pathlib import Path

import aiohttp
import toml
from croniter import croniter
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich import box
from rich.logging import RichHandler

from catlink_sdk import CatLinkClient
from catlink_sdk.models.device import Device
from catlink_sdk.models.litterbox import LitterBox
from catlink_sdk.models.feeder import FeederDevice
from catlink_sdk.models.scooper import ScooperDevice

console = Console()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)


class CatLinkMonitor:
    """CatLink设备监控器"""
    
    def __init__(self, config_path: str = "config.toml"):
        """初始化监控器"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.client: Optional[CatLinkClient] = None
        self.last_notified_state: Dict[str, Dict[str, any]] = {}  # 记录上次通知的状态
        
    def _load_config(self) -> dict:
        """加载配置文件"""
        if not self.config_path.exists():
            logger.error(f"配置文件不存在: {self.config_path}")
            self._create_default_config()
            logger.info(f"已创建默认配置文件: {self.config_path}")
            logger.info("请编辑配置文件后重新运行程序")
            sys.exit(1)
            
        try:
            return toml.load(self.config_path)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)
    
    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            "catlink": {
                "username": "your_phone_number",
                "password": "your_password",
            },
            "dingtalk": {
                "webhook": "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN",
                "secret": "YOUR_SECRET (optional)",
            },
            "monitor": {
                "cron_schedule": "0 9 * * *",  # 每天早上9点执行
                "litter_days_threshold": 0,
                "deodorant_days_threshold": 0,
            }
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            toml.dump(default_config, f)
    
    async def connect(self):
        """连接到CatLink"""
        catlink_config = self.config.get("catlink", {})
        self.client = CatLinkClient(
            phone=catlink_config.get("username"),
            password=catlink_config.get("password")
        )
        
        logger.info("正在连接到CatLink...")
        await self.client.authenticate()
        logger.info("CatLink连接成功")
    
    async def send_dingtalk_message(self, title: str, content: str):
        """发送钉钉消息"""
        dingtalk_config = self.config.get("dingtalk", {})
        webhook = dingtalk_config.get("webhook")
        secret = dingtalk_config.get("secret")
        
        if not webhook:
            logger.error("钉钉webhook未配置")
            return
        
        # 构建消息
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": content
            }
        }
        
        # 如果配置了secret，需要计算签名
        if secret:
            import time
            import hmac
            import hashlib
            import base64
            import urllib.parse
            
            timestamp = str(round(time.time() * 1000))
            secret_enc = secret.encode('utf-8')
            string_to_sign = f'{timestamp}\n{secret}'
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            webhook = f"{webhook}&timestamp={timestamp}&sign={sign}"
        
        # 发送请求
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(webhook, json=message) as response:
                    result = await response.json()
                    if result.get("errcode") == 0:
                        logger.info("钉钉消息发送成功")
                    else:
                        logger.error(f"钉钉消息发送失败: {result}")
            except Exception as e:
                logger.error(f"发送钉钉消息异常: {e}")
    
    async def check_device(self, device):
        """检查单个设备状态"""
        if not isinstance(device, (ScooperDevice, LitterBox)):
            return
        
        monitor_config = self.config.get("monitor", {})
        litter_threshold = monitor_config.get("litter_days_threshold", 0)
        deodorant_threshold = monitor_config.get("deodorant_days_threshold", 0)
        
        alerts = []
        device_key = f"{device.id}_{device.name}"
        current_state = {}
        
        # 检查猫砂剩余天数
        try:
            litter_days = device.litter_remaining_days
            if litter_days is not None:
                current_state['litter_days'] = litter_days
                if litter_days <= litter_threshold:
                    alerts.append(f"- 猫砂剩余天数: **{litter_days}天**")
        except Exception as e:
            logger.debug(f"获取猫砂剩余天数失败: {e}")
        
        # 检查除臭剂剩余天数
        try:
            deodorant_days = device.deodorant_countdown
            if deodorant_days is not None:
                current_state['deodorant_days'] = deodorant_days
                if deodorant_days <= deodorant_threshold:
                    alerts.append(f"- 除臭剂剩余: **{deodorant_days}天**")
        except Exception as e:
            logger.debug(f"获取除臭剂剩余天数失败: {e}")
        
        # 检查状态是否变化
        last_state = self.last_notified_state.get(device_key, {})
        state_changed = current_state != last_state
        
        # 发送提醒（有警报且状态变化时）
        if alerts and state_changed:
            title = f"⚠️ {device.name} 需要补充耗材"
            
            # 获取额外信息
            extra_info = []
            if hasattr(device, 'temperature') and device.temperature:
                extra_info.append(f"温度: {device.temperature}°C")
            if hasattr(device, 'humidity') and device.humidity:
                extra_info.append(f"湿度: {device.humidity}%")
            
            content = f"## {title}\n\n"
            content += "### 需要补充的耗材:\n"
            content += "\n".join(alerts)
            
            if extra_info:
                content += "\n\n### 设备状态:\n"
                content += "- " + "\n- ".join(extra_info)
            
            content += f"\n\n---\n*检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
            
            await self.send_dingtalk_message(title, content)
            
            # 更新已通知状态
            self.last_notified_state[device_key] = current_state
            
            logger.info(f"已发送提醒: {device.name} - {', '.join(alerts)}")
        elif not alerts and device_key in self.last_notified_state:
            # 如果状态恢复正常，清除记录
            del self.last_notified_state[device_key]
            logger.info(f"{device.name} 耗材状态已恢复正常")
    
    async def check_all_devices(self):
        """检查所有设备"""
        if not self.client:
            logger.error("未连接到CatLink")
            return
        
        try:
            devices = await self.client.get_devices()
            logger.info(f"找到 {len(devices)} 个设备")
            
            for device in devices:
                await self.check_device(device)
                
        except Exception as e:
            logger.error(f"检查设备失败: {e}")
    
    async def run(self):
        """运行监控器"""
        await self.connect()
        
        monitor_config = self.config.get("monitor", {})
        cron_schedule = monitor_config.get("cron_schedule", "0 9 * * *")
        
        # 验证cron表达式
        try:
            cron = croniter(cron_schedule, datetime.now())
        except Exception as e:
            logger.error(f"无效的cron表达式: {cron_schedule} - {e}")
            return
        
        logger.info(f"开始监控，使用cron调度: {cron_schedule}")
        
        # 立即执行一次检查
        logger.info("立即执行首次检查...")
        try:
            await self.check_all_devices()
        except Exception as e:
            logger.error(f"首次检查失败: {e}")
        
        logger.info(f"下次执行时间: {cron.get_next(datetime).strftime('%Y-%m-%d %H:%M:%S')}")
        
        while True:
            try:
                # 计算下次执行时间
                next_run = cron.get_next(datetime)
                wait_seconds = (next_run - datetime.now()).total_seconds()
                
                if wait_seconds > 0:
                    logger.info(f"等待执行，下次检查时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                    await asyncio.sleep(wait_seconds)
                
                # 执行检查
                await self.check_all_devices()
                
            except KeyboardInterrupt:
                logger.info("监控已停止")
                break
            except Exception as e:
                logger.error(f"监控异常: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟重试
        
        if self.client:
            await self.client.close()


class CatLinkDemo:
    def __init__(self, phone: str, password: str):
        self.phone = phone
        self.password = password
        self.client: Optional[CatLinkClient] = None
        self.devices: list[Device] = []

    async def connect(self):
        """Connect to CatLink API and authenticate."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("正在连接 CatLink...", total=None)
            
            self.client = CatLinkClient(phone=self.phone, password=self.password)
            
            progress.update(task, description="正在认证...")
            await self.client.authenticate()
            
            progress.update(task, description="正在获取设备...")
            self.devices = await self.client.get_devices()
            
            progress.update(task, completed=True)

        console.print(f"[green]✓ 连接成功！找到 {len(self.devices)} 个设备[/green]")

    async def show_devices(self):
        """Display all devices in a formatted table."""
        if not self.devices:
            console.print("[yellow]未找到设备。[/yellow]")
            return

        table = Table(title="CatLink 设备列表", box=box.ROUNDED)
        table.add_column("设备ID", style="cyan")
        table.add_column("设备名称", style="magenta")
        table.add_column("设备类型", style="green")
        table.add_column("在线状态", style="blue")
        table.add_column("工作状态", style="yellow")
        table.add_column("模式", style="magenta")
        table.add_column("电量", style="yellow")

        for device in self.devices:
            online_status = "✓ 在线" if device.online else "✗ 离线"
            power_status = f"{getattr(device, 'power', 'N/A')}{'%' if hasattr(device, 'power') else ''}"
            
            table.add_row(
                device.id,
                device.name,
                device.type,
                online_status,
                getattr(device, 'state', 'N/A'),
                getattr(device, 'mode', 'N/A'),
                power_status,
            )

        console.print(table)

    async def show_device_details(self, device: Device):
        """Show detailed information for a specific device."""
        # 利用设备的 get_attributes() 提供的详细信息
        try:
            attrs = device.get_attributes()  # type: ignore
        except Exception:
            attrs = {}

        # Fallback: 如果没有实现 get_attributes
        if not attrs:
            attrs = {
                "id": device.id,
                "name": device.name,
                "type": device.type,
                "model": device.model,
                "online": device.online,
            }

        # 中文标签映射
        zh_labels = {
            "id": "设备ID",
            "name": "设备名称",
            "type": "设备类型",
            "model": "设备型号",
            "state": "工作状态",
            "mode": "模式",
            "online": "在线",
            "occupied": "占用",
            "litter_weight": "猫砂重量(kg)",
            "litter_remaining_days": "猫砂剩余天数",
            "temperature": "温度(°C)",
            "humidity": "湿度(%)",
            "deodorant_countdown": "除臭剂剩余(天)",
            "total_clean_time": "总清理次数",
            "manual_clean_time": "手动清理次数",
            "induction_clean_time": "自动清理次数",
            "work_status": "WorkStatus",
            "alarm_status": "AlarmStatus",
            "atmosphere_status": "AtmosphereStatus",
            "box_full_sensitivity": "满箱灵敏度",
            "last_sync": "最后同步",
            "last_log": "最后日志",
            "error": "错误",
            # 额外参数
            "weight": "重量",
            "firmware_version": "固件版本",
            "timezone_id": "时区",
            "gmt": "GMT",
            "indicator_light": "指示灯",
            "light_color": "灯光颜色",
            "light_color_model": "灯光颜色模式",
            "atmosphere_model": "氛围灯模式",
            "safe_time": "安全时间",
            "key_lock": "按键锁",
            "auto_update_pet_weight": "自动更新体重",
            "pro_model": "Pro型号",
            "support_weight_calibration": "支持重量校准",
            "atmosphere_model": "氛围灯模式",
            "light_color_model": "灯光颜色模式",
            "light_color": "灯光颜色",
            "indicator_light": "指示灯",
            "panel_tone": "面板音效",
            "warning_tone": "警告音效",
            "all_timing_toggle": "定时总开关",
            "timing_settings": "定时设置",
            "near_enable_timing": "接近启动定时",
            "timer_times": "定时次数",
            "clear_times": "清理次数",
            "box_installed": "收纳盒安装",
            "sand_type": "猫砂类型",
            "quiet_enable": "静音启用",
            "quiet_times": "静音时段",
            "ccare_countdown_timestamp": "护理倒计时",
            "ccare_temp_entrance": "护理入口",
            "toilet_slice_flag": "厕所切片标识",
            "error_alert_flag": "错误警报标志",
            "high_edition": "高版本",
            "default_status": "默认状态",
            "auto_update_pet_weight": "自动更新宠物体重",
            "master": "主人标识",
            "sharers": "共享用户",
            "show_buy_btn": "显示购买按钮",
            "good_url": "商品URL",
            "mall_code": "商城代码",
            "device_error_list": "设备错误列表",
            "cat_litter_weight_raw": "原始猫砂重量",
            "mac": "MAC地址",
            "real_model": "真实型号",
            "current_message_type": "当前信息类型",
            "weight": "重量",
            # ...可继续补充
        }

        # 自定义展示顺序
        preferred_order = [
            "state", "mode", "online", "occupied", "litter_weight", "litter_remaining_days",
            "temperature", "humidity", "deodorant_countdown", "total_clean_time", "manual_clean_time",
            "induction_clean_time", "work_status", "alarm_status", "atmosphere_status", "box_full_sensitivity",
            "last_sync", "last_log", "error",
        ]

        details = []

        # 主键优先
        basic_keys = ["id", "name", "type", "model"]
        for key in basic_keys:
            if key in attrs:
                details.append(f"[cyan]{key}:[/cyan] {attrs[key]}")

        # 判断是否开启调试
        debug_mode = attrs.get("debug_enabled", False)

        # 动态遍历其余属性
        for key in preferred_order + sorted(set(attrs.keys()) - set(basic_keys) - set(preferred_order)):
            if key not in attrs:
                continue
            if key.startswith("_"):
                # 跳过私有/调试字段
                continue
            if key == "debug_enabled" and not debug_mode:
                # 未开启调试时不显示 debug_enabled
                continue

            value = attrs[key]
            # 友好格式化布尔值
            if isinstance(value, bool):
                value = "✅" if value else "❌"
            # 如果是列表或字典，用json缩进化简显示
            if isinstance(value, (list, dict)):
                value = json.dumps(value, ensure_ascii=False)

            # 中文标签或英文友好名
            label = zh_labels.get(key, key.replace("_", " "))
            details.append(f"[cyan]{label}:[/cyan] {value}")

        panel = Panel("\n".join(details), title=f"🐱 {device.name}", box=box.ROUNDED)
        console.print(panel)

    async def control_litter_box(self, device):
        """Control a litter box device."""
        while True:
            console.print("\n[bold]猫砂盆控制:[/bold]")
            console.print("1. 设置模式 (auto/manual/sleep)")
            console.print("2. 开始清理")
            console.print("3. 校准重量")
            console.print("4. 查看统计")
            console.print("5. 返回设备列表")
            
            choice = Prompt.ask("请选择", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                mode = Prompt.ask("选择模式", choices=["auto", "manual", "sleep"])
                with console.status(f"正在设置模式为 {mode}..."):
                    await device.set_mode(mode)
                console.print(f"[green]✓ 模式已设置为 {mode}[/green]")
                
            elif choice == "2":
                if Confirm.ask("是否开始清理周期？"):
                    with console.status("正在开始清理..."):
                        await device.execute_action("Cleaning")
                    console.print("[green]✓ 清理已开始[/green]")
                    
            elif choice == "3":
                if hasattr(device, 'calibrate_weight'):
                    with console.status("正在校准重量..."):
                        await device.calibrate_weight()
                    console.print("[green]✓ 重量已校准[/green]")
                else:
                    console.print("[yellow]此设备不支持重量校准[/yellow]")
                
            elif choice == "4":
                stats_table = Table(title="猫砂盆统计数据", box=box.SIMPLE)
                stats_table.add_column("指标", style="cyan")
                stats_table.add_column("数值", style="magenta")
                
                if hasattr(device, 'total_uses'):
                    stats_table.add_row("总使用次数", str(device.total_uses))
                if hasattr(device, 'today_uses'):
                    stats_table.add_row("今日使用", str(device.today_uses))
                if hasattr(device, 'avg_use_time'):
                    stats_table.add_row("平均使用时长", f"{device.avg_use_time} 秒")
                if hasattr(device, 'litter_weight'):
                    stats_table.add_row("猫砂重量", f"{device.litter_weight:.2f} kg")
                
                console.print(stats_table)
                
            elif choice == "5":
                break

    async def control_feeder(self, device: FeederDevice):
        """Control a feeder device."""
        while True:
            console.print("\n[bold]喂食器控制:[/bold]")
            console.print("1. 投喂食物")
            console.print("2. 设置喂食计划")
            console.print("3. 查看食物量")
            console.print("4. 返回设备列表")
            
            choice = Prompt.ask("请选择", choices=["1", "2", "3", "4"])
            
            if choice == "1":
                amount = Prompt.ask("食物量 (克)", default="10")
                try:
                    amount = int(amount)
                    with console.status(f"正在投喂 {amount}g 食物..."):
                        await device.dispense_food(amount)
                    console.print(f"[green]✓ 已投喂 {amount}g 食物[/green]")
                except ValueError:
                    console.print("[red]无效的数量[/red]")
                    
            elif choice == "2":
                console.print("[yellow]喂食计划配置功能在此演示中未实现[/yellow]")
                
            elif choice == "3":
                info_lines = []
                if hasattr(device, 'weight'):
                    info_lines.append(f"食物重量: {device.weight}g")
                if hasattr(device, 'state'):
                    info_lines.append(f"状态: {device.state}")
                
                if info_lines:
                    food_panel = Panel(
                        "\n".join(info_lines),
                        title="喂食器状态",
                        box=box.ROUNDED
                    )
                    console.print(food_panel)
                else:
                    console.print("[yellow]无可用的喂食器状态[/yellow]")
                
            elif choice == "4":
                break

    async def interactive_menu(self):
        """Main interactive menu."""
        while True:
            console.print("\n[bold]主菜单:[/bold]")
            console.print("1. 显示所有设备")
            console.print("2. 控制设备")
            console.print("3. 检查耗材状态")
            console.print("4. 配置监控提醒")
            console.print("5. 刷新设备状态")
            console.print("6. 退出")
            
            choice = Prompt.ask("请选择", choices=["1", "2", "3", "4", "5", "6"])
            
            if choice == "1":
                await self.show_devices()
                
            elif choice == "2":
                if not self.devices:
                    console.print("[yellow]没有可用设备[/yellow]")
                    continue
                    
                # Select device
                device_choices = {str(i+1): device for i, device in enumerate(self.devices)}
                console.print("\n[bold]选择设备:[/bold]")
                for idx, device in device_choices.items():
                    console.print(f"{idx}. {device.name} ({device.type})")
                
                device_choice = Prompt.ask("选择设备", choices=list(device_choices.keys()))
                selected_device = device_choices[device_choice]
                
                await self.show_device_details(selected_device)
                
                # Device-specific controls
                if isinstance(selected_device, (LitterBox, ScooperDevice)):
                    await self.control_litter_box(selected_device)
                elif isinstance(selected_device, FeederDevice):
                    await self.control_feeder(selected_device)
                else:
                    console.print("[yellow]此设备类型无可用控制[/yellow]")
                    
            elif choice == "3":
                # 检查耗材状态
                await self.check_supplies_status()
                
            elif choice == "4":
                # 配置监控提醒
                console.print("\n[bold]监控配置说明:[/bold]")
                console.print("1. 创建 config.toml 配置文件")
                console.print("2. 配置钉钉机器人的 webhook 和 secret（可选）")
                console.print("3. 设置监控参数（检查间隔、提醒阈值等）")
                console.print("4. 运行命令: python cli.py --monitor -c config.toml")
                console.print("\n[yellow]提示: 使用 --monitor --test 可以测试钉钉配置[/yellow]")
                
            elif choice == "5":
                with console.status("正在刷新设备..."):
                    assert self.client is not None  # 确保已连接
                    self.devices = await self.client.get_devices()
                console.print("[green]✓ 设备已刷新[/green]")
                
            elif choice == "6":
                break
    
    async def check_supplies_status(self):
        """检查所有设备的耗材状态"""
        if not self.devices:
            console.print("[yellow]没有可用设备[/yellow]")
            return
            
        supplies_table = Table(title="耗材状态", box=box.ROUNDED)
        supplies_table.add_column("设备名称", style="cyan")
        supplies_table.add_column("猫砂剩余", style="magenta")
        supplies_table.add_column("除臭剂剩余", style="green")
        supplies_table.add_column("状态", style="yellow")
        
        for device in self.devices:
            if isinstance(device, (LitterBox, ScooperDevice)):
                litter_days = "N/A"
                deodorant_days = "N/A"
                status = "正常"
                
                try:
                    if hasattr(device, 'litter_remaining_days') and device.litter_remaining_days is not None:
                        litter_days = f"{device.litter_remaining_days}天"
                        if device.litter_remaining_days <= 0:
                            status = "⚠️ 需补充"
                except:
                    pass
                    
                try:
                    if hasattr(device, 'deodorant_countdown') and device.deodorant_countdown is not None:
                        deodorant_days = f"{device.deodorant_countdown}天"
                        if device.deodorant_countdown <= 0:
                            status = "⚠️ 需补充"
                except:
                    pass
                
                supplies_table.add_row(
                    device.name,
                    litter_days,
                    deodorant_days,
                    status
                )
        
        console.print(supplies_table)

    async def show_all_device_status(self):
        """Show status for all devices without interaction."""
        await self.show_devices()
        console.print()
        
        for device in self.devices:
            await self.show_device_details(device)
            console.print()
            
            # Show recent events if available
            if hasattr(device, 'get_events'):
                events = device.get_events()  # type: ignore[attr-defined]
                if events:
                    console.print(f"[bold]{device.name} 的最近事件:[/bold]")
                    event_table = Table(box=box.SIMPLE)
                    event_table.add_column("时间", style="cyan")
                    event_table.add_column("事件", style="yellow")
                    
                    for event in events[:5]:  # Show last 5 events
                        event_table.add_row(
                            event.get('time', '未知'),
                            event.get('event', '未知事件')
                        )
                    
                    console.print(event_table)
                    console.print()

    async def run(self, status_only: bool = False):
        """Run the demo application."""
        try:
            await self.connect()
            if status_only:
                await self.show_all_device_status()
            else:
                await self.interactive_menu()
        except Exception as e:
            import traceback
            console.print(f"[red]Error: {e}[/red]")
            console.print(f"[red]{traceback.format_exc()}[/red]")
        finally:
            if self.client:
                await self.client.close()
                console.print("[green]✓ 连接已关闭[/green]")


async def main():
    parser = argparse.ArgumentParser(
        description="CatLink SDK 示例 - 控制您的 CatLink 设备",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python cli.py -u 13800138000 -p mypassword
  python cli.py -u 13800138000 --status  # 仅显示设备状态
  python cli.py --username 13800138000  # 将提示输入密码
  python cli.py -c config.toml  # 从配置文件读取账号信息
  
监控模式:
  python cli.py --monitor -c config.toml  # 运行监控模式
  python cli.py --monitor --test -c config.toml  # 测试钉钉配置
        """
    )
    
    parser.add_argument(
        "-u", "--username",
        help="您的 CatLink 账户手机号"
    )
    
    parser.add_argument(
        "-p", "--password",
        help="您的 CatLink 账户密码 (如果不提供将提示输入)"
    )
    
    parser.add_argument(
        "-s", "--status",
        action="store_true",
        help="仅显示设备状态而不进入交互式菜单"
    )
    
    # 监控相关参数
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="运行监控模式（需要配置文件）"
    )
    
    parser.add_argument(
        "-c", "--config",
        default="config.toml",
        help="配置文件路径 (默认: config.toml)"
    )
    
    parser.add_argument(
        "-t", "--test",
        action="store_true",
        help="测试模式 - 测试钉钉消息发送"
    )
    
    args = parser.parse_args()
    
    # 监控模式
    if args.monitor:
        monitor = CatLinkMonitor(args.config)
        
        if args.test:
            # 测试模式
            await monitor.connect()
            await monitor.send_dingtalk_message(
                "🧪 CatLink监控测试",
                "## 测试消息\n\n这是一条测试消息，确认钉钉机器人配置正确。\n\n✅ 配置正常"
            )
            if monitor.client:
                await monitor.client.close()
        else:
            # 正常运行
            await monitor.run()
    else:
        # 交互模式
        if not args.username:
            # 尝试从配置文件读取
            if args.config:
                try:
                    config_path = Path(args.config)
                    if config_path.exists():
                        config = toml.load(config_path)
                        catlink_config = config.get("catlink", {})
                        args.username = catlink_config.get("username")
                        if not args.password:
                            args.password = catlink_config.get("password")
                except Exception as e:
                    logger.debug(f"无法从配置文件读取账号信息: {e}")
            
            if not args.username:
                parser.error("交互模式需要提供用户名 (-u/--username) 或在配置文件中设置")
        
        # Get password if not provided
        password = args.password
        if not password:
            password = getpass("请输入您的 CatLink 密码: ")
        
        # Display welcome message
        welcome_panel = Panel(
            "[bold cyan]CatLink SDK 演示程序[/bold cyan]\n"
            "控制您的智能宠物设备",
            box=box.DOUBLE,
            expand=False
        )
        console.print(welcome_panel)
        
        # Run the demo
        demo = CatLinkDemo(phone=args.username, password=password)
        await demo.run(status_only=args.status)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]用户中断[/yellow]")
        sys.exit(0)