/**
 * WebSocket Client - Real-time event streaming.
 *
 * npm install ws
 */

import WebSocket from 'ws';

const WS_URL = process.env.PROPR_WS_URL || 'wss://api.propr.xyz/ws';
const API_KEY = process.env.PROPR_API_KEY;

function connect() {
  const ws = new WebSocket(WS_URL, {
    headers: { 'X-API-Key': API_KEY! },
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
