"""WebSocket Client - Real-time event streaming."""

import asyncio, json, os
import websockets
from dotenv import load_dotenv

load_dotenv()

WS_URL = os.getenv("PROPR_WS_URL", "wss://api.propr.xyz/ws")
API_KEY = os.getenv("PROPR_API_KEY")

async def listen():
    async with websockets.connect(
        WS_URL,
        additional_headers={"X-API-Key": API_KEY},
        ping_interval=20, ping_timeout=10,
    ) as ws:
        async for raw in ws:
            msg = json.loads(raw)
            event_type = msg.get("type")
            data = msg.get("data", msg)

            if event_type == "position.updated":
                print(f"Position: {data.get('base')} uPnL={data.get('unrealizedPnl')}")
            elif event_type == "order.filled":
                print(f"Filled: {data.get('side')} {data.get('base')} @ {data.get('averageFillPrice')}")
            elif event_type == "trade.created":
                print(f"Trade: {data.get('type')} {data.get('quantity')} {data.get('base')}")

asyncio.run(listen())
