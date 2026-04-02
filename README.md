# Propr Bot API Documentation

Official documentation and SDKs for the [Propr](https://propr.xyz) trading bot API.

> **Why this repo?** The Propr website cannot be scraped by AI agents or documentation tools. This repo mirrors the bot API docs so you can feed them directly into your coding agent, IDE, or toolchain.

## Contents

| Path | Description |
|------|-------------|
| [`docs/api.md`](docs/api.md) | Full REST API reference (14 endpoints) |
| [`docs/websocket.md`](docs/websocket.md) | WebSocket real-time events |
| [`docs/quickstart.md`](docs/quickstart.md) | Bot quickstart guide (Python) |
| [`python/propr_sdk.py`](python/propr_sdk.py) | Python SDK (copy & paste) |
| [`python/README.md`](python/README.md) | Python SDK documentation |
| [`python/examples/`](python/examples/) | Python examples (grid bot, DCA, etc.) |
| [`javascript/propr-sdk.ts`](javascript/propr-sdk.ts) | TypeScript/JavaScript SDK (copy & paste) |
| [`javascript/README.md`](javascript/README.md) | JavaScript SDK documentation |
| [`javascript/examples/`](javascript/examples/) | JS/TS examples (grid bot, portfolio, etc.) |

## Quick Start

### Python

```bash
pip install requests python-ulid websockets python-dotenv
```

```python
from propr_sdk import ProprClient

client = ProprClient()  # reads PROPR_API_KEY from .env
client.setup()          # finds your active challenge account

positions = client.get_open_positions()
orders = client.market_buy("BTC", "0.001")
```

### JavaScript / TypeScript

```bash
npm install ulid
```

```typescript
import { ProprClient } from './propr-sdk';

const client = new ProprClient(); // reads PROPR_API_KEY from env
await client.setup();

const positions = await client.getOpenPositions();
const orders = await client.marketBuy('BTC', '0.001');
```

## Environments

| Environment | Base URL | WebSocket | App |
|-------------|----------|-----------|-----|
| **Live** | `https://api.propr.xyz/v1` | `wss://api.propr.xyz/ws` | `https://app.propr.xyz` |
| **Beta** | `https://api.beta.propr.xyz/v1` | `wss://api.beta.propr.xyz/ws` | `https://app.beta.propr.xyz` |

## Authentication

1. Create an account at [app.propr.xyz](https://app.propr.xyz)
2. Go to **Settings** and generate an API key (starts with `pk_live_`)
3. Set it as an environment variable: `PROPR_API_KEY=pk_live_...`

All authenticated requests require the `X-API-Key` header.

## Links

- [Propr App](https://app.propr.xyz)
- [API Docs on propr.xyz](https://propr.xyz/docs/bot)
- [OpenAPI Spec](https://propr.xyz/openapi.json)
