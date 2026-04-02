"""Stop Loss + Take Profit - Open a position with SL/TP orders."""

from propr_sdk import ProprClient

client = ProprClient()
client.setup()

# Open long position
client.market_buy("ETH", "0.1")

# Set stop loss at 3% below entry
client.create_order(
    side="sell",
    position_side="long",
    order_type="stop_market",
    asset="ETH/USDC",
    base="ETH",
    quote="USDC",
    quantity="0.1",
    trigger_price="2900",  # adjust to your entry
    reduce_only=True,
)

# Set take profit at 5% above entry
client.create_order(
    side="sell",
    position_side="long",
    order_type="take_profit_market",
    asset="ETH/USDC",
    base="ETH",
    quote="USDC",
    quantity="0.1",
    trigger_price="3150",  # adjust to your entry
    reduce_only=True,
)

print("Position opened with SL and TP")
