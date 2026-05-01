# Bot API Documentation

Everything you need to build a trading bot on Propr.

## Base URLs

| Environment | REST API | WebSocket |
|-------------|----------|-----------|
| **Live** | `https://api.propr.xyz/v1` | `wss://api.propr.xyz/ws` |
| **Beta** | `https://api.beta.propr.xyz/v1` | `wss://api.beta.propr.xyz/ws` |

## Authentication

### Get Your API Key

1. Go to [app.propr.xyz](https://app.propr.xyz) and create an account / log in with Google
2. Navigate to [Settings](https://app.propr.xyz/settings)
3. Generate an API key (starts with `pk_live_`)

Include your API key in the `X-API-Key` header on all authenticated requests:

```bash
curl -H "X-API-Key: <your_api_key>" \
  https://api.propr.xyz/v1/users/me
```

| Property | Value |
|----------|-------|
| Header | `X-API-Key: pk_live_...` |
| Rate limit | 1,200 requests/min |
| Keys per user | 1 (regenerate from Settings if compromised) |
| Scope | Full account access (orders, positions, trades) |

> **Keep your API key secret.** Do not commit it to version control or share it publicly. Use environment variables to store it in your bot.

---

## Getting Started: Purchase a Challenge

Before you can trade via the API, you need an active challenge. A challenge gives you a funded trading account with specific rules (max drawdown, daily loss limits, leverage caps). Here's how to get one:

1. Create an account at [app.propr.xyz](https://app.propr.xyz) (Google sign in)
2. Go to [app.propr.xyz/dashboard](https://app.propr.xyz/dashboard)
3. Browse available challenges (different account sizes, durations, and rules)
4. Click **Get Started** on the challenge you want
5. Complete the Stripe checkout to purchase
6. Once purchased, your challenge attempt is created with a linked `accountId`

You can also list available challenges programmatically via `GET /challenges` (no auth required) to see pricing, rules, and configuration before purchasing through the app.

After purchase, retrieve your `accountId` via `GET /challenge-attempts?status=active`. This account ID is required for all trading endpoints (`/accounts/{accountId}/orders`, `/accounts/{accountId}/positions`, etc.).

> Each challenge attempt creates a new trading account. If you fail a challenge and purchase again, you'll get a new `accountId`.

---

## Health Check (No Auth)

Always check health before trading. No authentication required.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Returns `{ "status": "OK" }` |
| `GET` | `/health/services` | Returns `{ "core": "OK" \| "ERROR" }` |

---

## User Profile (Auth Required)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/users/me` | Get the current authenticated user's profile |

---

## Challenges (No Auth)

> **Getting Started:** You must purchase a challenge before you can trade via the API. Go to [app.propr.xyz/dashboard](https://app.propr.xyz/dashboard), click **Get Started** on a challenge, and complete the Stripe checkout.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/challenges` | List all available challenges and their configuration |

**Query params:**

| Param | Description |
|-------|-------------|
| `challengeId` | Filter by challenge ID |
| `productId` | Filter by product ID |
| `currency` | Filter by currency |
| `exchange` | Filter by exchange |
| `limit` | Results per page (default 20) |
| `offset` | Pagination offset (default 0) |

Response includes: challenge name, description, exchange (hyperliquid), duration, initial balance, max daily loss %, max drawdown %, leverage limits, phases, rewards, and pricing.

---

## Challenge Attempts (Auth Required)

Your challenge progress. Your `accountId` (needed for all trading endpoints) is found here.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/challenge-attempts` | List your challenge attempts |
| `GET` | `/challenge-attempts/{attemptId}` | Get specific attempt details |

**Query params:** `attemptId`, `challengeId`, `status` (active/passed/failed), `limit`, `offset`

Response includes: status, total profit/loss, win rate, max drawdown, trading days, failure reason, linked accountId, current phase.

**Failure reasons:** `max_drawdown_exceeded`, `max_daily_loss_exceeded`, `profit_target_not_met`

---

## Orders (Auth Required)

All trading endpoints follow the pattern `/accounts/{accountId}/...` and require auth. You must own the account.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/accounts/{accountId}/orders` | List all orders on the account |
| `POST` | `/accounts/{accountId}/orders` | Create order(s) |
| `POST` | `/accounts/{accountId}/orders/{orderId}/cancel` | Cancel an order |

### Create Order Request

```json
{
  "orders": [
    {
      "accountId": "your-account-id",
      "intentId": "unique-ulid-you-generate",
      "exchange": "hyperliquid",
      "type": "limit",
      "side": "buy",
      "positionSide": "long",
      "productType": "perp",
      "timeInForce": "GTC",
      "asset": "BTC",
      "base": "BTC",
      "quote": "USDC",
      "quantity": "0.001",
      "price": "95000",
      "reduceOnly": false,
      "closePosition": false
    }
  ]
}
```

> **Important:** `intentId` must be a unique ULID you generate per order. Same intentId = idempotent (same order won't be placed twice).

> **Asset format:** Use the symbol only (e.g. `"BTC"`, `"ETH"`, `"SOL"`), not the pair. Passing `"BTC/USDC"` will return `13450 EXCHANGE_ASSET_NOT_FOUND`. See the [Available Assets](#available-assets) table for the full list. For HIP-3 assets, include the `xyz:` prefix (e.g. `"xyz:AAPL"`).

### Batching and Conditional Order Rules

A few request-shape rules that are enforced server side:

| Rule | When it applies | Error code |
|------|-----------------|------------|
| Top-level `orderGroupId` is required | `orders.length > 1` | `13059 ORDER_VALIDATION_GROUP_ID_REQUIRED` |
| Conditional orders (`stop_market`, `stop_limit`, `take_profit_market`, `take_profit_limit`) need a `positionId` on the order, OR must be in the same group as an entry order | Standalone conditional, or group with no entry order | `13056 CONDITIONAL_ORDER_REQUIRES_POSITION_OR_GROUP` |
| Only one entry order (`market`, `limit`) per request | Multiple entries in one `orders` array | `13066 MULTIPLE_ENTRY_ORDERS` |
| `orderGroupId` must be a valid ULID you generate | Provided but malformed | `13061 INVALID_GROUP_ID` |

**Attaching SL/TP to an open position** (the common case for bots):

```json
{
  "orders": [
    {
      "intentId": "01K...",
      "positionId": "urn:prp-position:...",
      "type": "stop_market",
      "side": "sell",
      "positionSide": "long",
      "asset": "BTC",
      "base": "BTC",
      "quote": "USDC",
      "quantity": "0.001",
      "triggerPrice": "90000",
      "reduceOnly": true,
      "exchange": "hyperliquid",
      "productType": "perp",
      "timeInForce": "GTC"
    }
  ]
}
```

Single order, no `orderGroupId` needed. Partial-quantity laddered SL/TP on the same position is supported: submit each leg as its own request (or batch them under one `orderGroupId`).

### Create Order Response (201)

```json
{
  "data": [
    {
      "orderId": "urn:prp-order:2z4EkWgopowT",
      "intentId": "01KJJ0N8CJW89K0Q6SX50KZW27",
      "orderGroupId": null,
      "exchangeOrderId": null,
      "userId": "urn:prp-user:...",
      "accountId": "urn:prp-account:...",
      "positionId": null,
      "exchange": "hyperliquid",
      "productType": "perp",
      "asset": "BTC",
      "base": "BTC",
      "quote": "USDC",
      "type": "limit",
      "side": "buy",
      "positionSide": "long",
      "timeInForce": "GTC",
      "quantity": "0.001",
      "price": "50000",
      "triggerPrice": null,
      "closePosition": false,
      "cumulativeQuantity": "0",
      "cumulativeQuote": "0",
      "averageFillPrice": null,
      "cumulativeTradingFees": "0",
      "tradingFeeRate": "0.00075",
      "expiresAt": null,
      "filledAt": null,
      "cancelledAt": null,
      "status": "open",
      "reduceOnly": false,
      "createdAt": "2026-02-28T11:38:06.733Z",
      "updatedAt": "2026-02-28T11:38:06.733Z"
    }
  ]
}
```

> **Important:** The response `data` array contains one entry per order submitted. Market orders may already show `status: "filled"` in the response. Use the returned `orderId` to track and cancel orders.

### Cancel Order Response

Returns the cancelled order object on success.

| Code | Meaning |
|------|---------|
| 201 | Order successfully cancelled |
| 400 | Order cannot be cancelled (already filled, cancelled, or expired) |
| 401 | Unauthorized |
| 404 | Order not found |

> **Note:** The cancel endpoint returns `201` on success, not `200`. Bots should treat both `200` and `201` as successful cancellation. A `400` response means the order has already been filled, cancelled, or expired (safe to ignore).

### Order Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `orderId` | string | Unique order identifier (URN format) |
| `intentId` | string | Your ULID from the request |
| `orderGroupId` | string \| null | Group ID if part of a batch |
| `exchangeOrderId` | string \| null | Exchange assigned ID |
| `positionId` | string \| null | Linked position (null until filled) |
| `status` | string | Current order status |
| `cumulativeQuantity` | string | Total quantity filled so far |
| `cumulativeQuote` | string | Total quote value filled |
| `averageFillPrice` | string \| null | Weighted average fill price |
| `cumulativeTradingFees` | string | Total fees charged |
| `tradingFeeRate` | string | Fee rate applied (e.g., "0.00075" = 0.075%) |
| `filledAt` | string \| null | ISO timestamp when fully filled |
| `cancelledAt` | string \| null | ISO timestamp when cancelled |

### Order Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `market` | Executes immediately at best price | quantity |
| `limit` | Executes at specified price or better | quantity, price |
| `stop_market` | Triggers market order at trigger price | quantity, triggerPrice |
| `stop_limit` | Triggers limit order at trigger price | quantity, price, triggerPrice |
| `take_profit_market` | Take profit as market order | quantity, triggerPrice |
| `take_profit_limit` | Take profit as limit order | quantity, price, triggerPrice |

### Time In Force

| Value | Description |
|-------|-------------|
| `GTC` | Good Till Cancel (default) |
| `IOC` | Immediate or Cancel |
| `FOK` | Fill or Kill (all or nothing) |
| `GTX` | Good Till Crossing (post only / maker) |

### Order Statuses

```
pending -> open -> partially_filled -> filled
pending -> rejected
open -> cancelled / expired
```

### Closing Positions

There are two fields that control position reduction: `reduceOnly` and `closePosition`.

| Field | Effect |
|-------|--------|
| `reduceOnly: true` | Order can only reduce an existing position, never increase it. Rejects if no position exists to reduce. |
| `closePosition: true` | Closes the entire position. Use with `reduceOnly: true` for safety. |

To reduce a position by a specific amount:

```json
{
  "side": "sell",
  "positionSide": "long",
  "quantity": "0.001",
  "reduceOnly": true,
  "closePosition": false
}
```

To fully close a position:

```json
{
  "side": "sell",
  "positionSide": "long",
  "quantity": "1.003",
  "reduceOnly": true,
  "closePosition": true
}
```

> **Warning:** Selling without `reduceOnly: true` on an existing long position will open a separate short position instead of closing the long. Always set `reduceOnly: true` when you intend to close or reduce.

**GET orders query params:**

| Param | Description |
|-------|-------------|
| `orderId` | Filter by order ID |
| `tradeId` | Filter by trade ID |
| `positionId` | Filter by position ID |
| `base` | Filter by base asset |
| `quote` | Filter by quote asset |
| `side` | buy or sell |
| `status` | Filter by order status |
| `limit` | Results per page |
| `offset` | Pagination offset |

---

## Positions (Auth Required)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/accounts/{accountId}/positions` | List positions for the account |

**Query params:** `positionId`, `asset`, `base`, `quote`, `positionSide` (long/short), `status` (open/closed/liquidated), `limit`, `offset`

**Response fields:** `positionId`, `asset`, `positionSide`, `status`, `quantity`, `entryPrice`, `markPrice`, `liquidationPrice`, `unrealizedPnl`, `realizedPnl`, `marginUsed`, `leverage`, `marginMode`, `cumulativeFunding`, `cumulativeTradingFees`, `returnOnEquity`

### Position Behavior

**Position merging:** Multiple orders on the same asset and side merge into a single position. For example, three separate BUY 0.001 BTC orders will result in one position with `quantity: "0.003"` and a weighted average `entryPrice`. The `positionId` remains the same.

**Zero quantity positions:** When a position is fully closed, it may still appear in the API with `quantity: "0"` and `status: "open"` temporarily. Filter these out by checking `quantity != "0"` when listing active positions.

**Tracking bot exposure:** Because orders merge into existing positions, bots cannot distinguish their own fills from manually placed trades by looking at positions alone. Track your bot's net exposure internally by counting successful order fills rather than reading position quantities.

### Position Response

```json
{
  "data": [
    {
      "positionId": "urn:prp-position:HSS7U71q3Pjb",
      "userId": "urn:prp-user:...",
      "accountId": "urn:prp-account:...",
      "exchange": "hyperliquid",
      "productType": "perp",
      "status": "open",
      "asset": "BTC",
      "base": "BTC",
      "quote": "USDC",
      "positionSide": "long",
      "leverage": "1",
      "marginMode": "cross",
      "quantity": "1.003",
      "entryPrice": "64039.625524",
      "breakEvenPrice": "64087.942865",
      "markPrice": "64039",
      "liquidationPrice": "33972.404959",
      "unrealizedPnl": "-0.627401",
      "realizedPnl": "0.40657",
      "marginUsed": "64231.117",
      "notionalValue": "64231.117",
      "cumulativeFunding": "0",
      "cumulativeTradingFees": "48.462293",
      "tradingFeeRate": "0.00075",
      "returnOnEquity": "-0.00001",
      "createdAt": "2026-02-28T11:12:00.436Z",
      "updatedAt": "2026-02-28T11:37:20.032Z",
      "closedAt": null
    }
  ]
}
```

---

## Trades (Auth Required)

Execution history for your account.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/accounts/{accountId}/trades` | List trade executions |

**Query params:** `tradeId`, `positionId`, `orderId`, `base`, `quote`, `side`, `limit`, `offset`

**Trade types:** `open`, `increase`, `reduce`, `close`, `flip`, `liquidation`

**Liquidity types:** `maker`, `taker`

### Trade Response

```json
{
  "data": [
    {
      "tradeId": "urn:prp-trade:mFye8tSuvvow",
      "userId": "urn:prp-user:...",
      "accountId": "urn:prp-account:...",
      "orderId": "urn:prp-order:CjRJt6rhCHCT",
      "positionId": "urn:prp-position:HSS7U71q3Pjb",
      "exchangeTradeId": null,
      "transactionHash": null,
      "exchange": "hyperliquid",
      "productType": "perp",
      "type": "reduce",
      "liquidityType": "taker",
      "asset": "BTC",
      "base": "BTC",
      "quote": "USDC",
      "side": "sell",
      "positionSide": "long",
      "quantity": "0.001",
      "price": "64152",
      "quoteQuantity": "64.152",
      "fee": "0.048114",
      "feeAsset": "USDC",
      "feeRate": "0.00075",
      "leverage": "1",
      "marginMode": "cross",
      "realizedPnl": "0.112374476",
      "positionSizeBefore": "1.004",
      "slippage": "0",
      "markPriceAtOrder": "64152",
      "isLiquidation": false,
      "executedAt": "2026-02-28T11:34:03.529Z",
      "createdAt": "2026-02-28T11:34:03.404Z"
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `type` | Trade type: open, increase, reduce, close, flip, liquidation |
| `liquidityType` | maker (limit order resting on book) or taker (crossing the spread) |
| `realizedPnl` | Profit/loss realized on this trade (string, USDC) |
| `positionSizeBefore` | Position quantity before this trade executed |
| `slippage` | Price slippage from mark price at order time |
| `isLiquidation` | Whether this trade was a forced liquidation |

---

## Margin Configuration (Auth Required)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/accounts/{accountId}/margin-config/{asset}` | Get margin config for a specific asset |
| `PUT` | `/accounts/{accountId}/margin-config/{configId}` | Update margin configuration |

### Update Request

```json
{
  "exchange": "hyperliquid",
  "asset": "BTC",
  "marginMode": "cross",
  "leverage": 10
}
```

Margin modes: `cross` (uses entire account balance) or `isolated` (per position margin).

### Margin Config Response

```json
{
  "configId": "urn:prp-margin-config:Yf1LZ9jMxm7R",
  "accountId": "urn:prp-account:...",
  "exchange": "hyperliquid",
  "asset": "BTC",
  "marginMode": "cross",
  "leverage": "4",
  "createdAt": "2026-02-28T03:39:24.693Z",
  "updatedAt": "2026-02-28T03:39:44.291Z"
}
```

> **Note:** The `configId` from this response is required when calling `PUT /accounts/{accountId}/margin-config/{configId}` to update leverage or margin mode.

### Available Assets

The full Hyperliquid asset universe is supported, including native perps and HIP-3 assets (stocks and commodities).

#### Crypto Perps

Use the token ticker directly as the asset name.

| Asset | Pair | Min Quantity |
|-------|------|-------------|
| BTC | BTC/USDC | 0.001 |
| ETH | ETH/USDC | 0.01 |
| SOL | SOL/USDC | 0.1 |
| DOGE | DOGE/USDC | 1 |
| XRP | XRP/USDC | 1 |
| AVAX | AVAX/USDC | 0.1 |
| LINK | LINK/USDC | 0.1 |

#### HIP-3 Assets (Stocks & Commodities)

HIP-3 assets use the `xyz:SYMBOL` format. You must include the `xyz:` prefix.

| Asset | Type | Format |
|-------|------|--------|
| Apple | Stock | xyz:AAPL |
| Tesla | Stock | xyz:TSLA |
| Nvidia | Stock | xyz:NVDA |
| Gold | Commodity | xyz:GOLD |
| Silver | Commodity | xyz:SILVER |
| Oil (Crude) | Commodity | xyz:CL |

> **Common mistake:** Using `AAPL` instead of `xyz:AAPL` will return a `404 exchange_asset_not_found` error. Always use the `xyz:` prefix for HIP-3 assets.

Use `GET /accounts/{accountId}/margin-config/{asset}` to check if an asset is available (a `200` response confirms the asset is tradeable).

---

## Leverage Limits (Public)

Before setting leverage on a margin config, query the effective leverage limits to know the maximum allowed per asset.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/leverage-limits/effective` | Get the effective max leverage for all assets. No auth required. |

### Response

```json
{
  "defaultMax": 2,
  "overrides": {
    "BTC": 5,
    "ETH": 5
  }
}
```

**How to use:** For any asset, check if it exists in `overrides`. If it does, use that value as the max leverage. Otherwise, fall back to `defaultMax`.

**Current limits:** BTC and ETH support up to **5x** leverage. All other assets default to **2x**.

```python
limits = client.get("/leverage-limits/effective")

def max_leverage(asset: str) -> int:
    return limits["overrides"].get(asset, limits["defaultMax"])

# BTC -> 5x, ETH -> 5x, SOL -> 2x (default)
```

> **Note:** Setting leverage above the allowed max for an asset will be rejected by the server. Always check the effective limits before updating margin config.

---

## OpenAPI Specification

Full OpenAPI 3.0.3 spec with all 14 endpoints, request/response schemas, and field-level documentation. Use it with Swagger UI, code generators, or feed it directly to your AI agent for context.

Download: [openapi.json](https://propr.xyz/openapi.json)

Schemas included: Order (32 fields), Position (28 fields), Trade (31 fields), MarginConfig (8 fields), OrderRequest, Error, PaginatedResponse

---

## Enums Reference

| Category | Values |
|----------|--------|
| Exchange | hyperliquid |
| Product Type | spot, perp |
| Position Side | long, short |
| Order Side | buy, sell |
| Margin Mode | cross, isolated |
| Currency | USDC, USD, EUR |

---

## Error Handling

| Code | Meaning |
|------|---------|
| 400 | Bad request / validation error |
| 401 | Unauthorized (invalid or missing API key) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

## Trading Fees

All orders are subject to trading fees based on liquidity type:

| Liquidity | Fee Rate | Description |
|-----------|----------|-------------|
| Taker | 0.075% | Market orders and limit orders that cross the spread |
| Maker | 0.075% | Limit orders that rest on the book (may vary) |

Fees are deducted from your account balance in USDC and tracked per order in `cumulativeTradingFees` and per trade in `fee`. The `tradingFeeRate` field on orders and trades shows the rate applied.

> **Note:** The `breakEvenPrice` on positions accounts for fees. It differs from `entryPrice` because it includes the cost to enter and exit the position at the current fee rate.

---

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Cancel returns 201 but bot expects 200 | Accept both 200 and 201 as success |
| Selling without reduceOnly opens a short | Always set `reduceOnly: true` when closing |
| Bot tries to cancel already filled orders | Filter orders by status=open and track your own orderIds |
| Position quantity shows "0" but status is "open" | Filter by `quantity != "0"` in your code |
| Bot can't find its own positions (merged into existing) | Track fills internally, don't rely on position ID matching |
| markPrice is stale on REST | Use WebSocket position.updated events for live pricing |
| API key not set or invalid | Check PROPR_API_KEY env var is set; generate at Settings page |
