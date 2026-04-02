/**
 * Portfolio Monitor - Print a summary of all open positions.
 */

import { ProprClient } from '../propr-sdk';

const client = new ProprClient();
await client.setup();

const positions = await client.getOpenPositions();

let totalMargin = 0;
let totalUpnl = 0;

console.log('Asset        Side   Qty          Entry        Mark         uPnL');
console.log('-'.repeat(72));

for (const p of positions) {
  const margin = parseFloat(p.marginUsed);
  const upnl = parseFloat(p.unrealizedPnl);
  totalMargin += margin;
  totalUpnl += upnl;

  console.log(
    `${p.base.padEnd(12)} ${p.positionSide.padEnd(6)} ${p.quantity.padEnd(12)} ` +
    `${p.entryPrice.padEnd(12)} ${p.markPrice.padEnd(12)} ${upnl.toFixed(2)}`
  );
}

console.log('-'.repeat(72));
console.log(`Total margin: ${totalMargin.toFixed(2)} USDC`);
console.log(`Total uPnL:   ${totalUpnl.toFixed(2)} USDC`);
