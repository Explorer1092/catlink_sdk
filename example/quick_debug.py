import asyncio, json, logging
from catlink_sdk import CatLinkClient
from catlink_sdk.models.litterbox import LitterBox
from catlink_sdk.models.scooper import ScooperDevice

logging.basicConfig(level=logging.DEBUG)   # 打开 SDK 调试日志

async def main():
    client = CatLinkClient(phone="", password="")
    await client.authenticate()
    devices = await client.get_devices()
    for d in devices:
        if isinstance(d, (LitterBox, ScooperDevice)):
            await d.update_device_detail()        # 触发 detail 接口
            print(f"\n=== {d.name} ({d.id}) ===")
            print(json.dumps(d.detail, indent=2, ensure_ascii=False))
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())