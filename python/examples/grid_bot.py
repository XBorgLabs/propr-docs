"""Grid Bot - Place a grid of limit orders around the current price."""

from decimal import Decimal
from propr_sdk import ProprClient

client = ProprClient()
client.setup()

# Set 3x leverage on BTC
client.set_leverage("BTC", 3)

# Get current mark price from an existing position or use a reference
positions = client.get_open_positions(base="BTC")
if positions:
    mid_price = Decimal(positions[0]["markPrice"])
else:
    mid_price = Decimal("95000")  # fallback reference price

# Place grid: 5 buy orders below, 5 sell orders above
grid_spacing = Decimal("500")
quantity = "0.001"

for i in range(1, 6):
    buy_price = str(mid_price - grid_spacing * i)
    sell_price = str(mid_price + grid_spacing * i)

    client.limit_buy("BTC", quantity, buy_price)
    client.limit_sell("BTC", quantity, sell_price, reduce_only=False)

print(f"Grid placed: 10 orders around {mid_price}")
