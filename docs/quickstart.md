# Bot Quickstart (Python)

```python
import os
import requests
from ulid import ULID
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.propr.xyz/v1"

# Step 1: Load your API key from environment
# Get your key at https://app.propr.xyz/settings
API_KEY = os.getenv("PROPR_API_KEY")

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Step 2: Check health
r = requests.get(f"{BASE_URL}/health")
print(r.json())  # {"status": "OK"}

# Step 3: Get your user profile
r = requests.get(f"{BASE_URL}/users/me", headers=headers)
print(r.json())

# Step 4: Get your account ID from challenge attempts
r = requests.get(f"{BASE_URL}/challenge-attempts", headers=headers)
attempts = r.json()
ACCOUNT_ID = attempts["data"][0]["accountId"]

# Step 5: Check positions
r = requests.get(
    f"{BASE_URL}/accounts/{ACCOUNT_ID}/positions",
    headers=headers
)
print(r.json())

# Step 6: Place a limit buy order
order = {
    "orders": [{
        "accountId": ACCOUNT_ID,
        "intentId": str(ULID()),
        "exchange": "hyperliquid",
        "type": "limit",
        "side": "buy",
        "positionSide": "long",
        "productType": "perp",
        "timeInForce": "GTC",
        "asset": "BTC/USDC",
        "base": "BTC",
        "quote": "USDC",
        "quantity": "0.001",
        "price": "90000"
    }]
}
r = requests.post(
    f"{BASE_URL}/accounts/{ACCOUNT_ID}/orders",
    json=order, headers=headers
)
print(r.json())

# Step 7: List and cancel open orders
r = requests.get(
    f"{BASE_URL}/accounts/{ACCOUNT_ID}/orders?status=open",
    headers=headers
)
open_orders = r.json()

if open_orders["data"]:
    order_id = open_orders["data"][0]["orderId"]
    r = requests.post(
        f"{BASE_URL}/accounts/{ACCOUNT_ID}/orders/{order_id}/cancel",
        headers=headers
    )
    print(r.json())
```

## AI Agent Quickstart

If you're using an AI coding agent to build your bot, give it this context to avoid common mistakes.

### Recommended API Client Pattern

```python
import os
import requests
from decimal import Decimal
from ulid import ULID

BASE_URL = "https://api.propr.xyz/v1"

class ProprClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("PROPR_API_KEY")
        self.account_id = None
        if not self.api_key:
            raise ValueError("Set PROPR_API_KEY env var or pass api_key")

    def _headers(self):
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def request(self, method, path, **kwargs):
        """Make an authenticated API request."""
        return requests.request(method, f"{BASE_URL}{path}",
                               headers=self._headers(), **kwargs)

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def setup(self):
        """Find account ID from active challenge attempt."""
        r = self.get("/challenge-attempts", params={"status": "active"})
        attempts = r.json()["data"]
        if not attempts:
            raise Exception("No active challenge. Purchase one first.")
        self.account_id = attempts[0]["accountId"]
        return self.account_id

    def place_order(self, side, position_side, order_type, quantity,
                    price=None, reduce_only=False, close_position=False):
        """Place a single order. Returns order data or None."""
        order = {
            "accountId": self.account_id,
            "intentId": str(ULID()),
            "exchange": "hyperliquid",
            "type": order_type,
            "side": side,
            "positionSide": position_side,
            "productType": "perp",
            "timeInForce": "IOC" if order_type == "market" else "GTC",
            "asset": "BTC/USDC",
            "base": "BTC",
            "quote": "USDC",
            "quantity": str(quantity),
            "reduceOnly": reduce_only,
            "closePosition": close_position,
        }
        if price is not None:
            order["price"] = str(price)

        r = self.post(f"/accounts/{self.account_id}/orders",
                      json={"orders": [order]})
        if r.status_code in (200, 201):
            return r.json()["data"]
        return None

    def get_positions(self, base="BTC", status="open"):
        """Get open positions, filtering out zero-quantity entries."""
        r = self.get(f"/accounts/{self.account_id}/positions",
                    params={"base": base, "status": status})
        if r.status_code == 200:
            return [p for p in r.json()["data"]
                    if Decimal(p["quantity"]) > 0]
        return []

    def cancel_order(self, order_id):
        """Cancel an order. Returns True if cancelled, False if already done."""
        r = self.post(
            f"/accounts/{self.account_id}/orders/{order_id}/cancel")
        return r.status_code in (200, 201)
```

### Usage

```python
client = ProprClient()  # reads PROPR_API_KEY from env
client.setup()

# Place a market buy
client.place_order("buy", "long", "market", quantity="0.001")

# Place a limit sell
client.place_order("sell", "long", "limit", quantity="0.001",
                   price="70000", reduce_only=True)

# Check positions
positions = client.get_positions()
for p in positions:
    print(f"{p['positionSide']} {p['quantity']} @ {p['entryPrice']}")
```

### Key Rules for AI Agents Building Bots

1. Load your API key from environment variables. Never hardcode it in your source code.
2. Use Decimal for all monetary math. Never use float.
3. Generate a new ULID for every order: `from ulid import ULID; str(ULID())`
4. Set `reduceOnly: true` on every closing/reducing order. Without it, you'll accidentally open opposing positions.
5. Accept 201 as success for both create and cancel endpoints.
6. Track your own exposure internally. Positions merge, so you can't distinguish bot fills from manual trades by reading positions.
7. Filter positions by `quantity != "0"`. Closed positions may linger with zero quantity.
8. Use `timeInForce: "IOC"` for market orders. Prevents them from resting on the book.

## Tips for Bot Development

### Authentication
1. Store your API key in environment variables. Use a `.env` file locally and set env vars in your deployment platform (Railway, Render, etc.). Never commit your key to version control.
2. You get one API key per account. Generate it at [Settings](https://app.propr.xyz/settings). If compromised, regenerate it from the same page.

### Orders
3. Always generate a unique intentId (ULID format) per order for idempotency. Reusing the same intentId will not place a duplicate order. Use this as a safety mechanism against double sends.
4. Use `timeInForce: "IOC"` for market orders. Immediate or Cancel ensures your market order either fills instantly or is cancelled.
5. Always set `reduceOnly: true` when closing positions. Without it, a sell on a long position may open a new short position instead of reducing the long. This is the most common bot mistake.
6. The cancel endpoint returns 201, not 200. Treat both 200 and 201 as success. A 400 on cancel means the order was already filled or cancelled (safe to ignore).

### Positions
7. Positions merge on the same asset/side. Three separate BUY BTC orders create one position with combined quantity. Track your bot's exposure internally rather than relying on position counts.
8. Filter out zero quantity positions. Fully closed positions may still appear with `quantity: "0"`. Always check `quantity != "0"` when listing active positions.
9. Use markPrice from WebSocket for real time pricing. The markPrice returned by REST may lag behind the market.

### Data
10. All monetary values are strings (decimal precision). Avoid floating point math. Use Decimal in Python, BigNumber in JavaScript, or equivalent.
11. Your accountId is linked to your challenge attempt. Find it via `GET /challenge-attempts`. Each challenge attempt creates a new account.
12. Challenge rules are enforced server side. Max drawdown, daily loss limits, and leverage limits are all checked on the server.

### Monitoring
13. Use WebSocket for real time updates instead of polling REST endpoints. Subscribe once and receive `order.filled`, `position.updated`, and `trade.created` events as they happen.
14. Always check `GET /health/services` before starting a trading session. If core is not "OK", do not trade.
