#!/usr/bin/env python3
"""
CatLink SDK Example CLI Application

This example demonstrates how to use the CatLink SDK with command-line arguments
for authentication and various device control features.
"""

import asyncio
import argparse
import sys
from getpass import getpass
from typing import Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich.prompt import Prompt, Confirm
from rich import box

from catlink_sdk import CatLinkClient, AdditionalDeviceConfig
from catlink_sdk.models.device import Device
from catlink_sdk.models.litterbox import LitterBox
from catlink_sdk.models.feeder import FeederDevice
from catlink_sdk.models.scooper import ScooperDevice

console = Console()


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
        table.add_column("电量", style="yellow")

        for device in self.devices:
            online_status = "✓ 在线" if device.online else "✗ 离线"
            power_status = f"{getattr(device, 'power', 'N/A')}{'%' if hasattr(device, 'power') else ''}"
            
            table.add_row(
                device.id,
                device.name,
                device.type,
                online_status,
                power_status
            )

        console.print(table)

    async def show_device_details(self, device: Device):
        """Show detailed information for a specific device."""
        details = []
        
        # Common details
        details.append(f"[cyan]设备ID:[/cyan] {device.id}")
        details.append(f"[cyan]设备名称:[/cyan] {device.name}")
        details.append(f"[cyan]设备类型:[/cyan] {device.type}")
        details.append(f"[cyan]设备型号:[/cyan] {device.model}")
        details.append(f"[cyan]在线状态:[/cyan] {'[green]在线[/green]' if device.online else '[red]离线[/red]'}")
        details.append(f"[cyan]电量:[/cyan] {getattr(device, 'power', '不支持')}{'%' if hasattr(device, 'power') else ''}")
        
        # Device-specific details
        if isinstance(device, (LitterBox, ScooperDevice)):
            if hasattr(device, 'mode'):
                details.append(f"[cyan]工作模式:[/cyan] {device.mode}")
            if hasattr(device, 'occupied'):
                details.append(f"[cyan]占用状态:[/cyan] {'[yellow]有猫使用[/yellow]' if device.occupied else '[green]空闲[/green]'}")
            if hasattr(device, 'litter_weight'):
                details.append(f"[cyan]猫砂重量:[/cyan] {device.litter_weight:.2f} kg")
            if hasattr(device, 'temperature'):
                details.append(f"[cyan]环境温度:[/cyan] {device.temperature}°C")
            if hasattr(device, 'humidity'):
                details.append(f"[cyan]环境湿度:[/cyan] {device.humidity}%")
            
            if hasattr(device, 'last_clean_time') and device.last_clean_time:
                details.append(f"[cyan]上次清理:[/cyan] {device.last_clean_time}")
            elif hasattr(device, 'manual_clean_time') and device.manual_clean_time:
                details.append(f"[cyan]手动清理时间:[/cyan] {device.manual_clean_time}")
            
            if hasattr(device, 'deodorant_left_days'):
                details.append(f"[cyan]除臭剂剩余:[/cyan] {device.deodorant_left_days} 天")
                
            if hasattr(device, 'total_uses'):
                details.append(f"[cyan]总使用次数:[/cyan] {device.total_uses}")
            if hasattr(device, 'today_uses'):
                details.append(f"[cyan]今日使用:[/cyan] {device.today_uses} 次")
            if hasattr(device, 'avg_use_time'):
                details.append(f"[cyan]平均使用时长:[/cyan] {device.avg_use_time} 秒")
        
        elif isinstance(device, FeederDevice):
            if hasattr(device, 'weight'):
                details.append(f"[cyan]食物重量:[/cyan] {device.weight}g")
            if hasattr(device, 'state'):
                details.append(f"[cyan]状态:[/cyan] {device.state}")
            if hasattr(device, 'last_log'):
                details.append(f"[cyan]最后活动:[/cyan] {device.last_log}")

        panel = Panel("\n".join(details), title=f"🐱 {device.name}", box=box.ROUNDED)
        console.print(panel)

    async def control_litter_box(self, device: LitterBox):
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
            console.print("3. 刷新设备状态")
            console.print("4. 退出")
            
            choice = Prompt.ask("请选择", choices=["1", "2", "3", "4"])
            
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
                with console.status("正在刷新设备..."):
                    self.devices = await self.client.get_devices()
                console.print("[green]✓ 设备已刷新[/green]")
                
            elif choice == "4":
                break

    async def show_all_device_status(self):
        """Show status for all devices without interaction."""
        await self.show_devices()
        console.print()
        
        for device in self.devices:
            await self.show_device_details(device)
            console.print()
            
            # Show recent events if available
            if hasattr(device, 'get_events'):
                events = device.get_events()
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
  python example.py -u 13800138000 -p mypassword
  python example.py -u 13800138000 --status  # 仅显示设备状态
  python example.py --username 13800138000  # 将提示输入密码
        """
    )
    
    parser.add_argument(
        "-u", "--username",
        required=True,
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
    
    args = parser.parse_args()
    
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