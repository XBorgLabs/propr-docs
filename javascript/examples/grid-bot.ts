/**
 * Grid Bot - Place a grid of limit orders around the current price.
 */

import { ProprClient } from '../propr-sdk';

const client = new ProprClient();
await client.setup();

// Set 3x leverage on BTC
await client.setLeverage('BTC', 3);

// Get reference price from existing position
const positions = await client.getOpenPositions('BTC');
const midPrice = positions.length
  ? parseFloat(positions[0].markPrice)
  : 95_000;

// Place grid: 5 buy orders below, 5 sell orders above
const gridSpacing = 500;
const quantity = '0.001';

for (let i = 1; i <= 5; i++) {
  const buyPrice = String(midPrice - gridSpacing * i);
  const sellPrice = String(midPrice + gridSpacing * i);

  await client.limitBuy('BTC', quantity, buyPrice);
  await client.limitSell('BTC', quantity, sellPrice, 'USDC', false);
}

console.log(`Grid placed: 10 orders around ${midPrice}`);
