"""Portfolio Monitor - Print a summary of account and open positions."""

from decimal import Decimal
from propr_sdk import ProprClient

client = ProprClient()
client.setup()

# Get account state
account = client.get_account()
balance = Decimal(account["balance"])
available = Decimal(account["availableBalance"])
total_upnl = Decimal(account["totalUnrealizedPnl"])
equity = balance + total_upnl + Decimal(account["isolatedPositionMargin"])

print("Account Overview")
print("=" * 66)
print(f"Balance:       {balance:>12.2f} USDC")
print(f"Available:     {available:>12.2f} USDC")
print(f"uPnL:          {total_upnl:>12.2f} USDC")
print(f"Equity:        {equity:>12.2f} USDC")
print()

positions = client.get_open_positions()

if not positions:
    print("No open positions.")
else:
    print(f"{'Asset':<12} {'Side':<6} {'Qty':<12} {'Entry':<12} {'Mark':<12} {'uPnL':<12}")
    print("-" * 66)

    total_margin = Decimal("0")

    for p in positions:
        margin = Decimal(p["marginUsed"])
        upnl = Decimal(p["unrealizedPnl"])
        total_margin += margin

        print(f"{p['base']:<12} {p['positionSide']:<6} {p['quantity']:<12} "
              f"{p['entryPrice']:<12} {p['markPrice']:<12} {str(upnl):<12}")

    print("-" * 66)
    print(f"Total margin used: {total_margin:.2f} USDC")
