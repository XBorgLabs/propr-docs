# WebSocket (Real Time)

## Connection

```
wss://api.propr.xyz/ws
# Connect with header: X-API-Key: <your_api_key>
```

On success you'll receive:

```json
{ "type": "connected", "data": { "userId": "..." } }
```

Heartbeat: Server pings every 20 seconds. Dead connections are terminated automatically.

## Environment Variables

```bash
PROPR_API_KEY=pk_live_your_api_key_here
# PROPR_WS_URL=wss://api.propr.xyz/ws
```

## Events

All events follow this format:

```json
{
  "type": "order.filled",
  "userId": "...",
  "data": { ... },
  "timestamp": 1709136000000
}
```

| Event | Description |
|-------|-------------|
| `account.updated` | Balance/margin changed |
| `order.created` | New order placed |
| `order.updated` | Order state changed |
| `order.cancelled` | Order cancelled |
| `order.triggered` | Conditional order triggered |
| `order.filled` | Order fully filled |
| `order.partially_filled` | Order partially filled |
| `position.opened` | New position opened |
| `position.updated` | Position metrics changed |
| `position.closed` | Position closed |
| `position.liquidated` | Position liquidated |
| `position.take_profit.hit` | Take profit reached |
| `position.stop_loss.hit` | Stop loss triggered |
| `trade.created` | New trade execution |

## Python Client Example

Full async client with all 14 event handlers and reconnect logic:

```python
import asyncio, json, os, sys
from datetime import datetime
import websockets
from dotenv import load_dotenv

load_dotenv()

WS_URL = os.getenv("PROPR_WS_URL", "wss://api.propr.xyz/ws")
API_KEY = os.getenv("PROPR_API_KEY")
RECONNECT_DELAY = 5

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] {msg}")

# Event Handlers
EVENT_HANDLERS = {
    "connected":              lambda d: log(f"Connected — userId: {d.get('userId')}"),
    "account.updated":        lambda d: log(f"Account updated — balance: {d.get('balance')}"),
    "order.created":          lambda d: log(f"Order CREATED — {d.get('side','?').upper()} "
                                            f"{d.get('quantity')} {d.get('base')} @ {d.get('price','market')}"),
    "order.updated":          lambda d: log(f"Order UPDATED — status={d.get('status')} id={d.get('orderId')}"),
    "order.cancelled":        lambda d: log(f"Order CANCELLED — id={d.get('orderId')}"),
    "order.triggered":        lambda d: log(f"Order TRIGGERED — {d.get('type')} id={d.get('orderId')}"),
    "order.filled":           lambda d: log(f"Order FILLED — {d.get('side','?').upper()} "
                                            f"{d.get('cumulativeQuantity')} {d.get('base')} "
                                            f"@ avg {d.get('averageFillPrice')}"),
    "order.partially_filled": lambda d: log(f"Order PARTIAL — {d.get('cumulativeQuantity')}/"
                                            f"{d.get('quantity')} filled"),
    "position.opened":        lambda d: log(f"Position OPENED — {d.get('positionSide','?').upper()} "
                                            f"{d.get('quantity')} {d.get('base')} @ {d.get('entryPrice')}"),
    "position.updated":       lambda d: log(f"Position UPDATED — mark: {d.get('markPrice')} "
                                            f"uPnL: {d.get('unrealizedPnl')}"),
    "position.closed":        lambda d: log(f"Position CLOSED — PnL: {d.get('realizedPnl')} USDC"),
    "position.liquidated":    lambda d: log(f"LIQUIDATED — {d.get('base')} loss: {d.get('realizedPnl')}"),
    "position.take_profit.hit": lambda d: log(f"TP HIT — PnL: {d.get('realizedPnl')}"),
    "position.stop_loss.hit": lambda d: log(f"SL HIT — PnL: {d.get('realizedPnl')}"),
    "trade.created":          lambda d: log(f"Trade — {d.get('type')} {d.get('side','?').upper()} "
                                            f"{d.get('quantity')} {d.get('base')} @ {d.get('price')}"),
}

async def listen(ws):
    async for raw in ws:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue
        handler = EVENT_HANDLERS.get(msg.get("type"))
        if handler:
            handler(msg.get("data", msg))
        else:
            log(f"Unhandled: {msg.get('type')}")

async def connect_and_listen():
    if not API_KEY:
        sys.exit("Set PROPR_API_KEY in .env")
    while True:
        try:
            async with websockets.connect(
                WS_URL,
                additional_headers={"X-API-Key": API_KEY},
                ping_interval=20, ping_timeout=10
            ) as ws:
                log("Listening for events...")
                await listen(ws)
        except websockets.ConnectionClosed as e:
            log(f"Disconnected: {e}")
        log(f"Reconnecting in {RECONNECT_DELAY}s...")
        await asyncio.sleep(RECONNECT_DELAY)

if __name__ == "__main__":
    asyncio.run(connect_and_listen())
```

## JavaScript Client Example

Using the `ws` package (Node.js):

```javascript
// npm install ws
import WebSocket from 'ws';

const WS_URL = process.env.PROPR_WS_URL || 'wss://api.propr.xyz/ws';
const API_KEY = process.env.PROPR_API_KEY;

function connect() {
  const ws = new WebSocket(WS_URL, {
    headers: { 'X-API-Key': API_KEY },
  });

  ws.on('open', () => console.log('Connected'));

  ws.on('message', (raw) => {
    const msg = JSON.parse(raw.toString());
    const { type, data } = msg;

    switch (type) {
      case 'connected':
        console.log(`Authenticated: ${data.userId}`);
        break;
      case 'position.updated':
        console.log(`Position: ${data.base} uPnL=${data.unrealizedPnl}`);
        break;
      case 'order.filled':
        console.log(`Filled: ${data.side} ${data.base} @ ${data.averageFillPrice}`);
        break;
      case 'trade.created':
        console.log(`Trade: ${data.type} ${data.quantity} ${data.base}`);
        break;
      default:
        console.log(`Event: ${type}`);
    }
  });

  ws.on('close', () => {
    console.log('Disconnected, reconnecting in 5s...');
    setTimeout(connect, 5000);
  });

  ws.on('error', (err) => console.error('WS error:', err.message));
}

connect();
```
