# Propr JavaScript / TypeScript SDK

Official JS/TS client for the Propr trading API.

**Node 18+** | **TypeScript** | Package: `propr-sdk`

## Installation

```bash
npm install ulid
# or
yarn add ulid
# or
pnpm add ulid
```

Create a `.env` file in your project root:

```bash
PROPR_API_KEY=pk_live_your_api_key_here
PROPR_API_URL=https://api.propr.xyz/v1
PROPR_WS_URL=wss://api.propr.xyz/ws
```

Get your API key from [Settings](https://app.propr.xyz/settings).

## Quick Start

```typescript
import { ProprClient } from './propr-sdk';

const client = new ProprClient(); // reads PROPR_API_KEY from env
await client.setup();             // finds your active challenge account

// Check your positions
const positions = await client.getOpenPositions();
for (const p of positions) {
  console.log(`${p.positionSide} ${p.quantity} ${p.base} @ ${p.entryPrice}`);
}

// Place a market buy
const orders = await client.marketBuy('BTC', '0.001');
console.log(`Order placed: ${orders[0].orderId}`);
```

### CommonJS (Node.js without ESM)

```javascript
// propr-sdk.js (rename .ts to .js and remove type annotations)
// Or compile with: npx tsc propr-sdk.ts --target es2020 --module commonjs

const { ProprClient } = require('./propr-sdk');

async function main() {
  const client = new ProprClient();
  await client.setup();

  const positions = await client.getOpenPositions();
  console.log(positions);
}

main().catch(console.error);
```

## API Reference

### Constructor

```typescript
const client = new ProprClient({
  apiKey: 'pk_live_...',            // or set PROPR_API_KEY env var
  baseUrl: 'https://...',           // or set PROPR_API_URL env var
  timeout: 30_000,                  // request timeout in ms (default 30s)
});
```

### Setup

| Method | Description |
|--------|-------------|
| `await client.setup()` | Auto detect account ID from active challenge |
| `await client.setup(accountId)` | Use a specific account ID |

### Health

| Method | Auth | Returns |
|--------|------|---------|
| `await client.health()` | No | `{ status: "OK" }` |
| `await client.healthServices()` | No | `{ core: "OK" \| "ERROR" }` |

### User

| Method | Auth | Returns |
|--------|------|---------|
| `await client.getUser()` | Yes | User profile object |

### Challenges

| Method | Auth | Returns |
|--------|------|---------|
| `await client.getChallenges()` | No | `Challenge[]` |
| `await client.getChallengeAttempts({ status: "active" })` | Yes | `Attempt[]` |
| `await client.getChallengeAttempt(attemptId)` | Yes | `Attempt` |

### Orders

| Method | Description |
|--------|-------------|
| `await client.getOrders({ status: "open" })` | List orders with filters |
| `await client.createOrder({ side, positionSide, orderType, ... })` | Place a single order |
| `await client.createOrders([{...}, {...}])` | Place multiple orders |
| `await client.cancelOrder(orderId)` | Cancel an order (null if already done) |
| `await client.cancelAllOrders("BTC")` | Cancel all open orders |

### Convenience Order Methods

| Method | Description |
|--------|-------------|
| `await client.marketBuy("BTC", "0.001")` | Market buy (long) |
| `await client.marketSell("BTC", "0.001")` | Market sell (close long, reduceOnly) |
| `await client.limitBuy("BTC", "0.001", "90000")` | Limit buy (long) |
| `await client.limitSell("BTC", "0.001", "100000")` | Limit sell (close, reduceOnly) |
| `await client.closePosition("BTC")` | Close entire position (auto detects side) |

### Positions

| Method | Description |
|--------|-------------|
| `await client.getPositions({ base: "BTC", status: "open" })` | List positions with filters |
| `await client.getOpenPositions()` | Get all open non zero positions |
| `await client.getOpenPositions("ETH")` | Get open positions for a specific asset |

### Trades

| Method | Description |
|--------|-------------|
| `await client.getTrades({ base: "BTC" })` | List trade executions with filters |

### Margin & Leverage

| Method | Description |
|--------|-------------|
| `await client.getMarginConfig("BTC")` | Get margin config for an asset |
| `await client.setLeverage("BTC", 5)` | Set leverage (creates/updates config) |
| `await client.getLeverageLimits()` | Get max leverage limits for all assets |
| `await client.maxLeverage("BTC")` | Get max leverage for a specific asset |

## TypeScript Types

The SDK exports full TypeScript interfaces for all response types:

```typescript
import type {
  Order,
  Position,
  Trade,
  MarginConfig,
  LeverageLimits,
  CreateOrderParams,
  ProprClientOptions,
} from './propr-sdk';
```

All monetary values are returned as strings to preserve decimal precision. Use a library like `decimal.js` or `bignumber.js` for arithmetic. Never use native `Number` for money calculations.

## Error Handling

```typescript
import { ProprClient, ProprAPIError } from './propr-sdk';

const client = new ProprClient();
await client.setup();

try {
  const orders = await client.marketBuy('BTC', '0.001');
} catch (err) {
  if (err instanceof ProprAPIError) {
    console.log(`API Error: status=${err.statusCode} code=${err.code}`);

    if (err.statusCode === 429) console.log('Rate limited - slow down');
    if (err.statusCode === 400) console.log('Bad request - check params');
    if (err.statusCode === 401) console.log('Invalid API key');
  } else {
    console.error('Unexpected error:', err);
  }
}
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
- **Portfolio Monitor** - Print a summary of all open positions
- **Stop Loss + Take Profit** - Open a position with SL/TP orders
- **WebSocket Client** - Real time event streaming
