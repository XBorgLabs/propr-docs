/**
 * Stop Loss + Take Profit - Open a position with SL/TP orders.
 */

import { ProprClient } from '../propr-sdk';

const client = new ProprClient();
await client.setup();

// Open long position
await client.marketBuy('ETH', '0.1');

// Set stop loss at 2900
await client.createOrder({
  side: 'sell',
  positionSide: 'long',
  orderType: 'stop_market',
  asset: 'ETH/USDC',
  base: 'ETH',
  quote: 'USDC',
  quantity: '0.1',
  triggerPrice: '2900',
  reduceOnly: true,
});

// Set take profit at 3150
await client.createOrder({
  side: 'sell',
  positionSide: 'long',
  orderType: 'take_profit_market',
  asset: 'ETH/USDC',
  base: 'ETH',
  quote: 'USDC',
  quantity: '0.1',
  triggerPrice: '3150',
  reduceOnly: true,
});

console.log('Position opened with SL and TP');
