# Propr Python SDK

Official Python client for the Propr trading API.

**Python 3.9+** | Package: `propr-sdk`

## Installation

```bash
pip install requests python-ulid websockets python-dotenv
```

Create a `.env` file in your project root:

```bash
PROPR_API_KEY=pk_live_your_api_key_here
PROPR_API_URL=https://api.propr.xyz/v1
PROPR_WS_URL=wss://api.propr.xyz/ws
```

Get your API key from [Settings](https://app.propr.xyz/settings).

## Quick Start

```python
from propr_sdk import ProprClient

client = ProprClient()  # reads PROPR_API_KEY from .env
client.setup()          # finds your active challenge account

# Check your positions
positions = client.get_open_positions()
for p in positions:
    print(f"{p['positionSide']} {p['quantity']} {p['base']} @ {p['entryPrice']}")

# Place a market buy
orders = client.market_buy("BTC", "0.001")
print(f"Order placed: {orders[0]['orderId']}")
```

## API Reference

### Constructor

```python
client = ProprClient(
    api_key="pk_live_...",      # or set PROPR_API_KEY env var
    base_url="https://...",     # or set PROPR_API_URL env var
    timeout=30,                 # request timeout in seconds
)
```

### Setup

| Method | Description |
|--------|-------------|
| `client.setup()` | Auto detect account ID from active challenge |
| `client.setup(account_id="...")` | Use a specific account ID |

### Health

| Method | Auth | Returns |
|--------|------|---------|
| `client.health()` | No | `{"status": "OK"}` |
| `client.health_services()` | No | `{"core": "OK" \| "ERROR"}` |

### User

| Method | Auth | Returns |
|--------|------|---------|
| `client.get_user()` | Yes | User profile dict |

### Challenges

| Method | Auth | Returns |
|--------|------|---------|
| `client.get_challenges()` | No | List of challenge dicts |
| `client.get_challenge_attempts(status="active")` | Yes | List of attempt dicts |
| `client.get_challenge_attempt(attempt_id)` | Yes | Single attempt dict |

### Orders

| Method | Description |
|--------|-------------|
| `client.get_orders(status="open")` | List orders with optional filters |
| `client.create_order(side, position_side, order_type, asset, base, quote, quantity, ...)` | Place a single order |
| `client.create_orders([{...}, {...}])` | Place multiple orders in batch |
| `client.cancel_order(order_id)` | Cancel a specific order |
| `client.cancel_all_orders(base="BTC")` | Cancel all open orders |

### Convenience Order Methods

| Method | Description |
|--------|-------------|
| `client.market_buy("BTC", "0.001")` | Market buy (long) |
| `client.market_sell("BTC", "0.001")` | Market sell (close long, reduce_only=True) |
| `client.limit_buy("BTC", "0.001", "90000")` | Limit buy (long) |
| `client.limit_sell("BTC", "0.001", "100000")` | Limit sell (close, reduce_only=True) |
| `client.close_position("BTC")` | Close entire position (auto detects side) |

### Positions

| Method | Description |
|--------|-------------|
| `client.get_positions(base="BTC", status="open")` | List positions with filters |
| `client.get_open_positions()` | Get all open non zero positions |
| `client.get_open_positions(base="ETH")` | Get open positions for specific asset |

### Trades

| Method | Description |
|--------|-------------|
| `client.get_trades(base="BTC")` | List trade executions with filters |

### Margin & Leverage

| Method | Description |
|--------|-------------|
| `client.get_margin_config("BTC")` | Get margin config for an asset |
| `client.set_leverage("BTC", 5)` | Set leverage (creates/updates config) |
| `client.get_leverage_limits()` | Get max leverage limits for all assets |
| `client.max_leverage("BTC")` | Get max leverage for a specific asset |

## Error Handling

```python
from propr_sdk import ProprClient, ProprAPIError

client = ProprClient()
client.setup()

try:
    orders = client.market_buy("BTC", "0.001")
except ProprAPIError as e:
    print(f"API Error: status={e.status_code} code={e.code} message={e.message}")

    if e.status_code == 429:
        print("Rate limited - slow down")
    elif e.status_code == 400:
        print("Bad request - check order parameters")
    elif e.status_code == 401:
        print("Invalid API key")
except Exception as e:
    print(f"Unexpected error: {e}")
```

| Status | Meaning | Action |
|--------|---------|--------|
| 400 | Bad request / validation | Check parameters |
| 401 | Invalid API key | Check PROPR_API_KEY |
| 403 | Forbidden | Check account ownership |
| 404 | Not found | Check resource ID |
| 429 | Rate limited | Slow down (1200 req/min) |
| 500 | Server error | Retry or check health |

## Examples

See the [`examples/`](examples/) directory for complete working examples:

- **Grid Bot** - Place a grid of limit orders around the current price
- **DCA Bot** - Dollar cost average into a position over time
- **Portfolio Monitor** - Print a summary of all open positions
- **Stop Loss + Take Profit** - Open a position with SL/TP orders
- **WebSocket Client** - Real time event streaming
