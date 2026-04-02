"""DCA Bot - Dollar-cost average into a position over time."""

import time
from propr_sdk import ProprClient

client = ProprClient()
client.setup()

# Buy 0.001 BTC every 60 seconds, 10 times
for i in range(10):
    try:
        orders = client.market_buy("BTC", "0.001")
        print(f"DCA #{i+1}: {orders[0]['status']}")
    except Exception as e:
        print(f"DCA #{i+1} failed: {e}")

    if i < 9:
        time.sleep(60)
