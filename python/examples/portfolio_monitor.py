"""Portfolio Monitor - Print a summary of all open positions."""

from decimal import Decimal
from propr_sdk import ProprClient

client = ProprClient()
client.setup()

positions = client.get_open_positions()

total_margin = Decimal("0")
total_upnl = Decimal("0")

print(f"{'Asset':<12} {'Side':<6} {'Qty':<12} {'Entry':<12} {'Mark':<12} {'uPnL':<12}")
print("-" * 66)

for p in positions:
    margin = Decimal(p["marginUsed"])
    upnl = Decimal(p["unrealizedPnl"])
    total_margin += margin
    total_upnl += upnl

    print(f"{p['base']:<12} {p['positionSide']:<6} {p['quantity']:<12} "
          f"{p['entryPrice']:<12} {p['markPrice']:<12} {str(upnl):<12}")

print("-" * 66)
print(f"Total margin: {total_margin:.2f} USDC")
print(f"Total uPnL:   {total_upnl:.2f} USDC")
